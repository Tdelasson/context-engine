from collections.abc import Callable, Mapping

from context_engine.observability import (
    RecordingRunEventSink,
    RunEvent,
    RunEventEmitter,
    ToolApprovalRequested,
    ToolApprovalResolved,
    ToolCallFinished,
    ToolPolicyDecided,
    ToolValidated,
)
from context_engine.tools import (
    ToolApprovalDecision,
    ToolApprovalRequest,
    ToolApprovalResolution,
    ToolInputField,
    ToolInputSchema,
    ToolInvocation,
    ToolNamePolicy,
    ToolPolicyDecision,
    ToolRegistry,
    ToolResultStatus,
    ToolRuntime,
)


class _AddTool:
    name = "add"
    description = "Add two integers."
    input_schema = ToolInputSchema(
        fields=(ToolInputField(name="a", value_type=int), ToolInputField(name="b", value_type=int))
    )

    def __init__(self) -> None:
        self.calls = 0

    def execute(self, invocation: ToolInvocation) -> Mapping[str, object]:
        self.calls += 1
        arguments = invocation.arguments_as_mapping()
        a, b = arguments["a"], arguments["b"]
        assert isinstance(a, int) and isinstance(b, int)
        return {"sum": a + b}


class _FailingTool:
    name = "explode"
    description = "Always fails."
    input_schema = ToolInputSchema(fields=())

    def execute(self, invocation: ToolInvocation) -> Mapping[str, object]:
        raise RuntimeError("boom")


class _Resolver:
    def __init__(self, decision: ToolApprovalDecision, reason: str | None = None) -> None:
        self._resolution = ToolApprovalResolution(decision=decision, reason=reason)

    def resolve(self, request: ToolApprovalRequest) -> ToolApprovalResolution:
        return self._resolution


class _RaisingSink:
    def record(self, event: RunEvent) -> None:
        raise RuntimeError("sink unavailable")


def _stepping_clock(step: float = 0.5) -> Callable[[], float]:
    state = {"now": 0.0}

    def clock() -> float:
        state["now"] += step
        return state["now"]

    return clock


def _runtime(
    *,
    policy: ToolNamePolicy | None = None,
    resolver: _Resolver | None = None,
) -> tuple[ToolRuntime, RecordingRunEventSink, _AddTool]:
    registry = ToolRegistry()
    add = _AddTool()
    registry.register(add)
    registry.register(_FailingTool())
    sink = RecordingRunEventSink()
    emitter = RunEventEmitter(sink, run_id="run-1", monotonic_clock=_stepping_clock())
    runtime = ToolRuntime(registry, policy=policy, approval_resolver=resolver, events=emitter)
    return runtime, sink, add


def _add(invocation_id: str = "call-1") -> ToolInvocation:
    return ToolInvocation.from_mapping("add", {"a": 2, "b": 3}, invocation_id=invocation_id)


def test_allowed_invocation_emits_validated_policy_and_finished_with_duration() -> None:
    runtime, sink, _ = _runtime()

    result = runtime.execute(_add())

    assert result.status is ToolResultStatus.SUCCESS
    assert [event.payload for event in sink.events] == [
        ToolValidated(tool_name="add", accepted=True, invocation_id="call-1"),
        ToolPolicyDecided(tool_name="add", decision="allow", invocation_id="call-1"),
        ToolCallFinished(
            tool_name="add",
            status="success",
            executed=True,
            invocation_id="call-1",
            duration_seconds=0.5,
        ),
    ]
    assert [event.sequence for event in sink.events] == [1, 2, 3]


def test_unknown_tool_emits_rejected_validation_and_unexecuted_finish() -> None:
    runtime, sink, _ = _runtime()

    result = runtime.execute(ToolInvocation.from_mapping("missing", {}))

    assert result.status is ToolResultStatus.ERROR
    validated, finished = (event.payload for event in sink.events)
    assert isinstance(validated, ToolValidated)
    assert validated.accepted is False
    assert validated.error_type == "UnknownToolError"
    assert isinstance(finished, ToolCallFinished)
    assert finished.executed is False
    assert finished.duration_seconds is None
    assert finished.status == "error"


