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


def test_model_decision_tool_call_requires_tool_name_and_arguments() -> None:
    with pytest.raises(ValueError, match="tool_name is required"):
        ModelDecision(kind=ModelDecisionKind.TOOL_CALL, tool_arguments=(("a", 1),))

    with pytest.raises(ValueError, match="tool_arguments are required"):
        ModelDecision(kind=ModelDecisionKind.TOOL_CALL, tool_name="add")


def test_model_decision_tool_call_factory_normalizes_arguments() -> None:
    decision = ModelDecision.tool_call(tool_name="add", arguments={"b": 3, "a": 2})

    assert decision.kind is ModelDecisionKind.TOOL_CALL
    assert decision.tool_name == "add"
    assert decision.tool_arguments == (("a", 2), ("b", 3))
    assert decision.tool_arguments_as_mapping() == {"a": 2, "b": 3}


def test_model_decision_non_tool_call_rejects_tool_fields() -> None:
    with pytest.raises(ValueError, match="only valid for TOOL_CALL"):
        ModelDecision(
            kind=ModelDecisionKind.RESPOND,
            proposed_response="done",
            tool_name="add",
            tool_arguments=(("a", 2), ("b", 3)),
        )
