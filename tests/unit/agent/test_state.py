from dataclasses import FrozenInstanceError

import pytest

from context_engine.agent import (
    ALLOWED_TRANSITIONS,
    AgentExecutionState,
    AgentExecutionStatus,
    InvalidAgentStateTransitionError,
    can_transition,
    transition_agent_state,
)


def test_agent_execution_status_values_are_explicit() -> None:
    assert tuple(AgentExecutionStatus) == (
        AgentExecutionStatus.START,
        AgentExecutionStatus.CONTEXT,
        AgentExecutionStatus.THINK,
        AgentExecutionStatus.ACTION_PROPOSED,
        AgentExecutionStatus.RUNTIME_VALIDATE,
        AgentExecutionStatus.TOOL_CALL,
        AgentExecutionStatus.RESPOND,
        AgentExecutionStatus.COMPLETED,
        AgentExecutionStatus.FAILED,
    )


def test_agent_execution_state_represents_status() -> None:
    state = AgentExecutionState(status=AgentExecutionStatus.THINK)
    assert state.status is AgentExecutionStatus.THINK


def test_agent_execution_state_is_immutable() -> None:
    state = AgentExecutionState(status=AgentExecutionStatus.START)
    with pytest.raises(FrozenInstanceError):
        state.status = AgentExecutionStatus.THINK  # type: ignore[misc]


def test_allowed_transitions_graph_is_explicit_and_complete() -> None:
    assert ALLOWED_TRANSITIONS == {
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


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (from_status, to_status)
        for from_status, to_statuses in ALLOWED_TRANSITIONS.items()
        for to_status in to_statuses
    ],
)  # type: ignore[misc]
def test_runtime_allows_every_explicit_transition(
    from_status: AgentExecutionStatus, to_status: AgentExecutionStatus
) -> None:
    assert can_transition(from_status, to_status) is True


def test_transition_agent_state_returns_new_state_for_valid_transition() -> None:
    state = AgentExecutionState(status=AgentExecutionStatus.START)

    transitioned = transition_agent_state(state, AgentExecutionStatus.CONTEXT)

    assert transitioned is not state
    assert transitioned == AgentExecutionState(status=AgentExecutionStatus.CONTEXT)
    assert state == AgentExecutionState(status=AgentExecutionStatus.START)


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (AgentExecutionStatus.START, AgentExecutionStatus.TOOL_CALL),
        (AgentExecutionStatus.THINK, AgentExecutionStatus.COMPLETED),
        (AgentExecutionStatus.ACTION_PROPOSED, AgentExecutionStatus.THINK),
    ],
)  # type: ignore[misc]
def test_runtime_rejects_invalid_non_terminal_transitions(
    from_status: AgentExecutionStatus, to_status: AgentExecutionStatus
) -> None:
    state = AgentExecutionState(status=from_status)

    assert can_transition(from_status, to_status) is False
    with pytest.raises(
        InvalidAgentStateTransitionError,
        match=f"{from_status.value} -> {to_status.value}",
    ):
        transition_agent_state(state, to_status)


@pytest.mark.parametrize(
    "terminal_status",
    [AgentExecutionStatus.COMPLETED, AgentExecutionStatus.FAILED],
)  # type: ignore[misc]
def test_runtime_rejects_all_transitions_from_terminal_states(
    terminal_status: AgentExecutionStatus,
) -> None:
    state = AgentExecutionState(status=terminal_status)

    for next_status in AgentExecutionStatus:
        assert can_transition(terminal_status, next_status) is False
        with pytest.raises(
            InvalidAgentStateTransitionError,
            match=f"{terminal_status.value} -> {next_status.value}",
        ):
            transition_agent_state(state, next_status)
