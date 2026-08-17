import os

import pytest

from context_engine.agent import AgentRuntime, AgentRuntimeExecutionOutcome
from context_engine.models import (
    ModelMessage,
    ModelRequest,
    ModelRole,
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
    runtime = AgentRuntime(model_gateway=gateway, tool_runtime=ToolRuntime(registry))

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
