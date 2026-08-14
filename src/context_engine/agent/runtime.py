"""Deterministic runtime orchestration for a single agent execution."""

from context_engine.agent.state import AgentExecutionState, AgentExecutionStatus
from context_engine.agent.transitions import transition_agent_state
from context_engine.models import ModelGateway


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
