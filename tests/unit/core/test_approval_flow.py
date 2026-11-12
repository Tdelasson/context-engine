from __future__ import annotations

from collections.abc import Mapping, Sequence

import pytest

from context_engine.core import (
    ApplicationConfigurationError,
    ApplicationSettings,
    ContextEngineApplication,
    DocumentCatalog,
    NoPendingApprovalError,
    RunAlreadyActiveError,
    RunRecord,
    RunStatus,
    UnknownRunError,
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
    ToolApprovalDecision,
    ToolInputField,
    ToolInputSchema,
    ToolInvocation,
    ToolPolicyDecision,
    ToolRegistry,
    ToolResultStatus,
)
from context_engine.tools.calculator.tool import Calculator
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

    def __init__(self) -> None:
        self.executions = 0

    def execute(self, invocation: ToolInvocation) -> Mapping[str, object]:
        self.executions += 1
        return {"query": invocation.arguments_as_mapping()["query"], "result_count": 0}


def _search_call() -> ModelResponse:
    return ModelResponse(
        model_id="fake-model",
        output_text="",
        finish_reason=ModelFinishReason.STOP,
        tool_call=ModelToolCall.from_mapping(
            "search_documents", {"query": "bridge"}, tool_call_id="call-1"
        ),
        usage=ModelUsage(input_tokens=30, output_tokens=5),
    )


def _final(text: str) -> ModelResponse:
    return ModelResponse(
        model_id="fake-model",
        output_text=text,
        finish_reason=ModelFinishReason.STOP,
        usage=ModelUsage(input_tokens=80, output_tokens=9),
    )


def _application(
    *,
    required: tuple[str, ...] = ("search_documents",),
    timeout: float = 5.0,
    search: _SearchTool | None = None,
) -> ContextEngineApplication:
    registry = ToolRegistry()
    registry.register(Calculator())
    registry.register(search or _SearchTool())
    return ContextEngineApplication(
        settings=ApplicationSettings(
            approval_required_tools=required, approval_timeout_seconds=timeout
        ),
        document_catalog=DocumentCatalog(
            ingestion=coordinator(MemorySourceStore(fixture_chunker())),
            preloaded_sources=(
                SourceInput("preloaded", "demo.txt", b"demo", SourceFormat.TEXT, "preloaded"),
            ),
        ),
        model_gateway=_Gateway([_search_call(), _final("Done.")]),
        tool_registry=registry,
    )


def _await_approval_request(app: ContextEngineApplication, run_id: str) -> RunRecord:
    after = 0
    while True:
        events, finished = app.wait_for_run_events(run_id, after_sequence=after, timeout=5)
        assert events, "run produced no further events before the approval request"
        for event in events:
            if event.kind == "tool_approval_requested":
                return app.get_run(run_id)
            after = event.sequence
        assert not finished


def test_approval_required_tool_pauses_the_run_and_exposes_the_pending_invocation() -> None:
    search = _SearchTool()
    app = _application(search=search)

    started = app.start_run("find the bridge")
    paused = _await_approval_request(app, started.run_id)

    assert paused.status is RunStatus.AWAITING_APPROVAL
    assert paused.pending_approval is not None
    assert paused.pending_approval.tool_name == "search_documents"
    assert dict(paused.pending_approval.arguments) == {"query": "bridge"}
    assert paused.pending_approval.invocation_id == "call-1"
    assert search.executions == 0
    assert app.describe_system().active_run_id == started.run_id
    with pytest.raises(RunAlreadyActiveError):
        app.start_run("second")

    app.resolve_approval(started.run_id, ToolApprovalDecision.APPROVED)
    finished = app.wait_for_run(started.run_id, timeout=5)

    assert finished.status is RunStatus.SUCCESS
    assert finished.pending_approval is None
    assert finished.final_response == "Done."
    assert search.executions == 1
    assert finished.traces[0].policy_decision is ToolPolicyDecision.REQUIRE_APPROVAL
    assert finished.traces[0].approval_decision is ToolApprovalDecision.APPROVED
    assert finished.traces[0].status is ToolResultStatus.SUCCESS
    assert "tool_approval_resolved" in [event.kind for event in finished.events]


