import pytest

from context_engine.tools import (
    AllowAllToolPolicy,
    DuplicateToolRegistrationError,
    Tool,
    ToolInputField,
    ToolInputSchema,
    ToolInvocation,
    ToolNamePolicy,
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
    assert traces[0].output_as_mapping() == {"value": 3}
    assert traces[1].invocation.tool_name == "multiply"
    assert traces[1].invocation.invocation_id == "call-b"
    assert traces[1].output_as_mapping() == {"value": 12}
