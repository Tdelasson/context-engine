from __future__ import annotations

import time
from collections.abc import Mapping, Sequence

from fastapi.testclient import TestClient

from context_engine.api import create_app
from context_engine.core import ApplicationSettings, ContextEngineApplication, DocumentCatalog
from context_engine.knowledge.processing import SourceFormat, SourceInput
from context_engine.models import (
    ModelFinishReason,
    ModelRequest,
    ModelResponse,
    ModelToolCall,
    ModelUsage,
)
from context_engine.tools import ToolInputField, ToolInputSchema, ToolInvocation, ToolRegistry
from tests.source_index_fixtures import MemorySourceStore, coordinator, fixture_chunker


class _Gateway:
    def __init__(self, responses: Sequence[ModelResponse]) -> None:
        self._responses = list(responses)

    def generate(self, request: ModelRequest) -> ModelResponse:
        return self._responses.pop(0)


class _SearchTool:
    name = "search_documents"
    description = "Search deterministic fixture documents."
    input_schema = ToolInputSchema(fields=(ToolInputField(name="query", value_type=str),))

    def execute(self, invocation: ToolInvocation) -> Mapping[str, object]:
        return {"query": invocation.arguments_as_mapping()["query"], "result_count": 0}


def _client(*, timeout: float = 5.0) -> TestClient:
    registry = ToolRegistry()
    registry.register(_SearchTool())
    call = ModelResponse(
        model_id="fake-model",
        output_text="",
        finish_reason=ModelFinishReason.STOP,
        tool_call=ModelToolCall.from_mapping(
            "search_documents", {"query": "bridge"}, tool_call_id="call-1"
        ),
        usage=ModelUsage(input_tokens=1, output_tokens=1),
    )
    final = ModelResponse(
        model_id="fake-model",
        output_text="Done.",
        finish_reason=ModelFinishReason.STOP,
        usage=ModelUsage(input_tokens=1, output_tokens=1),
    )
    application = ContextEngineApplication(
        settings=ApplicationSettings(
            approval_required_tools=("search_documents",), approval_timeout_seconds=timeout
        ),
        document_catalog=DocumentCatalog(
            ingestion=coordinator(MemorySourceStore(fixture_chunker())),
            preloaded_sources=(
                SourceInput("preloaded", "demo.txt", b"demo", SourceFormat.TEXT, "preloaded"),
            ),
        ),
        model_gateway=_Gateway([call, final]),
        tool_registry=registry,
    )
    application.prepare()
    return TestClient(create_app(application, keepalive_seconds=0.05))


def _wait_for_status(client: TestClient, run_id: str, status: str) -> dict[str, object]:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        run: dict[str, object] = client.get(f"/api/v1/runs/{run_id}").json()
        if run["status"] == status:
            return run
        time.sleep(0.01)
    raise AssertionError(f"run never reached {status}")


def test_run_awaits_approval_then_resumes_on_approve() -> None:
    client = _client()
    run_id = client.post("/api/v1/runs", json={"prompt": "find"}).json()["run_id"]

    paused = _wait_for_status(client, run_id, "awaiting_approval")

    assert paused["pending_approval"] == {
        "tool_name": "search_documents",
        "arguments": {"query": "bridge"},
        "invocation_id": "call-1",
        "reason": "Tool invocation requires explicit human approval: search_documents",
    }
    assert client.get("/api/v1/system").json()["settings"]["approval_required_tools"] == [
        "search_documents"
    ]

    answered = client.post(f"/api/v1/runs/{run_id}/approval", json={"decision": "approved"})
    assert answered.status_code == 200

    finished = _wait_for_status(client, run_id, "success")
    assert finished["pending_approval"] is None
    assert finished["final_response"] == "Done."
    assert finished["traces"][0]["policy_decision"] == "require_approval"  # type: ignore[index]
    assert finished["traces"][0]["approval_decision"] == "approved"  # type: ignore[index]
    kinds = [event["kind"] for event in finished["events"]]  # type: ignore[attr-defined]
    assert kinds.index("tool_approval_requested") < kinds.index("tool_approval_resolved")


def test_rejection_with_reason_fails_the_run() -> None:
    client = _client()
    run_id = client.post("/api/v1/runs", json={"prompt": "find"}).json()["run_id"]
    _wait_for_status(client, run_id, "awaiting_approval")

    client.post(
        f"/api/v1/runs/{run_id}/approval", json={"decision": "rejected", "reason": "Too risky"}
    )

    failed = _wait_for_status(client, run_id, "failed")
    assert "Too risky" in str(failed["error_message"])
    assert failed["traces"][0]["approval_decision"] == "rejected"  # type: ignore[index]


def test_unanswered_approval_times_out_as_failed() -> None:
    client = _client(timeout=0.05)
    run_id = client.post("/api/v1/runs", json={"prompt": "find"}).json()["run_id"]

    failed = _wait_for_status(client, run_id, "failed")

    assert "timed out" in str(failed["error_message"])
    assert failed["traces"][0]["approval_decision"] == "rejected"  # type: ignore[index]


def test_invalid_late_duplicate_and_unknown_decisions_are_structured_errors() -> None:
    client = _client()
    run_id = client.post("/api/v1/runs", json={"prompt": "find"}).json()["run_id"]
    _wait_for_status(client, run_id, "awaiting_approval")
    url = f"/api/v1/runs/{run_id}/approval"

    invalid = client.post(url, json={"decision": "maybe"})
    first = client.post(url, json={"decision": "approved"})
    second = client.post(url, json={"decision": "rejected"})
    _wait_for_status(client, run_id, "success")
    late = client.post(url, json={"decision": "approved"})
    unknown = client.post("/api/v1/runs/missing/approval", json={"decision": "approved"})

    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "invalid_request"
    assert first.status_code == 200
    for rejected in (second, late):
        assert rejected.status_code == 409
        assert rejected.json()["error"]["code"] == "no_pending_approval"
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "unknown_run"