def test_rejection_ends_the_tool_call_and_reports_the_run_as_failed() -> None:
    search = _SearchTool()
    app = _application(search=search)
    started = app.start_run("find the bridge")
    _await_approval_request(app, started.run_id)

    app.resolve_approval(started.run_id, ToolApprovalDecision.REJECTED, reason="Not allowed today")
    finished = app.wait_for_run(started.run_id, timeout=5)

    assert finished.status is RunStatus.FAILED
    assert finished.error_phase == "tool_execution"
    assert finished.error_message is not None
    assert "ToolApprovalRejectedError" in finished.error_message
    assert "Not allowed today" in finished.error_message
    assert search.executions == 0
    assert finished.traces[0].policy_decision is ToolPolicyDecision.REQUIRE_APPROVAL
    assert finished.traces[0].approval_decision is ToolApprovalDecision.REJECTED
    assert finished.traces[0].status is ToolResultStatus.ERROR


def test_unanswered_approval_times_out_as_rejected() -> None:
    search = _SearchTool()
    app = _application(timeout=0.05, search=search)

    finished = app.run_prompt("find the bridge", timeout=5)

    assert finished.status is RunStatus.FAILED
    assert finished.error_message is not None and "timed out" in finished.error_message
    assert search.executions == 0
    assert finished.traces[0].approval_decision is ToolApprovalDecision.REJECTED
    resolved = [e for e in finished.events if e.kind == "tool_approval_resolved"]
    assert len(resolved) == 1
    assert app.describe_system().active_run_id is None


def test_empty_setting_leaves_behavior_unchanged() -> None:
    search = _SearchTool()
    app = _application(required=(), search=search)

    finished = app.run_prompt("find the bridge", timeout=5)

    assert finished.status is RunStatus.SUCCESS
    assert search.executions == 1
    assert finished.traces[0].policy_decision is ToolPolicyDecision.ALLOW
    assert finished.traces[0].approval_decision is None
    assert "tool_approval_requested" not in [event.kind for event in finished.events]


def test_tools_outside_the_setting_run_without_approval() -> None:
    app = _application(required=("calculator",))

    finished = app.run_prompt("find the bridge", timeout=5)

    assert finished.status is RunStatus.SUCCESS
    assert finished.traces[0].approval_decision is None


def test_decisions_without_a_pending_approval_are_rejected() -> None:
    app = _application()
    started = app.start_run("find the bridge")
    _await_approval_request(app, started.run_id)

    app.resolve_approval(started.run_id, ToolApprovalDecision.APPROVED)
    with pytest.raises(NoPendingApprovalError):
        app.resolve_approval(started.run_id, ToolApprovalDecision.REJECTED)
    finished = app.wait_for_run(started.run_id, timeout=5)

    assert finished.status is RunStatus.SUCCESS
    with pytest.raises(NoPendingApprovalError):
        app.resolve_approval(started.run_id, ToolApprovalDecision.APPROVED)
    with pytest.raises(UnknownRunError):
        app.resolve_approval("missing", ToolApprovalDecision.APPROVED)


def test_a_decision_for_a_run_that_never_asked_is_rejected() -> None:
    app = _application(required=())
    finished = app.run_prompt("find the bridge", timeout=5)

    with pytest.raises(NoPendingApprovalError):
        app.resolve_approval(finished.run_id, ToolApprovalDecision.APPROVED)


def test_configuring_an_unregistered_tool_is_rejected_at_composition() -> None:
    with pytest.raises(ApplicationConfigurationError, match="no_such_tool"):
        _application(required=("no_such_tool",))


@pytest.mark.parametrize(
    "overrides",
    [
        {"approval_timeout_seconds": 0.0},
        {"approval_timeout_seconds": float("nan")},
        {"approval_required_tools": ("  ",)},
        {"approval_required_tools": ("search_documents", "search_documents")},
    ],
)
def test_invalid_approval_settings_are_rejected(overrides: dict[str, object]) -> None:
    with pytest.raises(ApplicationConfigurationError):
        ApplicationSettings(**overrides)  # type: ignore[arg-type]


def test_approval_settings_are_read_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTEXT_ENGINE_APPROVAL_TOOLS", " search_documents , calculator ")
    monkeypatch.setenv("CONTEXT_ENGINE_APPROVAL_TIMEOUT_SECONDS", "42")

    settings = ApplicationSettings.from_environment()

    assert settings.approval_required_tools == ("search_documents", "calculator")
    assert settings.approval_timeout_seconds == 42.0


def test_defaults_require_no_approval() -> None:
    settings = ApplicationSettings()

    assert settings.approval_required_tools == ()
    assert settings.approval_timeout_seconds > 0
