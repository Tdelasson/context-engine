from collections.abc import Callable, Mapping

import pytest

from context_engine.agent import (
    ALLOWED_TRANSITIONS,
    AgentExecutionStatus,
    AgentRuntime,
    AgentRuntimeExecutionOutcome,
)
from context_engine.models import (
    ModelFinishReason,
    ModelGatewayExecutionError,
    ModelRequest,
    ModelResponse,
    ModelToolCall,
    ModelUsage,
)
from context_engine.observability import (
    ModelCallCompleted,
    RecordingRunEventSink,
    RunEvent,
    RunEventEmitter,
    RunFinished,
    RunStarted,
    StateTransitioned,
    ToolProposed,
)
from context_engine.tools import (
    ToolInputField,
    ToolInputSchema,
    ToolInvocation,
    ToolRegistry,
    ToolRuntime,
)


class _EchoTool:
    name = "echo"
    description = "Echo text."
    input_schema = ToolInputSchema(fields=(ToolInputField(name="text", value_type=str),))

    def execute(self, invocation: ToolInvocation) -> Mapping[str, object]:
        return {"echo": invocation.arguments_as_mapping()["text"]}


class _ScriptedGateway:
    def __init__(self, responses: list[ModelResponse | Exception]) -> None:
        self._responses = responses

    def generate(self, request: ModelRequest) -> ModelResponse:
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class _RaisingSink:
    def record(self, event: RunEvent) -> None:
        raise RuntimeError("sink unavailable")


def _tool_call_response() -> ModelResponse:
    return ModelResponse(
        model_id="stub",
        output_text="",
        finish_reason=ModelFinishReason.STOP,
        tool_call=ModelToolCall.from_mapping(
            tool_name="echo", arguments={"text": "hi"}, tool_call_id="call-1"
        ),
        usage=ModelUsage(input_tokens=40, output_tokens=7),
    )


def _final_response(text: str = "done") -> ModelResponse:
    return ModelResponse(
        model_id="stub",
        output_text=text,
        finish_reason=ModelFinishReason.STOP,
        usage=ModelUsage(input_tokens=90, output_tokens=12),
    )


def _stepping_clock(step: float = 0.25) -> Callable[[], float]:
    state = {"now": 0.0}

    def clock() -> float:
        state["now"] += step
        return state["now"]

    return clock


def _observed_runtime(
    responses: list[ModelResponse | Exception],
) -> tuple[AgentRuntime, RecordingRunEventSink]:
    sink = RecordingRunEventSink()
    emitter = RunEventEmitter(sink, run_id="run-1", monotonic_clock=_stepping_clock())
    registry = ToolRegistry()
    registry.register(_EchoTool())
    runtime = AgentRuntime(
        model_gateway=_ScriptedGateway(responses),
        tool_runtime=ToolRuntime(registry, events=emitter),
        events=emitter,
    )
    return runtime, sink


def _transitions(sink: RecordingRunEventSink) -> list[tuple[str, str]]:
    return [
        (event.payload.from_status, event.payload.to_status)
        for event in sink.events
        if isinstance(event.payload, StateTransitioned)
    ]


def test_run_with_one_tool_call_emits_the_full_ordered_sequence() -> None:
    runtime, sink = _observed_runtime([_tool_call_response(), _final_response()])

    result = runtime.run(model_id="stub", user_prompt="say hi", max_model_iterations=4)

    assert result.outcome is AgentRuntimeExecutionOutcome.RESPONDED
    assert [event.kind for event in sink.events] == [
        "run_started",
        "state_transitioned",  # start -> context
        "state_transitioned",  # context -> think
        "model_call_started",
        "model_call_completed",
        "state_transitioned",  # think -> action_proposed
        "state_transitioned",  # action_proposed -> runtime_validate
        "state_transitioned",  # runtime_validate -> tool_call
        "tool_proposed",
        "tool_validated",
        "tool_policy_decided",
        "tool_call_finished",
        "state_transitioned",  # tool_call -> think
        "model_call_started",
        "model_call_completed",
        "state_transitioned",  # think -> action_proposed
        "state_transitioned",  # action_proposed -> runtime_validate
        "state_transitioned",  # runtime_validate -> respond
        "state_transitioned",  # respond -> completed
        "run_finished",
    ]
    assert [event.sequence for event in sink.events] == list(range(1, len(sink.events) + 1))
    assert {event.run_id for event in sink.events} == {"run-1"}
    assert _transitions(sink) == [
        ("start", "context"),
        ("context", "think"),
        ("think", "action_proposed"),
        ("action_proposed", "runtime_validate"),
        ("runtime_validate", "tool_call"),
        ("tool_call", "think"),
        ("think", "action_proposed"),
        ("action_proposed", "runtime_validate"),
        ("runtime_validate", "respond"),
        ("respond", "completed"),
    ]
    assert sink.events[0].payload == RunStarted(model_id="stub", max_model_iterations=4)
    assert sink.events[8].payload == ToolProposed(
        tool_name="echo", arguments=(("text", "hi"),), invocation_id="call-1"
    )
    assert sink.events[-1].payload == RunFinished(
        outcome="responded", terminal_status="completed", model_iterations=2
    )


