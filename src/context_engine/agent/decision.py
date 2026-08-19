"""Provider-independent model decision boundary for agent runtime semantics."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from context_engine.models import ModelFinishReason, ModelResponse
from context_engine.tools import normalize_tool_arguments


class ModelDecisionKind(StrEnum):
    """Supported runtime-level outcomes interpreted from model responses."""

    RESPOND = "respond"
    RETRY = "retry"
    FAIL = "fail"
    TOOL_CALL = "tool_call"


@dataclass(frozen=True, slots=True)
class ModelDecision:
    """Typed runtime decision interpreted from a provider-independent response."""

    kind: ModelDecisionKind
    proposed_response: str | None = None
    tool_name: str | None = None
    tool_arguments: tuple[tuple[str, object], ...] | None = None
    tool_call_id: str | None = None

    @classmethod
    def tool_call(
        cls,
        tool_name: str,
        arguments: Mapping[str, object],
        *,
        tool_call_id: str | None = None,
    ) -> "ModelDecision":
        """Construct a typed tool-call model decision with normalized arguments."""
        return cls(
            kind=ModelDecisionKind.TOOL_CALL,
            tool_name=tool_name,
            tool_arguments=normalize_tool_arguments(arguments),
            tool_call_id=tool_call_id,
        )

    def tool_arguments_as_mapping(self) -> dict[str, object]:
        """Return typed tool-call arguments as a mutable mapping."""
        return {} if self.tool_arguments is None else dict(self.tool_arguments)

    def __post_init__(self) -> None:
        if self.kind is ModelDecisionKind.TOOL_CALL:
            if self.tool_name is None:
                raise ValueError("tool_name is required for TOOL_CALL decisions.")
            if self.tool_arguments is None:
                raise ValueError("tool_arguments are required for TOOL_CALL decisions.")
            return

        if (
            self.tool_name is not None
            or self.tool_arguments is not None
            or self.tool_call_id is not None
        ):
            raise ValueError(
                "tool_name/tool_arguments/tool_call_id are only valid for TOOL_CALL decisions."
            )


class ModelDecisionInterpretationError(ValueError):
    """Raised when a model response cannot be interpreted into a runtime decision."""


def interpret_model_response(response: ModelResponse) -> ModelDecision:
    """Deterministically interpret a typed model response into a runtime decision."""
    if response.tool_call is not None:
        return ModelDecision.tool_call(
            tool_name=response.tool_call.tool_name,
            arguments=response.tool_call.arguments_as_mapping(),
            tool_call_id=response.tool_call.tool_call_id,
        )

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
