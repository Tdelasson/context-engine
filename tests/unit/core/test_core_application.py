from __future__ import annotations

import threading
from collections.abc import Mapping, Sequence

import pytest

from context_engine.agent import AgentRuntimeExecutionOutcome
from context_engine.core import (
    ApplicationSettings,
    ContextEngineApplication,
    DocumentCatalog,
    InvalidPromptError,
    RunAlreadyActiveError,
    RunStatus,
    UnknownRunError,
    UploadCandidate,
)
from context_engine.knowledge.processing import SourceFormat, SourceInput
from context_engine.models import (
    ModelFinishReason,
    ModelGatewayExecutionError,
    ModelRequest,
    ModelResponse,
    ModelToolCall,
    ModelUsage,
)
from context_engine.observability import ModelCallCompleted, RunFinished, StateTransitioned
from context_engine.tools import (
    ToolInputField,
    ToolInputSchema,
    ToolInvocation,
    ToolRegistry,
    ToolResultStatus,
)
from context_engine.tools.calculator.tool import Calculator
from tests.source_index_fixtures import MemorySourceStore, coordinator, fixture_chunker


class _Gateway:
    def __init__(self, responses: Sequence[ModelResponse | Exception]) -> None:
        self._responses = list(responses)
        self.requests: list[ModelRequest] = []

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class _BlockingGateway:
    """Holds the first model call open until released, to keep a run active."""

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
        return {
            "query": invocation.arguments_as_mapping()["query"],
            "result_count": 1,
            "results": [
                {
                    "document_id": "facts.md#0",
                    "score": 0.91,
                    "content": "The bridge opened in 2000.",
                    "content_truncated": False,
                    "metadata": {"source_kind": "uploaded", "source_name": "facts.md"},
                }
            ],
        }


class _FailingSearchTool(_SearchTool):
    def execute(self, invocation: ToolInvocation) -> Mapping[str, object]:
        raise RuntimeError("retrieval backend unavailable")


def _tool_call(tool_name: str, arguments: Mapping[str, object]) -> ModelResponse:
    return ModelResponse(
        model_id="fake-model",
        output_text="",
        finish_reason=ModelFinishReason.STOP,
        tool_call=ModelToolCall.from_mapping(tool_name, arguments, tool_call_id="call-1"),
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
    gateway: object,
    *,
    search_tool: object | None = None,
    settings: ApplicationSettings | None = None,
) -> ContextEngineApplication:
    registry = ToolRegistry()
    registry.register(Calculator())
    registry.register(search_tool or _SearchTool())  # type: ignore[arg-type]
    return ContextEngineApplication(
        settings=settings or ApplicationSettings(),
        document_catalog=DocumentCatalog(
            ingestion=coordinator(MemorySourceStore(fixture_chunker())),
            preloaded_sources=(
                SourceInput("preloaded", "demo.txt", b"demo", SourceFormat.TEXT, "preloaded"),
            ),
        ),
        model_gateway=gateway,  # type: ignore[arg-type]
        tool_registry=registry,
    )


def test_run_record_holds_structured_result_tool_data_and_events() -> None:
    app = _application(
        _Gateway(
            [_tool_call("search_documents", {"query": "bridge"}), _final("It opened in 2000.")]
        )
    )

    record = app.run_prompt("  When did the bridge open?  ", timeout=5)

    assert record.status is RunStatus.SUCCESS
    assert record.prompt == "When did the bridge open?"
    assert record.model_id == app.settings.model_id
    assert record.final_response == "It opened in 2000."
    assert record.model_iterations == 2
    assert record.error_phase is None and record.error_message is None
    assert record.result is not None
    assert record.result.outcome is AgentRuntimeExecutionOutcome.RESPONDED
    assert record.finished_at is not None and record.finished_at >= record.started_at
    assert [trace.invocation.tool_name for trace in record.traces] == ["search_documents"]
    output = record.tool_results[0].output_as_mapping()
    assert output["result_count"] == 1
    assert [event.sequence for event in record.events] == list(range(1, len(record.events) + 1))
    assert {event.run_id for event in record.events} == {record.run_id}
    assert record.events[0].kind == "run_started"
    assert record.events[-1].payload == RunFinished(
        outcome="responded", terminal_status="completed", model_iterations=2
    )
    assert any(isinstance(event.payload, StateTransitioned) for event in record.events)
    tokens = [
        (event.payload.input_tokens, event.payload.output_tokens)
        for event in record.events
        if isinstance(event.payload, ModelCallCompleted)
    ]
    assert tokens == [(30, 5), (80, 9)]


def test_runs_are_listed_in_start_order_and_retrievable_by_id() -> None:
    app = _application(_Gateway([_final("one"), _final("two")]))

    first = app.run_prompt("first", timeout=5)
    second = app.run_prompt("second", timeout=5)

    assert [run.run_id for run in app.list_runs()] == [first.run_id, second.run_id]
    assert app.get_run(second.run_id).final_response == "two"
    assert first.run_id != second.run_id


def test_tool_error_after_response_is_reported_as_failed_with_tool_phase() -> None:
    app = _application(
        _Gateway([_tool_call("search_documents", {"query": "x"}), _final("I could not search.")]),
        search_tool=_FailingSearchTool(),
    )

    record = app.run_prompt("search", timeout=5)

    assert record.status is RunStatus.FAILED
    assert record.error_phase == "tool_execution"
    assert record.error_message == "RuntimeError: retrieval backend unavailable"
    assert record.traces[0].status is ToolResultStatus.ERROR
    assert record.final_response == "I could not search."


