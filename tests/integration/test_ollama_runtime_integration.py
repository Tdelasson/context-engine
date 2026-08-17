import os

import pytest

from context_engine.agent import AgentRuntime, AgentRuntimeExecutionOutcome
from context_engine.models import (
    ModelFinishReason,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ModelRole,
    ModelToolCall,
    ModelToolDefinition,
    OllamaModelGateway,
)
from context_engine.tools import (
    ToolInputField,
    ToolInputSchema,
    ToolInvocation,
    ToolRegistry,
    ToolRuntime,
)


def _skip_unless_ollama_enabled() -> None:
    if os.getenv("CONTEXT_ENGINE_RUN_OLLAMA_INTEGRATION") != "1":
        pytest.skip(
            "Set CONTEXT_ENGINE_RUN_OLLAMA_INTEGRATION=1 to run local Ollama integration tests."
        )


def _build_gateway() -> OllamaModelGateway:
    model_name = os.getenv("CONTEXT_ENGINE_OLLAMA_MODEL")
    if not model_name:
        pytest.skip("Set CONTEXT_ENGINE_OLLAMA_MODEL to a locally available Ollama model.")

    return OllamaModelGateway(
        base_url=os.getenv("CONTEXT_ENGINE_OLLAMA_BASE_URL", "http://localhost:11434"),
        model_name=model_name,
        timeout_seconds=float(os.getenv("CONTEXT_ENGINE_OLLAMA_TIMEOUT_SECONDS", "30")),
    )


class _AddTool:
    name = "add"
    description = "Add two integers."
    input_schema = ToolInputSchema(
        fields=(ToolInputField(name="a", value_type=int), ToolInputField(name="b", value_type=int))
    )

    def execute(self, invocation: ToolInvocation) -> dict[str, object]:
        arguments = invocation.arguments_as_mapping()
        a = arguments["a"]
        b = arguments["b"]
        if not isinstance(a, int) or not isinstance(b, int):
            raise RuntimeError("validated add tool received invalid argument types")
        return {"value": a + b}

class _MultTool:
    name = "multiply"
    description = "Multiply two floats."
    input_schema = ToolInputSchema(
        fields=(ToolInputField(name="a", value_type=int), ToolInputField(name="b", value_type=int))
    )

    def execute(self, invocation: ToolInvocation) -> dict[str, object]:
        arguments = invocation.arguments_as_mapping()
        a = arguments["a"]
        b = arguments["b"]
        if not isinstance(a, int) or not isinstance(b, int):
            raise RuntimeError("validated multiply tool received invalid argument types")
        return {"value": a * b}



class _RecordingGateway:
    def __init__(self, gateway: OllamaModelGateway) -> None:
        self._gateway = gateway
        self.requests: list[ModelRequest] = []

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        return self._gateway.generate(request)


def test_ollama_can_return_structured_tool_call_for_available_tool() -> None:
    _skip_unless_ollama_enabled()
    gateway = _build_gateway()
    model_name = os.getenv("CONTEXT_ENGINE_OLLAMA_MODEL")
    assert model_name is not None

    response = gateway.generate(
        ModelRequest(
            model_id=model_name,
            messages=(
                ModelMessage(
                    role=ModelRole.SYSTEM,
                    content=(
                        "Call the add tool with integers a=2 and b=3. "
                        "Do not answer directly in prose."
                    ),
                ),
                ModelMessage(role=ModelRole.USER, content="What is 2+3?"),
            ),
            tools=(
                ModelToolDefinition(
                    name="add",
                    description="Add two integers.",
                    input_schema={
                        "type": "object",
                        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                        "required": ["a", "b"],
                        "additionalProperties": False,
                    },
                ),
            ),
            temperature=0.0,
            max_output_tokens=64,
        )
    )

    assert response.tool_call is not None
    assert response.tool_call.tool_name == "add"
    assert response.tool_call.arguments_as_mapping() == {"a": 2, "b": 3}


