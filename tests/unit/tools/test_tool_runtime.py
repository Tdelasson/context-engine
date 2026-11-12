import pytest

from context_engine.tools import (
    AllowAllToolPolicy,
    DuplicateToolRegistrationError,
    Tool,
    ToolApprovalDecision,
    ToolApprovalRequest,
    ToolApprovalResolution,
    ToolInputField,
    ToolInputSchema,
    ToolInvocation,
    ToolNamePolicy,
    ToolOutput,
    ToolPolicyDecision,
    ToolPolicyEvaluation,
    ToolRegistry,
    ToolResultStatus,
    ToolRuntime,
    UnknownToolError,
)


class _AddTool:
    name = "add"
    description = "Add two integers."
    input_schema = ToolInputSchema(
        fields=(
            ToolInputField(name="a", value_type=int),
            ToolInputField(name="b", value_type=int),
        )
    )

    def __init__(self) -> None:
        self.was_executed = False
        self.last_invocation: ToolInvocation | None = None

    def execute(self, invocation: ToolInvocation) -> dict[str, object]:
        self.was_executed = True
        self.last_invocation = invocation
        arguments = invocation.arguments_as_mapping()
        a = arguments["a"]
        b = arguments["b"]
        if not isinstance(a, int) or not isinstance(b, int):
            raise RuntimeError("validated add tool received invalid argument types")
        return {"value": a + b}


class _FailingTool:
    name = "explode"
    description = "Raise an execution error."
    input_schema = ToolInputSchema(fields=(ToolInputField(name="message", value_type=str),))

    def execute(self, invocation: ToolInvocation) -> dict[str, object]:
        message = invocation.arguments_as_mapping()["message"]
        raise RuntimeError(f"failed: {message}")


class _MultiplyTool:
    name = "multiply"
    description = "Multiply two integers."
    input_schema = ToolInputSchema(
        fields=(ToolInputField(name="a", value_type=int), ToolInputField(name="b", value_type=int))
    )

    def __init__(self) -> None:
        self.was_executed = False

    def execute(self, invocation: ToolInvocation) -> dict[str, object]:
        self.was_executed = True
        arguments = invocation.arguments_as_mapping()
        a = arguments["a"]
        b = arguments["b"]
        if not isinstance(a, int) or not isinstance(b, int):
            raise RuntimeError("validated multiply tool received invalid argument types")
        return {"value": a * b}


class _RecordingPolicy:
    def __init__(self, decision: ToolPolicyDecision) -> None:
        self._decision = decision
        self.evaluated: list[ToolInvocation] = []

    def evaluate(self, invocation: ToolInvocation) -> ToolPolicyEvaluation:
        self.evaluated.append(invocation)
        return ToolPolicyEvaluation(decision=self._decision)


class _RecordingApprovalResolver:
    def __init__(self, decision: ToolApprovalDecision, reason: str | None = None) -> None:
        self._decision = decision
        self._reason = reason
        self.requests: list[ToolApprovalRequest] = []

    def resolve(self, request: ToolApprovalRequest) -> ToolApprovalResolution:
        self.requests.append(request)
        return ToolApprovalResolution(decision=self._decision, reason=self._reason)


def test_tool_registry_registers_and_looks_up_tool_deterministically() -> None:
    registry = ToolRegistry()
    tool = _AddTool()
    registry.register(tool)

    assert isinstance(tool, Tool)
    assert registry.get("add") is tool


def test_tool_registry_lists_tools_in_deterministic_name_order() -> None:
    registry = ToolRegistry()
    add_tool = _AddTool()
    multiply_tool = _MultiplyTool()
    registry.register(multiply_tool)
    registry.register(add_tool)

    assert tuple(tool.name for tool in registry.list_tools()) == ("add", "multiply")


def test_tool_registry_rejects_duplicate_registration() -> None:
    registry = ToolRegistry()
    registry.register(_AddTool())

    with pytest.raises(DuplicateToolRegistrationError, match="Tool already registered: add"):
        registry.register(_AddTool())


def test_tool_registry_rejects_unknown_tool_lookup() -> None:
    registry = ToolRegistry()

    with pytest.raises(UnknownToolError, match="Unknown tool: missing"):
        registry.get("missing")


