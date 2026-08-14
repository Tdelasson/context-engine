"""Deterministic runtime orchestration for a single agent execution."""

from context_engine.agent.decision import ModelDecision, interpret_model_response
from context_engine.agent.state import AgentExecutionState, AgentExecutionStatus
from context_engine.agent.transitions import transition_agent_state
from context_engine.models import (
    ModelGateway,
    ModelGatewayError,
    ModelMessage,
    ModelRequest,
    ModelRole,
    normalize_messages,
)


class AgentRuntimeModelInteractionError(RuntimeError):
    """Raised when runtime-model interaction fails at the runtime boundary."""


class AgentRuntime:
    """Owns execution state and applies validated transitions deterministically."""

    def __init__(
        self,
        initial_state: AgentExecutionState | None = None,
        model_gateway: ModelGateway | None = None,
    ) -> None:
        self._state = initial_state or AgentExecutionState(status=AgentExecutionStatus.START)
        self._model_gateway = model_gateway

    @property
    def state(self) -> AgentExecutionState:
        """Return the current immutable execution state."""
        return self._state

    @property
    def model_gateway(self) -> ModelGateway | None:
        """Return the runtime's provider-independent model gateway dependency."""
        return self._model_gateway

    @property
    def is_terminal(self) -> bool:
        """Return whether the execution reached a terminal state."""
        return self._state.status in {
            AgentExecutionStatus.COMPLETED,
            AgentExecutionStatus.FAILED,
        }

    def transition_to(self, status: AgentExecutionStatus) -> AgentExecutionState:
        """Advance execution by applying one validated transition."""
        self._state = transition_agent_state(self._state, status)
        return self._state

    def complete(self) -> AgentExecutionState:
        """Attempt to terminate execution successfully."""
        return self.transition_to(AgentExecutionStatus.COMPLETED)

    def fail(self) -> AgentExecutionState:
        """Attempt to terminate execution as failed."""
        return self.transition_to(AgentExecutionStatus.FAILED)

    def propose_action(
        self,
        *,
        model_id: str,
        user_prompt: str,
        system_prompt: str | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
    ) -> ModelDecision:
        """Generate and interpret a model decision for THINK -> ACTION_PROPOSED."""
        if self._model_gateway is None:
            raise AgentRuntimeModelInteractionError(
                "Model gateway is required for runtime model interaction."
            )

        next_state = transition_agent_state(self._state, AgentExecutionStatus.ACTION_PROPOSED)

        request = self._build_model_request(
            model_id=model_id,
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )

        try:
            response = self._model_gateway.generate(request)
        except ModelGatewayError as exc:
            raise AgentRuntimeModelInteractionError(
                "Model gateway failed during runtime model interaction."
            ) from exc

        decision = interpret_model_response(response)
        self._state = next_state
        return decision

    def _build_model_request(
        self,
        *,
        model_id: str,
        user_prompt: str,
        system_prompt: str | None,
        max_output_tokens: int | None,
        temperature: float | None,
    ) -> ModelRequest:
        messages: list[ModelMessage] = []

        if system_prompt is not None:
            messages.append(ModelMessage(role=ModelRole.SYSTEM, content=system_prompt))

        messages.append(ModelMessage(role=ModelRole.USER, content=user_prompt))

        return ModelRequest(
            model_id=model_id,
            messages=normalize_messages(messages),
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