def test_invalid_arguments_emit_rejected_validation_without_policy_event() -> None:
    runtime, sink, add = _runtime()

    runtime.execute(ToolInvocation.from_mapping("add", {"a": "two", "b": 3}))

    assert add.calls == 0
    assert [event.kind for event in sink.events] == ["tool_validated", "tool_call_finished"]
    validated = sink.events[0].payload
    assert isinstance(validated, ToolValidated)
    assert validated.accepted is False
    assert validated.error_type == "ToolInputValidationError"


def test_policy_denial_emits_decision_and_unexecuted_finish() -> None:
    runtime, sink, add = _runtime(
        policy=ToolNamePolicy.from_mapping({"add": ToolPolicyDecision.DENY})
    )

    runtime.execute(_add())

    assert add.calls == 0
    assert [event.kind for event in sink.events] == [
        "tool_validated",
        "tool_policy_decided",
        "tool_call_finished",
    ]
    decided = sink.events[1].payload
    assert isinstance(decided, ToolPolicyDecided)
    assert decided.decision == "deny"
    assert decided.reason is not None
    finished = sink.events[2].payload
    assert isinstance(finished, ToolCallFinished)
    assert finished.executed is False
    assert finished.error_type == "ToolPolicyDeniedError"


def test_approved_invocation_emits_request_and_resolution_before_execution() -> None:
    runtime, sink, add = _runtime(
        policy=ToolNamePolicy.from_mapping({"add": ToolPolicyDecision.REQUIRE_APPROVAL}),
        resolver=_Resolver(ToolApprovalDecision.APPROVED, "looks fine"),
    )

    result = runtime.execute(_add())

    assert result.status is ToolResultStatus.SUCCESS
    assert add.calls == 1
    assert [event.kind for event in sink.events] == [
        "tool_validated",
        "tool_policy_decided",
        "tool_approval_requested",
        "tool_approval_resolved",
        "tool_call_finished",
    ]
    requested = sink.events[2].payload
    assert isinstance(requested, ToolApprovalRequested)
    assert requested.arguments == (("a", 2), ("b", 3))
    resolved = sink.events[3].payload
    assert resolved == ToolApprovalResolved(
        tool_name="add", decision="approved", invocation_id="call-1", reason="looks fine"
    )


def test_rejected_approval_emits_resolution_and_unexecuted_finish() -> None:
    runtime, sink, add = _runtime(
        policy=ToolNamePolicy.from_mapping({"add": ToolPolicyDecision.REQUIRE_APPROVAL}),
        resolver=_Resolver(ToolApprovalDecision.REJECTED, "not now"),
    )

    runtime.execute(_add())

    assert add.calls == 0
    resolved = sink.events[3].payload
    assert isinstance(resolved, ToolApprovalResolved)
    assert resolved.decision == "rejected"
    finished = sink.events[4].payload
    assert isinstance(finished, ToolCallFinished)
    assert finished.executed is False
    assert finished.error_type == "ToolApprovalRejectedError"


def test_missing_resolver_emits_no_approval_events() -> None:
    runtime, sink, _ = _runtime(
        policy=ToolNamePolicy.from_mapping({"add": ToolPolicyDecision.REQUIRE_APPROVAL})
    )

    runtime.execute(_add())

    assert [event.kind for event in sink.events] == [
        "tool_validated",
        "tool_policy_decided",
        "tool_call_finished",
    ]
    finished = sink.events[2].payload
    assert isinstance(finished, ToolCallFinished)
    assert finished.error_type == "ToolApprovalRequiredError"


def test_tool_failure_emits_executed_error_finish_with_duration() -> None:
    runtime, sink, _ = _runtime()

    runtime.execute(ToolInvocation.from_mapping("explode", {}))

    finished = sink.events[-1].payload
    assert finished == ToolCallFinished(
        tool_name="explode",
        status="error",
        executed=True,
        duration_seconds=0.5,
        error_type="RuntimeError",
        error_message="boom",
    )


def test_raising_sink_does_not_change_result_or_trace() -> None:
    registry = ToolRegistry()
    registry.register(_AddTool())
    plain = ToolRuntime(registry)
    observed = ToolRuntime(registry, events=RunEventEmitter(_RaisingSink(), run_id="run-1"))

    assert observed.execute(_add()) == plain.execute(_add())
    assert observed.execution_traces == plain.execution_traces