def test_tool_runtime_executes_valid_tool_invocation_and_returns_structured_result() -> None:
    registry = ToolRegistry()
    tool = _AddTool()
    registry.register(tool)
    runtime = ToolRuntime(registry, policy=AllowAllToolPolicy())
    invocation = ToolInvocation.from_mapping("add", {"a": 2, "b": 3})

    result = runtime.execute(invocation)

    assert result.status is ToolResultStatus.SUCCESS
    assert result.output_as_mapping() == {"value": 5}
    assert result.error is None
    assert tool.was_executed is True
    assert tool.last_invocation is invocation
    assert len(runtime.execution_traces) == 1
    trace = runtime.execution_traces[0]
    assert trace.invocation.tool_name == "add"
    assert trace.invocation.arguments_as_mapping() == {"a": 2, "b": 3}
    assert trace.policy_decision is ToolPolicyDecision.ALLOW
    assert trace.approval_decision is None
    assert trace.status is ToolResultStatus.SUCCESS
    assert trace.output_as_mapping() == {"value": 5}
    assert trace.error is None


def test_tool_runtime_evaluates_allow_policy_before_execution() -> None:
    registry = ToolRegistry()
    tool = _AddTool()
    registry.register(tool)
    policy = _RecordingPolicy(ToolPolicyDecision.ALLOW)
    runtime = ToolRuntime(registry, policy=policy)
    invocation = ToolInvocation.from_mapping("add", {"a": 2, "b": 3})

    result = runtime.execute(invocation)

    assert result.status is ToolResultStatus.SUCCESS
    assert policy.evaluated == [invocation]
    assert tool.was_executed is True


def test_tool_runtime_denies_tool_invocation_without_execution() -> None:
    registry = ToolRegistry()
    tool = _AddTool()
    registry.register(tool)
    policy = ToolNamePolicy.from_mapping({"add": ToolPolicyDecision.DENY})
    runtime = ToolRuntime(registry, policy=policy)

    result = runtime.execute(
        ToolInvocation.from_mapping("add", {"a": 2, "b": 3}, invocation_id="tool-call-1")
    )

    assert result.status is ToolResultStatus.ERROR
    assert result.output is None
    assert result.error is not None
    assert result.error.error_type == "ToolPolicyDeniedError"
    assert result.error.message == "Tool invocation denied by policy: add"
    assert tool.was_executed is False
    assert len(runtime.execution_traces) == 1
    trace = runtime.execution_traces[0]
    assert trace.invocation.tool_name == "add"
    assert trace.invocation.arguments_as_mapping() == {"a": 2, "b": 3}
    assert trace.invocation.invocation_id == "tool-call-1"
    assert trace.policy_decision is ToolPolicyDecision.DENY
    assert trace.approval_decision is None
    assert trace.status is ToolResultStatus.ERROR
    assert trace.error is not None
    assert trace.error.error_type == "ToolPolicyDeniedError"
    assert trace.error.message == "Tool invocation denied by policy: add"


def test_tool_runtime_policy_can_distinguish_tools_deterministically() -> None:
    registry = ToolRegistry()
    add_tool = _AddTool()
    multiply_tool = _MultiplyTool()
    registry.register(add_tool)
    registry.register(multiply_tool)
    policy = ToolNamePolicy.from_mapping({"add": ToolPolicyDecision.DENY})
    runtime = ToolRuntime(registry, policy=policy)

    denied_result = runtime.execute(ToolInvocation.from_mapping("add", {"a": 2, "b": 3}))
    allowed_result = runtime.execute(ToolInvocation.from_mapping("multiply", {"a": 2, "b": 3}))

    assert denied_result.status is ToolResultStatus.ERROR
    assert denied_result.error is not None
    assert denied_result.error.error_type == "ToolPolicyDeniedError"
    assert add_tool.was_executed is False
    assert allowed_result.status is ToolResultStatus.SUCCESS
    assert allowed_result.output_as_mapping() == {"value": 6}
    assert multiply_tool.was_executed is True


