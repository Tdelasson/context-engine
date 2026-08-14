"""Provider-independent model decision boundary for agent runtime semantics."""

from dataclasses import dataclass
from enum import StrEnum

from context_engine.models import ModelFinishReason, ModelResponse


class ModelDecisionKind(StrEnum):
    """Supported runtime-level outcomes interpreted from model responses."""

    RESPOND = "respond"
    RETRY = "retry"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class ModelDecision:
    """Typed runtime decision interpreted from a provider-independent response."""

    kind: ModelDecisionKind
    proposed_response: str | None = None


class ModelDecisionInterpretationError(ValueError):
    """Raised when a model response cannot be interpreted into a runtime decision."""


def interpret_model_response(response: ModelResponse) -> ModelDecision:
    """Deterministically interpret a typed model response into a runtime decision."""
    if response.finish_reason is ModelFinishReason.STOP:
        return ModelDecision(
            kind=ModelDecisionKind.RESPOND,
            proposed_response=response.output_text,
        )

    if response.finish_reason is ModelFinishReason.LENGTH:
        return ModelDecision(kind=ModelDecisionKind.RETRY)

    if response.finish_reason is ModelFinishReason.OTHER:
        return ModelDecision(kind=ModelDecisionKind.FAIL)

    raise ModelDecisionInterpretationError(
        f"Unsupported model finish reason for decision interpretation: {response.finish_reason!r}"
    )