def test_runtime_end_to_end_model_tool_call_then_respond_with_local_ollama() -> None:
    _skip_unless_ollama_enabled()
    gateway = _build_gateway()
    model_name = os.getenv("CONTEXT_ENGINE_OLLAMA_MODEL")
    assert model_name is not None

    registry = ToolRegistry()
    registry.register(_AddTool())
    recording_gateway = _RecordingGateway(gateway)
    runtime = AgentRuntime(model_gateway=recording_gateway, tool_runtime=ToolRuntime(registry))

    result = runtime.run(
        model_id=model_name,
        system_prompt=(
            "Use tools when available. "
            "For arithmetic, call the add tool first, then respond using the tool result."
        ),
        user_prompt="What is 2+3?",
        max_output_tokens=128,
        temperature=0.0,
        max_model_iterations=4,
    )

    assert result.outcome is AgentRuntimeExecutionOutcome.RESPONDED
    assert len(runtime.tool_results) == 1
    assert runtime.tool_results[0].invocation.tool_name == "add"
    assert runtime.tool_results[0].output_as_mapping() == {"value": 5}
    assert len(recording_gateway.requests) >= 2
    second_request_messages = recording_gateway.requests[1].messages
    assert [message.role for message in second_request_messages[:4]] == [
        ModelRole.SYSTEM,
        ModelRole.USER,
        ModelRole.ASSISTANT,
        ModelRole.TOOL,
    ]
    assert second_request_messages[2].tool_call == ModelToolCall.from_mapping(
        tool_name="add",
        arguments={"a": 2, "b": 3},
        tool_call_id="call-1",
    )
    assert second_request_messages[3].tool_result is not None
    assert second_request_messages[3].tool_result.output_as_mapping() == {"value": 5}


def test_runtime_can_handle_multiple_tool_calls_with_deterministic_model_sequence() -> None:
    registry = ToolRegistry()
    registry.register(_AddTool())
    registry.register(_MultTool())

    class _SequenceGateway:
        def __init__(self) -> None:
            self.requests: list[ModelRequest] = []
            self._responses = [
                ModelResponse(
                    model_id="deterministic-model",
                    output_text="",
                    finish_reason=ModelFinishReason.STOP,
                    tool_call=ModelToolCall.from_mapping(
                        tool_name="add",
                        arguments={"a": 2, "b": 3},
                    ),
                ),
                ModelResponse(
                    model_id="deterministic-model",
                    output_text="",
                    finish_reason=ModelFinishReason.STOP,
                    tool_call=ModelToolCall.from_mapping(
                        tool_name="multiply",
                        arguments={"a": 5, "b": 4},
                    ),
                ),
                ModelResponse(
                    model_id="deterministic-model",
                    output_text="20",
                    finish_reason=ModelFinishReason.STOP,
                ),
            ]

        def generate(self, request: ModelRequest) -> ModelResponse:
            self.requests.append(request)
            return self._responses.pop(0)

    gateway = _SequenceGateway()
    runtime = AgentRuntime(model_gateway=gateway, tool_runtime=ToolRuntime(registry))

    result = runtime.run(
        model_id="deterministic-model",
        system_prompt=(
            "You are an arithmetic agent. "
            "Use tools for arithmetic operations. "
            "Call add when needed, then call multiply using the add result, then answer."
        ),
        user_prompt="Calculate (2 + 3) * 4.",
        max_output_tokens=128,
        temperature=0.0,
        max_model_iterations=4,
    )

    assert result.outcome is AgentRuntimeExecutionOutcome.RESPONDED
    assert result.proposed_response == "20"
    assert len(runtime.tool_results) == 2
    assert runtime.tool_results[0].invocation.tool_name == "add"
    assert runtime.tool_results[0].output_as_mapping() == {"value": 5}
    assert runtime.tool_results[1].invocation.tool_name == "multiply"
    assert runtime.tool_results[1].output_as_mapping() == {"value": 20}
    assert len(gateway.requests) == 3
    