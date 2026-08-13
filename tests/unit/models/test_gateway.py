import pytest

from context_engine.models import (
    ModelFinishReason,
    ModelGateway,
    ModelGatewayExecutionError,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ModelRole,
    ModelUsage,
    normalize_messages,
)


class MockModelGateway:
    def generate(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            model_id=request.model_id,
            output_text="ready",
            finish_reason=ModelFinishReason.STOP,
            usage=ModelUsage(input_tokens=4, output_tokens=1),
        )


class FailingMockModelGateway:
    def generate(self, request: ModelRequest) -> ModelResponse:
        raise ModelGatewayExecutionError(f"generation failed for model {request.model_id}")


def test_mock_gateway_satisfies_provider_independent_protocol() -> None:
    gateway = MockModelGateway()
    request = ModelRequest(
        model_id="mock-model",
        messages=(ModelMessage(role=ModelRole.USER, content="hello"),),
    )

    assert isinstance(gateway, ModelGateway)
    response = gateway.generate(request)

    assert response == ModelResponse(
        model_id="mock-model",
        output_text="ready",
        finish_reason=ModelFinishReason.STOP,
        usage=ModelUsage(input_tokens=4, output_tokens=1),
    )


def test_model_request_and_response_are_typed_and_immutable() -> None:
    messages = normalize_messages(
        [
            ModelMessage(role=ModelRole.SYSTEM, content="You are precise."),
            ModelMessage(role=ModelRole.USER, content="Summarize."),
        ]
    )

    request = ModelRequest(model_id="mock-model", messages=messages, max_output_tokens=64)

    assert request.messages == messages
    assert isinstance(request.messages, tuple)


def test_gateway_failure_uses_explicit_error_boundary() -> None:
    gateway = FailingMockModelGateway()
    request = ModelRequest(
        model_id="mock-model",
        messages=(ModelMessage(role=ModelRole.USER, content="fail"),),
    )

    with pytest.raises(ModelGatewayExecutionError, match="generation failed"):
        gateway.generate(request)
