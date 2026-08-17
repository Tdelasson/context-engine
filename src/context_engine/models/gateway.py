"""Provider-independent model gateway contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable


class ModelRole(StrEnum):
    """Supported roles for model input messages."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ModelFinishReason(StrEnum):
    """Why model generation stopped."""

    STOP = "stop"
    LENGTH = "length"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class ModelMessage:
    """A single typed message in a model prompt."""

    role: ModelRole
    content: str = ""
    tool_call: ModelToolCall | None = None
    tool_result: ModelToolResult | None = None

    def __post_init__(self) -> None:
        if self.role is ModelRole.ASSISTANT and self.tool_result is not None:
            raise ValueError("ASSISTANT messages cannot include tool_result.")
        if self.role is ModelRole.TOOL:
            if self.tool_result is None:
                raise ValueError("TOOL messages must include tool_result.")
            if self.tool_call is not None:
                raise ValueError("TOOL messages cannot include tool_call.")
            return

        if self.tool_result is not None:
            raise ValueError("Only TOOL messages can include tool_result.")

        if self.role in {ModelRole.SYSTEM, ModelRole.USER} and self.tool_call is not None:
            raise ValueError("SYSTEM and USER messages cannot include tool_call.")


@dataclass(frozen=True, slots=True)
class ModelRequest:
    """Minimum provider-independent input required for model generation."""

    model_id: str
    messages: tuple[ModelMessage, ...]
    tools: tuple[ModelToolDefinition, ...] = ()
    max_output_tokens: int | None = None
    temperature: float | None = None


@dataclass(frozen=True, slots=True)
class ModelUsage:
    """Normalized model usage metrics."""

    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class ModelResponse:
    """Minimum provider-independent output returned by model generation."""

    model_id: str
    output_text: str
    finish_reason: ModelFinishReason
    tool_call: ModelToolCall | None = None
    usage: ModelUsage | None = None


@runtime_checkable
class ModelGateway(Protocol):
    """Provider-independent model interface used by the agent runtime."""

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a typed model response from a typed request."""


def normalize_messages(messages: Sequence[ModelMessage]) -> tuple[ModelMessage, ...]:
    """Return an immutable message tuple for request construction."""
    return tuple(messages)


def normalize_model_tools(
    tools: Sequence[ModelToolDefinition],
) -> tuple[ModelToolDefinition, ...]:
    """Return an immutable tool tuple for request construction."""
    return tuple(tools)


@dataclass(frozen=True, slots=True)
class ModelToolDefinition:
    """Provider-independent model-visible tool declaration."""

    name: str
    description: str
    input_schema: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class ModelToolCall:
    """Provider-independent model-requested tool call representation."""

    tool_name: str
    arguments: tuple[tuple[str, object], ...]
    tool_call_id: str | None = None

    @classmethod
    def from_mapping(
        cls,
        tool_name: str,
        arguments: Mapping[str, object],
        *,
        tool_call_id: str | None = None,
    ) -> ModelToolCall:
        """Construct an immutable tool call from mapping arguments."""
        return cls(
            tool_name=tool_name,
            arguments=normalize_tool_call_arguments(arguments),
            tool_call_id=tool_call_id,
        )

    def arguments_as_mapping(self) -> dict[str, object]:
        """Return tool-call arguments as a mutable mapping."""
        return dict(self.arguments)


def normalize_tool_call_arguments(
    arguments: Mapping[str, object],
) -> tuple[tuple[str, object], ...]:
    """Return immutable normalized arguments for deterministic tool calls."""
    return tuple(sorted(arguments.items()))


class ModelToolResultStatus(StrEnum):
    """Structured status for model-visible tool result messages."""

    SUCCESS = "success"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ModelToolResult:
    """Provider-independent tool result message payload for model history."""

    tool_name: str
    output: tuple[tuple[str, object], ...] | None = None
    status: ModelToolResultStatus = ModelToolResultStatus.SUCCESS
    tool_call_id: str | None = None
    error_type: str | None = None
    error_message: str | None = None

    @classmethod
    def success(
        cls,
        *,
        tool_name: str,
        output: Mapping[str, object],
        tool_call_id: str | None = None,
    ) -> ModelToolResult:
        """Construct a successful tool result payload."""
        return cls(
            tool_name=tool_name,
            output=normalize_tool_call_arguments(output),
            status=ModelToolResultStatus.SUCCESS,
            tool_call_id=tool_call_id,
        )

    @classmethod
    def error(
        cls,
        *,
        tool_name: str,
        error_type: str,
        error_message: str,
        tool_call_id: str | None = None,
    ) -> ModelToolResult:
        """Construct an error tool result payload."""
        return cls(
            tool_name=tool_name,
            status=ModelToolResultStatus.ERROR,
            tool_call_id=tool_call_id,
            error_type=error_type,
            error_message=error_message,
        )

    def __post_init__(self) -> None:
        if self.status is ModelToolResultStatus.SUCCESS:
            if self.error_type is not None or self.error_message is not None:
                raise ValueError("Successful tool results cannot include error details.")
            return

        if self.error_type is None or self.error_message is None:
            raise ValueError("Error tool results must include error_type and error_message.")

    def output_as_mapping(self) -> dict[str, object]:
        """Return tool output payload as a mutable mapping."""
        return {} if self.output is None else dict(self.output)
