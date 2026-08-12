import pytest

from context_engine.agent import (
    AgentExecutionState,
    AgentExecutionStatus,
    AgentRuntime,
    InvalidAgentStateTransitionError,
)


class MappingController:
    def __init__(self, mapping: dict[AgentExecutionStatus, AgentExecutionStatus]) -> None:
        self._mapping = mapping

    def next_status(self, state: AgentExecutionState) -> AgentExecutionStatus:
        return self._mapping[state.status]


def test_runtime_starts_in_start() -> None:
    runtime = AgentRuntime()

    assert runtime.state == AgentExecutionState(status=AgentExecutionStatus.START)


def test_runtime_progresses_through_lifecycle_to_completed() -> None:
    runtime = AgentRuntime()

    runtime.transition_to(AgentExecutionStatus.CONTEXT)
    runtime.transition_to(AgentExecutionStatus.THINK)
    runtime.transition_to(AgentExecutionStatus.ACTION_PROPOSED)
    runtime.transition_to(AgentExecutionStatus.RUNTIME_VALIDATE)
    runtime.transition_to(AgentExecutionStatus.RESPOND)
    runtime.complete()

    assert runtime.state == AgentExecutionState(status=AgentExecutionStatus.COMPLETED)
    assert runtime.is_terminal is True


def test_runtime_transitions_replace_immutable_state_object() -> None:
    runtime = AgentRuntime()
    original = runtime.state

    runtime.transition_to(AgentExecutionStatus.CONTEXT)

    assert runtime.state is not original
    assert original == AgentExecutionState(status=AgentExecutionStatus.START)
    assert runtime.state == AgentExecutionState(status=AgentExecutionStatus.CONTEXT)


def test_runtime_run_reaches_completed() -> None:
    runtime = AgentRuntime()
    controller = MappingController(
        {
            AgentExecutionStatus.START: AgentExecutionStatus.CONTEXT,
            AgentExecutionStatus.CONTEXT: AgentExecutionStatus.THINK,
            AgentExecutionStatus.THINK: AgentExecutionStatus.ACTION_PROPOSED,
            AgentExecutionStatus.ACTION_PROPOSED: AgentExecutionStatus.RUNTIME_VALIDATE,
            AgentExecutionStatus.RUNTIME_VALIDATE: AgentExecutionStatus.RESPOND,
            AgentExecutionStatus.RESPOND: AgentExecutionStatus.COMPLETED,
        }
    )

    final_state = runtime.run(controller)

    assert final_state == AgentExecutionState(status=AgentExecutionStatus.COMPLETED)
    assert runtime.is_terminal is True


def test_runtime_run_reaches_failed() -> None:
    runtime = AgentRuntime()
    controller = MappingController(
        {
            AgentExecutionStatus.START: AgentExecutionStatus.CONTEXT,
            AgentExecutionStatus.CONTEXT: AgentExecutionStatus.THINK,
            AgentExecutionStatus.THINK: AgentExecutionStatus.ACTION_PROPOSED,
            AgentExecutionStatus.ACTION_PROPOSED: AgentExecutionStatus.RUNTIME_VALIDATE,
            AgentExecutionStatus.RUNTIME_VALIDATE: AgentExecutionStatus.FAILED,
        }
    )

    final_state = runtime.run(controller)

    assert final_state == AgentExecutionState(status=AgentExecutionStatus.FAILED)
    assert runtime.is_terminal is True


@pytest.mark.parametrize(
    "terminal_status",
    [AgentExecutionStatus.COMPLETED, AgentExecutionStatus.FAILED],
)  # type: ignore[misc]
def test_runtime_cannot_advance_terminal_states(
    terminal_status: AgentExecutionStatus,
) -> None:
    runtime = AgentRuntime(initial_state=AgentExecutionState(status=terminal_status))

    with pytest.raises(
        InvalidAgentStateTransitionError,
        match=f"{terminal_status.value} -> {AgentExecutionStatus.START.value}",
    ):
        runtime.transition_to(AgentExecutionStatus.START)


def test_runtime_invalid_transition_is_rejected_by_transition_system() -> None:
    runtime = AgentRuntime()
    controller = MappingController({AgentExecutionStatus.START: AgentExecutionStatus.THINK})

    with pytest.raises(
        InvalidAgentStateTransitionError,
        match=f"{AgentExecutionStatus.START.value} -> {AgentExecutionStatus.THINK.value}",
    ):
        runtime.run(controller)
