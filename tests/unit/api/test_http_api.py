from __future__ import annotations

import json
import threading
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from context_engine.api import create_app
from context_engine.core import (
    ApplicationSettings,
    ContextEngineApplication,
    DocumentCatalog,
    SourceCatalogError,
)
from context_engine.knowledge.processing import SourceFormat, SourceInput
from context_engine.models import (
    ModelFinishReason,
    ModelRequest,
    ModelResponse,
    ModelToolCall,
    ModelUsage,
)
from context_engine.tools import (
    ToolInputField,
    ToolInputSchema,
    ToolInvocation,
    ToolRegistry,
)
from context_engine.tools.calculator.tool import Calculator
from tests.source_index_fixtures import MemorySourceStore, coordinator, fixture_chunker


class _Gateway:
    def __init__(self, responses: Sequence[ModelResponse]) -> None:
        self._responses = list(responses)

    def generate(self, request: ModelRequest) -> ModelResponse:
        return self._responses.pop(0)


class _BlockingGateway:
    def __init__(self) -> None:
        self.entered = threading.Event()
        self.release = threading.Event()

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.entered.set()
        assert self.release.wait(timeout=5)
        return _final("released")


class _SearchTool:
    name = "search_documents"
    description = "Search deterministic fixture documents."
    input_schema = ToolInputSchema(fields=(ToolInputField(name="query", value_type=str),))

    def execute(self, invocation: ToolInvocation) -> Mapping[str, object]:
        return {"query": invocation.arguments_as_mapping()["query"], "result_count": 0}


def _tool_call(name: str, arguments: Mapping[str, object]) -> ModelResponse:
    return ModelResponse(
        model_id="fake-model",
        output_text="",
        finish_reason=ModelFinishReason.STOP,
        tool_call=ModelToolCall.from_mapping(name, arguments, tool_call_id="call-1"),
        usage=ModelUsage(input_tokens=30, output_tokens=5),
    )


def _final(text: str) -> ModelResponse:
    return ModelResponse(
        model_id="fake-model",
        output_text=text,
        finish_reason=ModelFinishReason.STOP,
        usage=ModelUsage(input_tokens=80, output_tokens=9),
    )


def _client(gateway: object, *, static_dir: Path | None = None) -> TestClient:
    registry = ToolRegistry()
    registry.register(Calculator())
    registry.register(_SearchTool())
    application = ContextEngineApplication(
        settings=ApplicationSettings(),
        document_catalog=DocumentCatalog(
            ingestion=coordinator(MemorySourceStore(fixture_chunker())),
            preloaded_sources=(
                SourceInput("preloaded", "demo.txt", b"demo", SourceFormat.TEXT, "preloaded"),
            ),
        ),
        model_gateway=gateway,  # type: ignore[arg-type]
        tool_registry=registry,
    )
    application.prepare()
    return TestClient(create_app(application, static_dir=static_dir, keepalive_seconds=0.05))


def _finished(client: TestClient, run_id: str) -> dict[str, object]:
    events = _read_stream(client, f"/api/v1/runs/{run_id}/events")
    assert events[-1]["kind"] == "run_finished"
    response = client.get(f"/api/v1/runs/{run_id}")
    assert response.status_code == 200
    body: dict[str, object] = response.json()
    return body


def _read_stream(
    client: TestClient, url: str, headers: dict[str, str] | None = None
) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    with client.stream("GET", url, headers=headers) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        for line in response.iter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[len("data: ") :]))
    return events


# -- runs -----------------------------------------------------------------------------