def test_tool_name_policy_can_require_human_approval_for_selected_tool() -> None:
    policy = ToolNamePolicy.from_mapping({"add": ToolPolicyDecision.REQUIRE_APPROVAL})
    invocation = ToolInvocation.from_mapping("add", {"a": 2, "b": 3})

    evaluation = policy.evaluate(invocation)

    assert evaluation.decision is ToolPolicyDecision.REQUIRE_APPROVAL
    assert evaluation.reason == "Tool invocation requires explicit human approval: add"


def test_tool_runtime_requests_approval_before_execution_and_executes_once_when_approved() -> None:
    registry = ToolRegistry()
    resolver = _RecordingApprovalResolver(ToolApprovalDecision.APPROVED)

    class _ApprovalOrderTool:
        name = "add"
        description = "Add two integers."
        input_schema = ToolInputSchema(
            fields=(
                ToolInputField(name="a", value_type=int),
                ToolInputField(name="b", value_type=int),
            )
        )

        def __init__(self) -> None:
            self.execute_count = 0
            self.approval_request_count_at_execute: int | None = None

        def execute(self, invocation: ToolInvocation) -> dict[str, object]:
            self.execute_count += 1
            self.approval_request_count_at_execute = len(resolver.requests)
            arguments = invocation.arguments_as_mapping()
            a = arguments["a"]
            b = arguments["b"]
            if not isinstance(a, int) or not isinstance(b, int):
                raise RuntimeError("validated add tool received invalid argument types")
            return {"value": a + b}

    tool = _ApprovalOrderTool()
    registry.register(tool)
    runtime = ToolRuntime(
        registry,
        policy=ToolNamePolicy.from_mapping({"add": ToolPolicyDecision.REQUIRE_APPROVAL}),
        approval_resolver=resolver,
    )
    invocation = ToolInvocation.from_mapping(
        "add",
        {"a": 2, "b": 3},
        invocation_id="tool-call-approval-1",
    )

    result = runtime.execute(invocation)

    assert result.status is ToolResultStatus.SUCCESS
    assert result.output_as_mapping() == {"value": 5}
    assert tool.execute_count == 1
    assert tool.approval_request_count_at_execute == 1
    assert len(resolver.requests) == 1
    assert resolver.requests[0].invocation is invocation
    assert resolver.requests[0].invocation.invocation_id == "tool-call-approval-1"
    assert resolver.requests[0].policy_evaluation.decision is ToolPolicyDecision.REQUIRE_APPROVAL
    assert len(runtime.execution_traces) == 1
    trace = runtime.execution_traces[0]
    assert trace.invocation.invocation_id == "tool-call-approval-1"
    assert trace.policy_decision is ToolPolicyDecision.REQUIRE_APPROVAL
    assert trace.approval_decision is ToolApprovalDecision.APPROVED
    assert trace.status is ToolResultStatus.SUCCESS


def test_tool_runtime_rejected_approval_does_not_execute_and_returns_structured_error() -> None:
    registry = ToolRegistry()
    tool = _AddTool()
    registry.register(tool)
    resolver = _RecordingApprovalResolver(
        ToolApprovalDecision.REJECTED,
        reason="Human rejected this invocation.",
    )
    runtime = ToolRuntime(
        registry,
        policy=ToolNamePolicy.from_mapping({"add": ToolPolicyDecision.REQUIRE_APPROVAL}),
        approval_resolver=resolver,
    )
    invocation = ToolInvocation.from_mapping(
        "add",
        {"a": 2, "b": 3},
        invocation_id="tool-call-approval-2",
    )

    result = runtime.execute(invocation)

    assert result.status is ToolResultStatus.ERROR
    assert result.error is not None
    assert result.error.error_type == "ToolApprovalRejectedError"
    assert result.error.message == "Human rejected this invocation."
    assert tool.was_executed is False
    assert len(resolver.requests) == 1
    assert resolver.requests[0].invocation.invocation_id == "tool-call-approval-2"
    assert len(runtime.execution_traces) == 1
    trace = runtime.execution_traces[0]
    assert trace.invocation.invocation_id == "tool-call-approval-2"
    assert trace.policy_decision is ToolPolicyDecision.REQUIRE_APPROVAL
    assert trace.approval_decision is ToolApprovalDecision.REJECTED
    assert trace.status is ToolResultStatus.ERROR
    assert trace.error is not None
    assert trace.error.error_type == "ToolApprovalRejectedError"


