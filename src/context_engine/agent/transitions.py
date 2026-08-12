"""Deterministic runtime-owned transitions for agent execution state."""

from collections.abc import Mapping, Set
from typing import Final

from context_engine.agent.state import AgentExecutionState, AgentExecutionStatus

ALLOWED_TRANSITIONS: Final[Mapping[AgentExecutionStatus, Set[AgentExecutionStatus]]] = {
    AgentExecutionStatus.START: frozenset({AgentExecutionStatus.CONTEXT}),
    AgentExecutionStatus.CONTEXT: frozenset({AgentExecutionStatus.THINK}),
    AgentExecutionStatus.THINK: frozenset({AgentExecutionStatus.ACTION_PROPOSED}),
    AgentExecutionStatus.ACTION_PROPOSED: frozenset({AgentExecutionStatus.RUNTIME_VALIDATE}),
    AgentExecutionStatus.RUNTIME_VALIDATE: frozenset(
        {
            AgentExecutionStatus.TOOL_CALL,
            AgentExecutionStatus.RESPOND,
            AgentExecutionStatus.THINK,
            AgentExecutionStatus.FAILED,
        }
    ),
    AgentExecutionStatus.TOOL_CALL: frozenset({AgentExecutionStatus.THINK}),
    AgentExecutionStatus.RESPOND: frozenset({AgentExecutionStatus.COMPLETED}),
    AgentExecutionStatus.COMPLETED: frozenset(),
    AgentExecutionStatus.FAILED: frozenset(),
}


class InvalidAgentStateTransitionError(ValueError):
    """Raised when the runtime attempts an invalid agent state transition."""

    def __init__(
        self, *, from_status: AgentExecutionStatus, to_status: AgentExecutionStatus
    ) -> None:
        super().__init__(
            f"Invalid agent state transition: {from_status.value} -> {to_status.value}"
        )


def can_transition(from_status: AgentExecutionStatus, to_status: AgentExecutionStatus) -> bool:
    """Return whether a transition between statuses is valid."""
    return to_status in ALLOWED_TRANSITIONS[from_status]


def transition_agent_state(
    state: AgentExecutionState, to_status: AgentExecutionStatus
) -> AgentExecutionState:
    """Return a new immutable state after validating an allowed transition."""
    if not can_transition(state.status, to_status):
        raise InvalidAgentStateTransitionError(from_status=state.status, to_status=to_status)
    return AgentExecutionState(status=to_status)