def test_start_run_returns_accepted_summary_and_run_detail_is_structured() -> None:
    client = _client(
        _Gateway([_tool_call("search_documents", {"query": "bridge"}), _final("Done.")])
    )

    started = client.post("/api/v1/runs", json={"prompt": "  find the bridge  "})

    assert started.status_code == 202
    summary = started.json()
    assert summary["prompt"] == "find the bridge"
    run = _finished(client, summary["run_id"])
    assert run["status"] == "success"
    assert run["final_response"] == "Done."
    assert run["outcome"] == "responded"
    assert run["model_iterations"] == 2
    assert run["tool_results"][0]["tool_name"] == "search_documents"  # type: ignore[index]
    assert run["tool_results"][0]["arguments"] == {"query": "bridge"}  # type: ignore[index]
    assert run["traces"][0]["policy_decision"] == "allow"  # type: ignore[index]
    sequences = [event["sequence"] for event in run["events"]]  # type: ignore[attr-defined]
    assert sequences == list(range(1, len(sequences) + 1))


def test_runs_are_listed_without_events() -> None:
    client = _client(_Gateway([_final("one")]))
    run_id = client.post("/api/v1/runs", json={"prompt": "first"}).json()["run_id"]
    _finished(client, run_id)

    listed = client.get("/api/v1/runs").json()["runs"]

    assert [run["run_id"] for run in listed] == [run_id]
    assert "events" not in listed[0]


def test_blank_prompt_and_missing_prompt_are_structured_422s() -> None:
    client = _client(_Gateway([]))

    blank = client.post("/api/v1/runs", json={"prompt": "   "})
    missing = client.post("/api/v1/runs", json={})

    assert blank.status_code == 422
    assert blank.json()["error"]["code"] == "invalid_prompt"
    assert missing.status_code == 422
    assert missing.json()["error"]["code"] == "invalid_request"
    assert client.get("/api/v1/runs").json() == {"runs": []}


def test_unknown_run_is_a_structured_404_for_detail_and_stream() -> None:
    client = _client(_Gateway([]))

    for url in ("/api/v1/runs/missing", "/api/v1/runs/missing/events"):
        response = client.get(url)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "unknown_run"


def test_second_concurrent_run_returns_409_with_active_run_id() -> None:
    gateway = _BlockingGateway()
    client = _client(gateway)
    first = client.post("/api/v1/runs", json={"prompt": "first"}).json()
    assert gateway.entered.wait(timeout=5)
    try:
        second = client.post("/api/v1/runs", json={"prompt": "second"})
        assert second.status_code == 409
        error = second.json()["error"]
        assert error["code"] == "run_already_active"
        assert error["details"] == {"active_run_id": first["run_id"]}
        assert client.get("/api/v1/system").json()["active_run_id"] == first["run_id"]
    finally:
        gateway.release.set()
    _finished(client, first["run_id"])
    assert client.post("/api/v1/runs", json={"prompt": "third"}).status_code in {202, 409}


def test_failed_run_is_never_reported_as_success() -> None:
    client = _client(_Gateway([_tool_call("search_documents", {"wrong": 1}), _final("ok")]))
    run_id = client.post("/api/v1/runs", json={"prompt": "x"}).json()["run_id"]

    run = _finished(client, run_id)

    assert run["status"] == "failed"
    assert run["error_phase"] is not None


# -- event stream ---------------------------------------------------------------------


def test_late_subscriber_replays_all_events_in_order_and_stream_terminates() -> None:
    client = _client(_Gateway([_final("hi")]))
    run_id = client.post("/api/v1/runs", json={"prompt": "hi"}).json()["run_id"]
    expected = _finished(client, run_id)["events"]

    replayed = _read_stream(client, f"/api/v1/runs/{run_id}/events")

    assert replayed == expected
    assert replayed[0]["kind"] == "run_started"
    assert replayed[-1]["kind"] == "run_finished"


def test_reconnecting_client_resumes_after_last_event_id_or_after_param() -> None:
    client = _client(_Gateway([_final("hi")]))
    run_id = client.post("/api/v1/runs", json={"prompt": "hi"}).json()["run_id"]
    events = _finished(client, run_id)["events"]
    cut = events[2]["sequence"]  # type: ignore[index]

    by_header = _read_stream(
        client, f"/api/v1/runs/{run_id}/events", headers={"Last-Event-ID": str(cut)}
    )
    by_param = _read_stream(client, f"/api/v1/runs/{run_id}/events?after={cut}")

    assert by_header == by_param == events[3:]  # type: ignore[index]


