"""Provider-independent deterministic tool runtime contracts and execution."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from context_engine.observability import (
    RunEventEmitter,
    RunEventPayload,
    ToolApprovalRequested,
    ToolApprovalResolved,
    ToolCallFinished,
    ToolPolicyDecided,
    ToolValidated,
)
from context_engine.tools.approval import (
    ToolApprovalDecision,
    ToolApprovalRequest,
    ToolApprovalResolver,
)
from context_engine.tools.errors import (
    DuplicateToolRegistrationError,
    ToolApprovalRejectedError,
    ToolApprovalRequiredError,
    ToolInputValidationError,
    ToolPolicyDeniedError,
    UnknownToolError,
)
from context_engine.tools.policy import (
    AllowAllToolPolicy,
    ToolPolicy,
    ToolPolicyDecision,
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
    invocation_id: str | None = None

    @classmethod
    def from_mapping(
        cls,
        tool_name: str,
        arguments: Mapping[str, object],
        *,
        invocation_id: str | None = None,
    ) -> "ToolInvocation":
        """Construct a typed immutable invocation from a mapping."""
        return cls(
            tool_name=tool_name,
            arguments=normalize_tool_arguments(arguments),
            invocation_id=invocation_id,
        )

    def arguments_as_mapping(self) -> dict[str, object]:
        """Return invocation arguments as a dictionary."""
        return dict(self.arguments)


@dataclass(frozen=True, slots=True)
class ToolOutput:
    """Tool output split into what the model sees and what only the runtime records.

    ``model`` becomes the tool result sent to the model. ``diagnostics`` is kept on the
    execution trace for observability and is never sent to the model.
    """

    model: Mapping[str, object]
    diagnostics: Mapping[str, object] | None = None


@runtime_checkable
class Tool(Protocol):
    """Provider-independent typed tool contract."""

    name: str
    description: str
    input_schema: ToolInputSchema

    def execute(self, invocation: ToolInvocation) -> Mapping[str, object] | ToolOutput:
        """Execute a tool invocation.

        Return a mapping when every output field is for the model, or a ``ToolOutput``
        to keep runtime-only diagnostics out of the model's view.
        """


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


@dataclass(frozen=True, slots=True)
class ToolExecutionTrace:
    """Provider-independent structured trace for one tool invocation."""

    invocation: ToolInvocation
    policy_decision: ToolPolicyDecision | None
    approval_decision: ToolApprovalDecision | None
    status: ToolResultStatus
    output: tuple[tuple[str, object], ...] | None = None
    error: ToolExecutionErrorDetails | None = None
    diagnostics: tuple[tuple[str, object], ...] | None = None

    def output_as_mapping(self) -> dict[str, object]:
        """Return traced output payload as a dictionary."""
        return {} if self.output is None else dict(self.output)

    def diagnostics_as_mapping(self) -> dict[str, object]:
        """Return runtime-only tool diagnostics as a dictionary."""
        return {} if self.diagnostics is None else dict(self.diagnostics)


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

    def __init__(
        self,
        registry: ToolRegistry,
        policy: ToolPolicy | None = None,
        approval_resolver: ToolApprovalResolver | None = None,
        events: RunEventEmitter | None = None,
    ) -> None:
        self._registry = registry
        self._policy = policy or AllowAllToolPolicy()
        self._approval_resolver = approval_resolver
        self._events = events
        self._execution_traces: list[ToolExecutionTrace] = []

    def list_tools(self) -> tuple[Tool, ...]:
        """Expose registered tools for model-facing declaration only."""
        return self._registry.list_tools()

    @property
    def execution_traces(self) -> tuple[ToolExecutionTrace, ...]:
        """Return structured tool execution traces in deterministic execution order."""
        return tuple(self._execution_traces)

    def execute(self, invocation: ToolInvocation) -> ToolResult:
        """Resolve, validate, and execute one invocation deterministically."""
        policy_decision: ToolPolicyDecision | None = None
        approval_decision: ToolApprovalDecision | None = None
        diagnostics: Mapping[str, object] | None = None
        validated = False
        started: float | None = None
        try:
            tool = self._registry.get(invocation.tool_name)
            arguments = invocation.arguments_as_mapping()
            tool.input_schema.validate(arguments)
            validated = True
            self._emit(
                ToolValidated(
                    tool_name=invocation.tool_name,
                    accepted=True,
                    invocation_id=invocation.invocation_id,
                )
            )
            policy_evaluation = self._policy.evaluate(invocation)
            policy_decision = policy_evaluation.decision
            self._emit(
                ToolPolicyDecided(
                    tool_name=invocation.tool_name,
                    decision=policy_decision.value,
                    invocation_id=invocation.invocation_id,
                    reason=policy_evaluation.reason,
                )
            )
            if policy_evaluation.decision is ToolPolicyDecision.DENY:
                raise ToolPolicyDeniedError(
                    policy_evaluation.reason
                    or f"Tool invocation denied by policy: {invocation.tool_name}"
                )
            if policy_evaluation.decision is ToolPolicyDecision.REQUIRE_APPROVAL:
                if self._approval_resolver is None:
                    raise ToolApprovalRequiredError(
                        "Tool invocation requires explicit human approval, "
                        "but no approval resolver is configured."
                    )
                self._emit(
                    ToolApprovalRequested(
                        tool_name=invocation.tool_name,
                        arguments=invocation.arguments,
                        invocation_id=invocation.invocation_id,
                        reason=policy_evaluation.reason,
                    )
                )
                approval_resolution = self._approval_resolver.resolve(
                    ToolApprovalRequest(
                        invocation=invocation,
                        policy_evaluation=policy_evaluation,
                    )
                )
                approval_decision = approval_resolution.decision
                self._emit(
                    ToolApprovalResolved(
                        tool_name=invocation.tool_name,
                        decision=approval_decision.value,
                        invocation_id=invocation.invocation_id,
                        reason=approval_resolution.reason,
                    )
                )
                if approval_resolution.decision is ToolApprovalDecision.REJECTED:
                    raise ToolApprovalRejectedError(
                        approval_resolution.reason
                        or f"Tool invocation rejected by human approval: {invocation.tool_name}"
                    )
            started = self._monotonic()
            returned = tool.execute(invocation)
            if isinstance(returned, ToolOutput):
                output, diagnostics = returned.model, returned.diagnostics
            else:
                output, diagnostics = returned, None
        except Exception as exc:
            error = ToolExecutionErrorDetails(error_type=type(exc).__name__, message=str(exc))
            if not validated:
                self._emit(
                    ToolValidated(
                        tool_name=invocation.tool_name,
                        accepted=False,
                        invocation_id=invocation.invocation_id,
                        error_type=error.error_type,
                        error_message=error.message,
                    )
                )
            return self._finish(
                ToolResult(invocation=invocation, status=ToolResultStatus.ERROR, error=error),
                policy_decision=policy_decision,
                approval_decision=approval_decision,
                started=started,
            )

        return self._finish(
            ToolResult(
                invocation=invocation,
                status=ToolResultStatus.SUCCESS,
                output=normalize_tool_arguments(output),
            ),
            policy_decision=policy_decision,
            approval_decision=approval_decision,
            started=started,
            diagnostics=diagnostics,
        )

    def _finish(
        self,
        result: ToolResult,
        *,
        policy_decision: ToolPolicyDecision | None,
        approval_decision: ToolApprovalDecision | None,
        started: float | None,
        diagnostics: Mapping[str, object] | None = None,
    ) -> ToolResult:
        """Record the trace and the terminal event for one invocation."""
        duration = None if started is None else max(0.0, self._monotonic() - started)
        self._execution_traces.append(
            ToolExecutionTrace(
                invocation=result.invocation,
                policy_decision=policy_decision,
                approval_decision=approval_decision,
                status=result.status,
                output=result.output,
                error=result.error,
                diagnostics=None if diagnostics is None else normalize_tool_arguments(diagnostics),
            )
        )
        self._emit(
            ToolCallFinished(
                tool_name=result.invocation.tool_name,
                status=result.status.value,
                executed=started is not None,
                invocation_id=result.invocation.invocation_id,
                duration_seconds=duration,
                error_type=None if result.error is None else result.error.error_type,
                error_message=None if result.error is None else result.error.message,
            )
        )
        return result

    def _emit(self, payload: RunEventPayload) -> None:
        if self._events is not None:
            self._events.emit(payload)

    def _monotonic(self) -> float:
        return 0.0 if self._events is None else self._events.monotonic()
