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


class ModelFinishReason(StrEnum):
    """Why model generation stopped."""

    STOP = "stop"
    LENGTH = "length"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class ModelMessage:
    """A single typed message in a model prompt."""

    role: ModelRole
    content: str


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

    @classmethod
    def from_mapping(cls, tool_name: str, arguments: Mapping[str, object]) -> ModelToolCall:
        """Construct an immutable tool call from mapping arguments."""
        return cls(tool_name=tool_name, arguments=normalize_tool_call_arguments(arguments))

    def arguments_as_mapping(self) -> dict[str, object]:
        """Return tool-call arguments as a mutable mapping."""
        return dict(self.arguments)


def normalize_tool_call_arguments(
    arguments: Mapping[str, object],
) -> tuple[tuple[str, object], ...]:
    """Return immutable normalized arguments for deterministic tool calls."""
    return tuple(sorted(arguments.items()))
