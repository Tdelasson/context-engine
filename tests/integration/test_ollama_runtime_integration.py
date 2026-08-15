import os

import pytest

from context_engine.agent import AgentRuntime, AgentRuntimeExecutionOutcome
from context_engine.models import OllamaModelGateway


@pytest.mark.skipif(
    os.getenv("CONTEXT_ENGINE_RUN_OLLAMA_INTEGRATION") != "1",
    reason="Set CONTEXT_ENGINE_RUN_OLLAMA_INTEGRATION=1 to run local Ollama integration tests.",
)
def test_agent_runtime_can_run_against_local_ollama() -> None:
    model_name = os.getenv("CONTEXT_ENGINE_OLLAMA_MODEL")
    if not model_name:
        pytest.skip("Set CONTEXT_ENGINE_OLLAMA_MODEL to a locally available Ollama model.")

    gateway = OllamaModelGateway(
        base_url=os.getenv("CONTEXT_ENGINE_OLLAMA_BASE_URL", "http://localhost:11434"),
        model_name=model_name,
        timeout_seconds=float(os.getenv("CONTEXT_ENGINE_OLLAMA_TIMEOUT_SECONDS", "30")),
    )
    runtime = AgentRuntime(model_gateway=gateway)

    result = runtime.run(
        model_id=model_name,
        system_prompt="You are concise. Respond with exactly one short sentence.",
        user_prompt="Say hello.",
        max_output_tokens=64,
        temperature=0.0,
        max_model_iterations=2,
    )

    assert result.outcome is AgentRuntimeExecutionOutcome.RESPONDED
    assert result.proposed_response is not None
    assert result.proposed_response.strip() != ""
