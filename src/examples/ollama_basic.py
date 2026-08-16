import os

from context_engine.agent.runtime import AgentRuntime
from context_engine.models.ollama import OllamaModelGateway


def main() -> None:
    gateway = OllamaModelGateway(
        base_url="http://localhost:11434",
        model_name="llama3.2",
        timeout_seconds=float(os.getenv("CONTEXT_ENGINE_OLLAMA_TIMEOUT_SECONDS", "30")),
    )

    runtime = AgentRuntime(model_gateway=gateway)

    result = runtime.run(
        model_id="llama3.2",
        system_prompt="You are a helpful software engineering assistant.",
        user_prompt="Explain dependency injection in three concise bullet points.",
        max_output_tokens=500,
        temperature=0.0,
    )

    print(f"Outcome: {result.outcome}")
    print(f"Terminal state: {result.terminal_state.status}")
    print(f"Model iterations: {result.model_iterations}")
    print()
    print("Response:")
    print(result.proposed_response)


if __name__ == "__main__":
    main()
