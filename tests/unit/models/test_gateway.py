import pytest

from context_engine.models.gateway import (
    MockModelGateway,
    ModelGateway,
    ModelGatewayError,
    ModelRequest,
    ModelResponse,
)


def test_mock_gateway_satisfies_model_gateway_contract() -> None:
    gateway = MockModelGateway()

    assert isinstance(gateway, ModelGateway)


def test_mock_gateway_returns_typed_response() -> None:
    gateway = MockModelGateway()
    request = ModelRequest(prompt="Hello", model="test-model")

    response = gateway.generate(request)

    assert isinstance(response, ModelResponse)
    assert response.text == "Hello"
    assert response.model == "test-model"


def test_mock_gateway_can_return_configured_response() -> None:
    expected = ModelResponse(text="response", model="mock")
    gateway = MockModelGateway(response=expected)

    response = gateway.generate(ModelRequest(prompt="ignored", model="requested"))

    assert response == expected


def test_empty_prompt_raises_gateway_error() -> None:
    gateway = MockModelGateway()

    with pytest.raises(ModelGatewayError, match="prompt must not be empty"):
        gateway.generate(ModelRequest(prompt="", model="test-model"))
