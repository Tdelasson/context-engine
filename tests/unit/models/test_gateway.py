import pytest

from context_engine.models import (
    ModelFinishReason,
    ModelGateway,
    ModelGatewayExecutionError,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ModelRole,
    ModelToolCall,
    ModelToolDefinition,
    ModelToolResult,
    ModelToolResultStatus,
    ModelUsage,
    normalize_messages,
    normalize_model_tools,
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


def test_model_request_can_include_provider_independent_tools() -> None:
    tools = normalize_model_tools(
        [
            ModelToolDefinition(
                name="add",
                description="Add two integers.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer"},
                        "b": {"type": "integer"},
                    },
                    "required": ["a", "b"],
                    "additionalProperties": False,
                },
            )
        ]
    )

    request = ModelRequest(
        model_id="mock-model",
        messages=(ModelMessage(role=ModelRole.USER, content="What is 2+3?"),),
        tools=tools,
    )

    assert request.tools == tools
    assert isinstance(request.tools, tuple)


def test_model_response_can_represent_provider_independent_tool_call() -> None:
    response = ModelResponse(
        model_id="mock-model",
        output_text="",
        finish_reason=ModelFinishReason.STOP,
        tool_call=ModelToolCall.from_mapping(tool_name="add", arguments={"b": 3, "a": 2}),
    )

    assert response.tool_call is not None
    assert response.tool_call.tool_name == "add"
    assert response.tool_call.arguments_as_mapping() == {"a": 2, "b": 3}


def test_model_message_can_serialize_assistant_tool_call() -> None:
    message = ModelMessage(
        role=ModelRole.ASSISTANT,
        tool_call=ModelToolCall.from_mapping(
            tool_name="add",
            arguments={"b": 3, "a": 2},
            tool_call_id="call-1",
        ),
    )

    assert message.tool_call is not None
    assert message.tool_call.tool_name == "add"
    assert message.tool_call.tool_call_id == "call-1"
    assert message.tool_call.arguments_as_mapping() == {"a": 2, "b": 3}


def test_model_message_can_serialize_tool_result_message() -> None:
    message = ModelMessage(
        role=ModelRole.TOOL,
        tool_result=ModelToolResult.success(
            tool_name="add",
            output={"value": 5},
            tool_call_id="call-1",
        ),
    )

    assert message.tool_result is not None
    assert message.tool_result.status is ModelToolResultStatus.SUCCESS
    assert message.tool_result.tool_name == "add"
    assert message.tool_result.tool_call_id == "call-1"
    assert message.tool_result.output_as_mapping() == {"value": 5}


def test_gateway_failure_uses_explicit_error_boundary() -> None:
    gateway = FailingMockModelGateway()
    request = ModelRequest(
        model_id="mock-model",
        messages=(ModelMessage(role=ModelRole.USER, content="fail"),),
    )

    with pytest.raises(ModelGatewayExecutionError, match="generation failed"):
        gateway.generate(request)
