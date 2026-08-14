import pytest

from context_engine.agent import (
    ModelDecision,
    ModelDecisionInterpretationError,
    ModelDecisionKind,
    interpret_model_response,
)
from context_engine.models import ModelFinishReason, ModelResponse


def test_interpret_model_response_stop_maps_to_respond_decision() -> None:
    response = ModelResponse(
        model_id="mock-model",
        output_text="final answer",
        finish_reason=ModelFinishReason.STOP,
    )

    assert interpret_model_response(response) == ModelDecision(
        kind=ModelDecisionKind.RESPOND,
        proposed_response="final answer",
    )


def test_interpret_model_response_length_maps_to_retry_decision() -> None:
    response = ModelResponse(
        model_id="mock-model",
        output_text="partial",
        finish_reason=ModelFinishReason.LENGTH,
    )

    assert interpret_model_response(response) == ModelDecision(kind=ModelDecisionKind.RETRY)


def test_interpret_model_response_other_maps_to_fail_decision() -> None:
    response = ModelResponse(
        model_id="mock-model",
        output_text="",
        finish_reason=ModelFinishReason.OTHER,
    )

    assert interpret_model_response(response) == ModelDecision(kind=ModelDecisionKind.FAIL)


def test_interpret_model_response_is_deterministic_for_identical_input() -> None:
    response = ModelResponse(
        model_id="mock-model",
        output_text="same",
        finish_reason=ModelFinishReason.STOP,
    )

    assert interpret_model_response(response) == interpret_model_response(response)


def test_interpret_model_response_rejects_unsupported_finish_reason() -> None:
    response = ModelResponse(
        model_id="mock-model",
        output_text="same",
        finish_reason="unexpected",  # type: ignore[arg-type]
    )

    with pytest.raises(
        ModelDecisionInterpretationError,
        match="Unsupported model finish reason",
    ):
        interpret_model_response(response)