def test_live_subscriber_receives_events_then_stream_closes_after_run_finished() -> None:
    gateway = _BlockingGateway()
    client = _client(gateway)
    run_id = client.post("/api/v1/runs", json={"prompt": "live"}).json()["run_id"]
    assert gateway.entered.wait(timeout=5)
    collected: list[dict[str, object]] = []

    def follow() -> None:
        collected.extend(_read_stream(client, f"/api/v1/runs/{run_id}/events"))

    reader = threading.Thread(target=follow)
    reader.start()
    gateway.release.set()
    reader.join(timeout=10)

    assert not reader.is_alive()
    assert [event["sequence"] for event in collected] == list(range(1, len(collected) + 1))
    assert collected[-1]["kind"] == "run_finished"


# -- sources --------------------------------------------------------------------------


def _upload(client: TestClient, *files: tuple[str, bytes]) -> object:
    return client.post(
        "/api/v1/sources",
        files=[("files", (name, content, "text/plain")) for name, content in files],
    )


def test_sources_upload_list_delete_and_clear() -> None:
    client = _client(_Gateway([]))

    initial = client.get("/api/v1/sources").json()
    assert [s["source_name"] for s in initial["preloaded"]] == ["demo.txt"]
    assert initial["uploaded"] == []

    uploaded = _upload(client, ("a.md", b"# A\n\nalpha"), ("b.txt", b"beta"))
    assert uploaded.status_code == 200  # type: ignore[attr-defined]
    report = uploaded.json()  # type: ignore[attr-defined]
    assert report["source_names"] == ["a.md", "b.txt"]
    assert report["chunk_count"] >= 2
    assert all(outcome["status"] for outcome in report["outcomes"])

    listed = client.get("/api/v1/sources").json()["uploaded"]
    assert sorted(s["source_name"] for s in listed) == ["a.md", "b.txt"]
    assert listed[0]["chunk_count"] >= 1

    deleted = client.delete(f"/api/v1/sources/{listed[0]['source_id']}")
    assert deleted.status_code == 200
    assert len(client.get("/api/v1/sources").json()["uploaded"]) == 1

    cleared = client.delete("/api/v1/sources")
    assert cleared.status_code == 200
    assert len(cleared.json()["deleted_source_ids"]) == 1
    final = client.get("/api/v1/sources").json()
    assert final["uploaded"] == []
    assert len(final["preloaded"]) == 1


def test_invalid_upload_is_a_structured_422_and_indexes_nothing() -> None:
    client = _client(_Gateway([]))

    response = _upload(client, ("bad.exe", b"MZ"))

    assert response.status_code == 422  # type: ignore[attr-defined]
    assert response.json()["error"]["code"] == "source_rejected"  # type: ignore[attr-defined]
    assert client.get("/api/v1/sources").json()["uploaded"] == []


def test_upload_without_files_is_a_structured_422() -> None:
    client = _client(_Gateway([]))

    response = client.post("/api/v1/sources")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_source_failures_report_whether_the_index_needs_recovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client(_Gateway([]))
    application = client.app.state.application  # type: ignore[attr-defined]

    def fail(_: object) -> None:
        raise SourceCatalogError("store: write failed. Restart/recover.", requires_recovery=True)

    monkeypatch.setattr(application, "ingest_uploads", fail)
    response = _upload(client, ("a.md", b"# A\n\nalpha"))

    assert response.status_code == 422  # type: ignore[attr-defined]
    error = response.json()["error"]  # type: ignore[attr-defined]
    assert error["code"] == "source_rejected"
    assert error["details"] == {"requires_recovery": True}


