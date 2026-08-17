"""Provider-independent deterministic tool runtime contracts and execution."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from context_engine.tools.errors import (
    DuplicateToolRegistrationError,
    ToolInputValidationError,
    ToolRuntimeError,
    UnknownToolError,
)


@dataclass(frozen=True, slots=True)
class ToolInputField:
    """Typed declaration for one expected tool input field."""

    name: str
    value_type: type[object]


@dataclass(frozen=True, slots=True)
class ToolInputSchema:
    """Explicit typed schema used to validate tool invocation inputs."""

    fields: tuple[ToolInputField, ...]

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for field in self.fields:
            if field.name in seen:
                raise ValueError(f"Duplicate tool input field name: {field.name}")
            seen.add(field.name)

    def validate(self, arguments: Mapping[str, object]) -> None:
        """Validate invocation arguments deterministically against the schema."""
        expected = {field.name: field.value_type for field in self.fields}
        missing_fields = [field.name for field in self.fields if field.name not in arguments]
        unknown_fields = sorted(name for name in arguments if name not in expected)

        type_mismatches: list[str] = []
        for field in self.fields:
            if field.name not in arguments:
                continue
            value = arguments[field.name]
            if not isinstance(value, field.value_type):
                type_mismatches.append(
                    f"{field.name} expected {field.value_type.__name__}, got {type(value).__name__}"
                )

        failures: list[str] = []
        if missing_fields:
            failures.append(f"Missing required fields: {', '.join(missing_fields)}")
        if unknown_fields:
            failures.append(f"Unknown fields: {', '.join(unknown_fields)}")
        if type_mismatches:
            failures.append(f"Type mismatches: {', '.join(type_mismatches)}")

        if failures:
            raise ToolInputValidationError("; ".join(failures))


def normalize_tool_arguments(arguments: Mapping[str, object]) -> tuple[tuple[str, object], ...]:
    """Return immutable normalized arguments for deterministic tool invocation."""
    return tuple(sorted(arguments.items()))


@dataclass(frozen=True, slots=True)
class ToolInvocation:
    """Typed tool invocation request representation."""

    tool_name: str
    arguments: tuple[tuple[str, object], ...]

    @classmethod
    def from_mapping(cls, tool_name: str, arguments: Mapping[str, object]) -> "ToolInvocation":
        """Construct a typed immutable invocation from a mapping."""
        return cls(tool_name=tool_name, arguments=normalize_tool_arguments(arguments))

    def arguments_as_mapping(self) -> dict[str, object]:
        """Return invocation arguments as a dictionary."""
        return dict(self.arguments)


@runtime_checkable
class Tool(Protocol):
    """Provider-independent typed tool contract."""

    name: str
    description: str
    input_schema: ToolInputSchema

    def execute(self, invocation: ToolInvocation) -> Mapping[str, object]:
        """Execute a tool invocation and return structured output."""


class ToolResultStatus(StrEnum):
    """Deterministic outcomes for runtime-owned tool execution."""

    SUCCESS = "success"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ToolExecutionErrorDetails:
    """Structured execution failure details."""

    error_type: str
    message: str


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Typed structured result returned by tool runtime execution."""

    invocation: ToolInvocation
    status: ToolResultStatus
    output: tuple[tuple[str, object], ...] | None = None
    error: ToolExecutionErrorDetails | None = None

    def output_as_mapping(self) -> dict[str, object]:
        """Return output payload as a dictionary."""
        return {} if self.output is None else dict(self.output)


class ToolRegistry:
    """Explicit deterministic in-memory tool registration and lookup."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register one tool by explicit unique name."""
        if tool.name in self._tools:
            raise DuplicateToolRegistrationError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, tool_name: str) -> Tool:
        """Return a registered tool, or raise if not registered."""
        tool = self._tools.get(tool_name)
        if tool is None:
            raise UnknownToolError(f"Unknown tool: {tool_name}")
        return tool

    def list_tools(self) -> tuple[Tool, ...]:
        """Return all registered tools in deterministic name order."""
        return tuple(self._tools[name] for name in sorted(self._tools))


class ToolRuntime:
    """Runtime-owned deterministic boundary for tool invocation and execution."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def list_tools(self) -> tuple[Tool, ...]:
        """Expose registered tools for model-facing declaration only."""
        return self._registry.list_tools()

    def execute(self, invocation: ToolInvocation) -> ToolResult:
        """Resolve, validate, and execute one invocation deterministically."""
        try:
            tool = self._registry.get(invocation.tool_name)
            arguments = invocation.arguments_as_mapping()
            tool.input_schema.validate(arguments)
            output = tool.execute(invocation)
        except ToolRuntimeError as exc:
            return ToolResult(
                invocation=invocation,
                status=ToolResultStatus.ERROR,
                error=ToolExecutionErrorDetails(
                    error_type=type(exc).__name__,
                    message=str(exc),
                ),
            )
        except Exception as exc:
            return ToolResult(
                invocation=invocation,
                status=ToolResultStatus.ERROR,
                error=ToolExecutionErrorDetails(
                    error_type=type(exc).__name__,
                    message=str(exc),
                ),
            )

        return ToolResult(
            invocation=invocation,
            status=ToolResultStatus.SUCCESS,
            output=normalize_tool_arguments(output),
        )