def test_tool_runtime_returns_error_when_approval_is_required_without_resolver() -> None:
    registry = ToolRegistry()
    tool = _AddTool()
    registry.register(tool)
    runtime = ToolRuntime(
        registry,
        policy=ToolNamePolicy.from_mapping({"add": ToolPolicyDecision.REQUIRE_APPROVAL}),
    )

    result = runtime.execute(ToolInvocation.from_mapping("add", {"a": 2, "b": 3}))

    assert result.status is ToolResultStatus.ERROR
    assert result.error is not None
    assert result.error.error_type == "ToolApprovalRequiredError"
    assert tool.was_executed is False
    assert len(runtime.execution_traces) == 1
    trace = runtime.execution_traces[0]
    assert trace.policy_decision is ToolPolicyDecision.REQUIRE_APPROVAL
    assert trace.approval_decision is None
    assert trace.status is ToolResultStatus.ERROR
    assert trace.error is not None
    assert trace.error.error_type == "ToolApprovalRequiredError"
    assert (
        trace.error.message == "Tool invocation requires explicit human approval, "
        "but no approval resolver is configured."
    )


def test_tool_runtime_rejects_invalid_input_without_execution() -> None:
    registry = ToolRegistry()
    tool = _AddTool()
    registry.register(tool)
    runtime = ToolRuntime(registry)

    result = runtime.execute(ToolInvocation.from_mapping("add", {"a": "2", "b": 3}))
    assert result.status is ToolResultStatus.ERROR
    assert result.output is None
    assert result.error is not None
    assert result.error.error_type == "ToolInputValidationError"
    assert "Type mismatches: a expected int, got str" in result.error.message
    assert tool.was_executed is False
    assert len(runtime.execution_traces) == 1
    trace = runtime.execution_traces[0]
    assert trace.invocation.tool_name == "add"
    assert trace.invocation.arguments_as_mapping() == {"a": "2", "b": 3}
    assert trace.policy_decision is None
    assert trace.approval_decision is None
    assert trace.status is ToolResultStatus.ERROR
    assert trace.error is not None
    assert trace.error.error_type == "ToolInputValidationError"


def test_tool_runtime_validates_input_before_policy_evaluation() -> None:
    registry = ToolRegistry()
    tool = _AddTool()
    registry.register(tool)
    policy = _RecordingPolicy(ToolPolicyDecision.ALLOW)
    runtime = ToolRuntime(registry, policy=policy)

    result = runtime.execute(ToolInvocation.from_mapping("add", {"a": "2", "b": 3}))

    assert result.status is ToolResultStatus.ERROR
    assert result.error is not None
    assert result.error.error_type == "ToolInputValidationError"
    assert policy.evaluated == []
    assert tool.was_executed is False


def test_tool_runtime_rejects_unknown_tool_invocation_deterministically() -> None:
    runtime = ToolRuntime(ToolRegistry())
    result = runtime.execute(ToolInvocation.from_mapping("unknown", {"a": 1}))
    assert result.status is ToolResultStatus.ERROR
    assert result.output is None
    assert result.error is not None
    assert result.error.error_type == "UnknownToolError"
    assert result.error.message == "Unknown tool: unknown"
    assert len(runtime.execution_traces) == 1
    trace = runtime.execution_traces[0]
    assert trace.invocation.tool_name == "unknown"
    assert trace.invocation.arguments_as_mapping() == {"a": 1}
    assert trace.policy_decision is None
    assert trace.approval_decision is None
    assert trace.status is ToolResultStatus.ERROR
    assert trace.error is not None
    assert trace.error.error_type == "UnknownToolError"


def test_tool_runtime_captures_execution_failure_as_structured_error_result() -> None:
    registry = ToolRegistry()
    registry.register(_FailingTool())
    runtime = ToolRuntime(registry)

    result = runtime.execute(ToolInvocation.from_mapping("explode", {"message": "boom"}))

    assert result.status is ToolResultStatus.ERROR
    assert result.output is None
    assert result.error is not None
    assert result.error.error_type == "RuntimeError"
    assert result.error.message == "failed: boom"
    assert len(runtime.execution_traces) == 1
    trace = runtime.execution_traces[0]
    assert trace.invocation.tool_name == "explode"
    assert trace.invocation.arguments_as_mapping() == {"message": "boom"}
    assert trace.policy_decision is ToolPolicyDecision.ALLOW
    assert trace.approval_decision is None
    assert trace.status is ToolResultStatus.ERROR
    assert trace.output is None
    assert trace.error is not None
    assert trace.error.error_type == "RuntimeError"
    assert trace.error.message == "failed: boom"