def test_validation_rejections_do_not_require_recovery() -> None:
    client = _client(_Gateway([]))

    response = _upload(client, ("bad.exe", b"MZ"))

    assert response.json()["error"]["details"] == {"requires_recovery": False}  # type: ignore[attr-defined]


def test_deleting_unknown_or_preloaded_source_is_rejected() -> None:
    client = _client(_Gateway([]))
    preloaded_id = client.get("/api/v1/sources").json()["preloaded"][0]["source_id"]

    unknown = client.delete("/api/v1/sources/nope")
    preloaded = client.delete(f"/api/v1/sources/{preloaded_id}")

    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "unknown_source"
    assert preloaded.status_code == 409
    assert preloaded.json()["error"]["code"] == "source_not_deletable"
    assert len(client.get("/api/v1/sources").json()["preloaded"]) == 1


def test_recover_returns_recovery_outcomes() -> None:
    client = _client(_Gateway([]))

    response = client.post("/api/v1/sources/recover")

    assert response.status_code == 200
    assert response.json() == {"outcomes": []}


# -- system, schema and static files --------------------------------------------------


def test_system_reports_tools_presets_dependencies_and_settings() -> None:
    client = _client(_Gateway([]))

    system = client.get("/api/v1/system").json()

    assert [tool["name"] for tool in system["tools"]] == ["calculator", "search_documents"]
    assert any(preset["name"] == "Calculator" for preset in system["prompt_presets"])
    assert [dep["name"] for dep in system["dependencies"]] == [
        "model",
        "embeddings",
        "vector_store",
    ]
    assert system["settings"]["retrieval_strategy"] == "dense"
    assert system["active_run_id"] is None


def test_openapi_document_describes_every_endpoint_response_schema() -> None:
    document = _client(_Gateway([])).get("/openapi.json").json()

    operations = [
        (path, method, operation)
        for path, methods in document["paths"].items()
        for method, operation in methods.items()
    ]
    assert {path for path, _, _ in operations} >= {
        "/api/v1/runs",
        "/api/v1/runs/{run_id}",
        "/api/v1/runs/{run_id}/events",
        "/api/v1/sources",
        "/api/v1/sources/{source_id}",
        "/api/v1/sources/recover",
        "/api/v1/system",
    }
    for path, method, operation in operations:
        success = next(code for code in operation["responses"] if code.startswith("2"))
        content = operation["responses"][success]["content"]
        assert content, f"{method} {path} has no documented success schema"
        for media in content.values():
            assert media["schema"], f"{method} {path} has an empty schema"
        assert "404" in operation["responses"] or "422" in operation["responses"]


def test_static_directory_is_served_when_present_and_absent_otherwise(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<h1>ui</h1>", encoding="utf-8")

    with_static = _client(_Gateway([]), static_dir=tmp_path)
    without = _client(_Gateway([]), static_dir=tmp_path / "missing")

    assert with_static.get("/").text == "<h1>ui</h1>"
    assert with_static.get("/api/v1/system").status_code == 200
    assert without.get("/").status_code == 404


def test_client_routes_fall_back_to_the_frontend_but_api_and_files_stay_404(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<h1>ui</h1>", encoding="utf-8")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    client = _client(_Gateway([]), static_dir=tmp_path)

    assert client.get("/runs/abc123").text == "<h1>ui</h1>"
    assert client.get("/runs").text == "<h1>ui</h1>"
    assert client.get("/assets/app.js").text == "console.log(1)"
    assert client.get("/assets/missing.js").status_code == 404
    unknown_api = client.get("/api/v1/nothing")
    assert unknown_api.status_code == 404
    assert unknown_api.json()["error"]["code"] == "http_error"
    assert client.get("/api/v1/system").status_code == 200


@pytest.mark.parametrize("path", ["/api/v1/runs/x/unknown", "/api/v2/runs"])
def test_unknown_routes_return_structured_404(path: str) -> None:
    response = _client(_Gateway([])).get(path)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_error"
