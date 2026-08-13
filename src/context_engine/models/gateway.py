"""Provider-independent model gateway contracts."""

from collections.abc import Sequence
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
    usage: ModelUsage | None = None


@runtime_checkable
class ModelGateway(Protocol):
    """Provider-independent model interface used by the agent runtime."""

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a typed model response from a typed request."""


def normalize_messages(messages: Sequence[ModelMessage]) -> tuple[ModelMessage, ...]:
    """Return an immutable message tuple for request construction."""
    return tuple(messages)