def test_tool_runtime_records_distinct_traces_in_deterministic_execution_order() -> None:
    registry = ToolRegistry()
    add_tool = _AddTool()
    multiply_tool = _MultiplyTool()
    registry.register(add_tool)
    registry.register(multiply_tool)
    runtime = ToolRuntime(registry, policy=AllowAllToolPolicy())

    runtime.execute(ToolInvocation.from_mapping("add", {"a": 1, "b": 2}, invocation_id="call-a"))
    runtime.execute(
        ToolInvocation.from_mapping("multiply", {"a": 3, "b": 4}, invocation_id="call-b")
    )

    traces = runtime.execution_traces
    assert len(traces) == 2
    assert traces[0].invocation.tool_name == "add"
    assert traces[0].invocation.invocation_id == "call-a"
    assert traces[0].approval_decision is None
    assert traces[0].output_as_mapping() == {"value": 3}
    assert traces[1].invocation.tool_name == "multiply"
    assert traces[1].invocation.invocation_id == "call-b"
    assert traces[1].approval_decision is None
    assert traces[1].output_as_mapping() == {"value": 12}


class _DiagnosedTool:
    name = "lookup"
    description = "Return an answer and runtime-only diagnostics."
    input_schema = ToolInputSchema(fields=(ToolInputField(name="key", value_type=str),))

    def execute(self, invocation: ToolInvocation) -> ToolOutput:
        key = invocation.arguments_as_mapping()["key"]
        return ToolOutput(model={"value": f"answer-{key}"}, diagnostics={"cache": "miss"})


def test_tool_runtime_keeps_tool_diagnostics_on_the_trace_only() -> None:
    registry = ToolRegistry()
    registry.register(_DiagnosedTool())
    runtime = ToolRuntime(registry)

    result = runtime.execute(ToolInvocation.from_mapping("lookup", {"key": "k"}))

    assert result.status is ToolResultStatus.SUCCESS
    assert result.output_as_mapping() == {"value": "answer-k"}
    trace = runtime.execution_traces[0]
    assert trace.output_as_mapping() == {"value": "answer-k"}
    assert trace.diagnostics_as_mapping() == {"cache": "miss"}


def test_tool_runtime_records_no_diagnostics_for_a_plain_mapping_output() -> None:
    registry = ToolRegistry()
    registry.register(_AddTool())
    runtime = ToolRuntime(registry)

    runtime.execute(ToolInvocation.from_mapping("add", {"a": 1, "b": 2}))

    assert runtime.execution_traces[0].diagnostics is None


class _MalformedOutputTool:
    name = "malformed"
    description = "Return output that is not a mapping."
    input_schema = ToolInputSchema(fields=(ToolInputField(name="part", value_type=str),))

    def execute(self, invocation: ToolInvocation) -> object:
        if invocation.arguments_as_mapping()["part"] == "diagnostics":
            return ToolOutput(model={"value": 1}, diagnostics=[("cache", "miss")])  # type: ignore[arg-type]
        return ToolOutput(model=[("value", 1)])  # type: ignore[arg-type]


@pytest.mark.parametrize("part", ["diagnostics", "model"])
def test_tool_runtime_traces_malformed_tool_output_as_an_error_result(part: str) -> None:
    registry = ToolRegistry()
    registry.register(_MalformedOutputTool())  # type: ignore[arg-type]
    runtime = ToolRuntime(registry)

    result = runtime.execute(ToolInvocation.from_mapping("malformed", {"part": part}))

    assert result.status is ToolResultStatus.ERROR
    assert result.error is not None and result.error.error_type == "ToolOutputValidationError"
    assert [trace.status for trace in runtime.execution_traces] == [ToolResultStatus.ERROR]
