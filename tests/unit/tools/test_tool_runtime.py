import pytest

from context_engine.tools import (
    DuplicateToolRegistrationError,
    Tool,
    ToolInputField,
    ToolInputSchema,
    ToolInputValidationError,
    ToolInvocation,
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

    def execute(self, invocation: ToolInvocation) -> dict[str, object]:
        self.was_executed = True
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


def test_tool_registry_registers_and_looks_up_tool_deterministically() -> None:
    registry = ToolRegistry()
    tool = _AddTool()
    registry.register(tool)

    assert isinstance(tool, Tool)
    assert registry.get("add") is tool


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
    runtime = ToolRuntime(registry)

    result = runtime.execute(ToolInvocation.from_mapping("add", {"a": 2, "b": 3}))

    assert result.status is ToolResultStatus.SUCCESS
    assert result.output_as_mapping() == {"value": 5}
    assert result.error is None
    assert tool.was_executed is True


def test_tool_runtime_rejects_invalid_input_without_execution() -> None:
    registry = ToolRegistry()
    tool = _AddTool()
    registry.register(tool)
    runtime = ToolRuntime(registry)

    with pytest.raises(
        ToolInputValidationError,
        match="Type mismatches: a expected int, got str",
    ):
        runtime.execute(ToolInvocation.from_mapping("add", {"a": "2", "b": 3}))

    assert tool.was_executed is False


def test_tool_runtime_rejects_unknown_tool_invocation_deterministically() -> None:
    runtime = ToolRuntime(ToolRegistry())

    with pytest.raises(UnknownToolError, match="Unknown tool: unknown"):
        runtime.execute(ToolInvocation.from_mapping("unknown", {"a": 1}))


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