def test_model_failure_is_reported_as_failed_with_runtime_phase() -> None:
    app = _application(_Gateway([ModelGatewayExecutionError("local Ollama timed out")]))

    record = app.run_prompt("hello", timeout=5)

    assert record.status is RunStatus.FAILED
    assert record.error_phase == "agent_runtime"
    assert record.error_message is not None
    assert record.final_response is None
    assert record.events[-1].kind == "run_finished"


def test_unexpected_runtime_exception_ends_the_run_and_frees_the_slot() -> None:
    app = _application(_Gateway([RuntimeError("unexpected"), _final("recovered")]))

    failed = app.run_prompt("hello", timeout=5)

    assert failed.status is RunStatus.FAILED
    assert failed.result is None
    assert failed.error_phase == "agent_runtime"
    assert failed.error_message == "RuntimeError: unexpected"
    assert app.describe_system().active_run_id is None
    assert app.run_prompt("again", timeout=5).status is RunStatus.SUCCESS


def test_iteration_limit_is_reported_as_limit_reached() -> None:
    app = _application(
        _Gateway([_tool_call("search_documents", {"query": "x"})] * 2),
        settings=ApplicationSettings(max_model_iterations=2),
    )

    record = app.run_prompt("loop", timeout=5)

    assert record.status is RunStatus.LIMIT_REACHED
    assert record.max_model_iterations == 2
    assert record.final_response is None
    assert record.error_phase == "agent_runtime"


def test_blank_prompt_is_rejected_before_any_run_or_model_call() -> None:
    gateway = _Gateway([])
    app = _application(gateway)

    with pytest.raises(InvalidPromptError):
        app.start_run("   ")

    assert app.list_runs() == ()
    assert gateway.requests == []


def test_second_run_is_rejected_while_one_is_active() -> None:
    gateway = _BlockingGateway()
    app = _application(gateway)

    active = app.start_run("first")
    assert gateway.entered.wait(timeout=5)
    try:
        assert active.status is RunStatus.RUNNING
        assert app.get_run(active.run_id).status is RunStatus.RUNNING
        assert app.describe_system().active_run_id == active.run_id
        with pytest.raises(RunAlreadyActiveError) as raised:
            app.start_run("second")
        assert raised.value.active_run_id == active.run_id
        assert len(app.list_runs()) == 1
    finally:
        gateway.release.set()

    finished, done = app.wait_for_run_events(active.run_id, after_sequence=10_000, timeout=5)
    assert done is True and finished == ()
    assert app.get_run(active.run_id).status is RunStatus.SUCCESS


def test_events_can_be_read_incrementally_while_a_run_is_active() -> None:
    gateway = _BlockingGateway()
    app = _application(gateway)

    active = app.start_run("first")
    assert gateway.entered.wait(timeout=5)
    early, done = app.wait_for_run_events(active.run_id, after_sequence=0, timeout=5)
    assert done is False
    assert early[0].kind == "run_started"
    assert early[-1].kind == "model_call_started"
    last_seen = early[-1].sequence

    gateway.release.set()
    collected = list(early)
    while not done:
        newer, done = app.wait_for_run_events(active.run_id, after_sequence=last_seen, timeout=5)
        collected.extend(newer)
        if newer:
            last_seen = newer[-1].sequence

    assert [event.sequence for event in collected] == list(range(1, len(collected) + 1))
    assert collected[-1].kind == "run_finished"
    assert tuple(collected) == app.get_run(active.run_id).events


def test_unknown_run_id_raises_a_typed_error() -> None:
    app = _application(_Gateway([]))

    with pytest.raises(UnknownRunError):
        app.get_run("missing")
    with pytest.raises(UnknownRunError):
        app.wait_for_run_events("missing")


def test_system_description_reports_tools_presets_dependencies_and_settings() -> None:
    app = _application(_Gateway([]))

    system = app.describe_system()

    assert [tool.name for tool in system.tools] == ["calculator", "search_documents"]
    assert all(tool.description for tool in system.tools)
    assert dict(system.prompt_presets)["Calculator"].startswith("Use the calculator")
    assert [dependency.name for dependency in system.dependencies] == [
        "model",
        "embeddings",
        "vector_store",
    ]
    assert system.settings is app.settings
    assert system.active_run_id is None


def test_source_facade_prepares_lists_ingests_deletes_and_clears() -> None:
    app = _application(_Gateway([]))

    prepared = app.prepare()
    assert prepared.source_names == ("demo.txt",)
    assert [source.source_name for source in app.list_sources().preloaded] == ["demo.txt"]
    assert app.list_sources().uploaded == ()

    report = app.ingest_uploads(
        (UploadCandidate("a.md", b"# A\n\nalpha"), UploadCandidate("b.txt", b"beta"))
    )
    assert report.source_names == ("a.md", "b.txt")
    uploaded = app.list_sources().uploaded
    assert sorted(source.source_name for source in uploaded) == ["a.md", "b.txt"]

    app.delete_upload(uploaded[0].source_id)
    assert len(app.list_sources().uploaded) == 1

    cleared = app.clear_uploads()
    assert len(cleared) == 1
    assert app.list_sources().uploaded == ()
    assert [source.source_name for source in app.list_sources().preloaded] == ["demo.txt"]
    assert app.recover_source_index() == app.documents.recovery_outcomes