def test_emitted_transitions_form_a_valid_chain_through_the_transition_map() -> None:
    runtime, sink = _observed_runtime([_tool_call_response(), _final_response()])

    runtime.run(model_id="stub", user_prompt="say hi")

    transitions = _transitions(sink)
    for from_status, to_status in transitions:
        assert (
            AgentExecutionStatus(to_status)
            in ALLOWED_TRANSITIONS[AgentExecutionStatus(from_status)]
        )
    for (_, reached), (left, _) in zip(transitions, transitions[1:], strict=False):
        assert reached == left


def test_model_call_events_report_duration_finish_reason_and_token_usage() -> None:
    runtime, sink = _observed_runtime([_tool_call_response(), _final_response()])

    runtime.run(model_id="stub", user_prompt="say hi")

    completed = [e.payload for e in sink.events if isinstance(e.payload, ModelCallCompleted)]
    assert completed == [
        ModelCallCompleted(
            iteration=1,
            duration_seconds=0.25,
            finish_reason="stop",
            input_tokens=40,
            output_tokens=7,
        ),
        ModelCallCompleted(
            iteration=2,
            duration_seconds=0.25,
            finish_reason="stop",
            input_tokens=90,
            output_tokens=12,
        ),
    ]


def test_token_usage_is_none_when_the_provider_reports_none() -> None:
    runtime, sink = _observed_runtime(
        [ModelResponse(model_id="stub", output_text="ok", finish_reason=ModelFinishReason.STOP)]
    )

    runtime.run(model_id="stub", user_prompt="hello")

    completed = next(e.payload for e in sink.events if isinstance(e.payload, ModelCallCompleted))
    assert completed.input_tokens is None
    assert completed.output_tokens is None


def test_gateway_failure_emits_model_error_and_a_single_failed_run_finish() -> None:
    runtime, sink = _observed_runtime([ModelGatewayExecutionError("model offline")])

    result = runtime.run(model_id="stub", user_prompt="hello")

    assert result.outcome is AgentRuntimeExecutionOutcome.FAILED
    completed = next(e.payload for e in sink.events if isinstance(e.payload, ModelCallCompleted))
    assert completed.error == "ModelGatewayExecutionError: model offline"
    assert completed.finish_reason is None
    assert _transitions(sink) == [
        ("start", "context"),
        ("context", "think"),
        ("think", "action_proposed"),
        ("action_proposed", "runtime_validate"),
        ("runtime_validate", "failed"),
    ]
    finishes = [e.payload for e in sink.events if isinstance(e.payload, RunFinished)]
    assert len(finishes) == 1
    assert finishes[0].outcome == "failed"
    assert finishes[0].terminal_status == "failed"
    assert finishes[0].error_message is not None
    assert sink.events[-1].kind == "run_finished"


def test_iteration_limit_emits_limit_reached_finish() -> None:
    runtime, sink = _observed_runtime([_tool_call_response(), _tool_call_response()])

    result = runtime.run(model_id="stub", user_prompt="loop", max_model_iterations=2)

    assert result.outcome is AgentRuntimeExecutionOutcome.LIMIT_REACHED
    finish = sink.events[-1].payload
    assert isinstance(finish, RunFinished)
    assert finish.outcome == "limit_reached"
    assert finish.terminal_status == "failed"
    assert finish.model_iterations == 2
    assert [e.kind for e in sink.events].count("tool_call_finished") == 2


def test_unexpected_gateway_exception_still_emits_one_run_finish_and_propagates() -> None:
    runtime, sink = _observed_runtime([RuntimeError("unexpected")])

    with pytest.raises(RuntimeError, match="unexpected"):
        runtime.run(model_id="stub", user_prompt="hello")

    finishes = [e.payload for e in sink.events if isinstance(e.payload, RunFinished)]
    assert len(finishes) == 1
    assert finishes[0].outcome == "failed"
    assert finishes[0].error_message == "RuntimeError: unexpected"


def test_invalid_iteration_limit_emits_no_events() -> None:
    runtime, sink = _observed_runtime([])

    with pytest.raises(ValueError):
        runtime.run(model_id="stub", user_prompt="hello", max_model_iterations=0)

    assert sink.events == ()


def test_raising_sink_does_not_change_the_run_result() -> None:
    def build(events: RunEventEmitter | None) -> AgentRuntime:
        registry = ToolRegistry()
        registry.register(_EchoTool())
        return AgentRuntime(
            model_gateway=_ScriptedGateway([_tool_call_response(), _final_response()]),
            tool_runtime=ToolRuntime(registry, events=events),
            events=events,
        )

    plain = build(None)
    observed = build(RunEventEmitter(_RaisingSink(), run_id="run-1"))

    assert observed.run(model_id="stub", user_prompt="hi") == plain.run(
        model_id="stub", user_prompt="hi"
    )
    assert observed.tool_results == plain.tool_results
    assert observed.tool_execution_traces == plain.tool_execution_traces
