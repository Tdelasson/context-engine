from context_engine.agent import AgentExecutionState, AgentExecutionStatus


def test_agent_execution_status_values_are_explicit() -> None:
    assert tuple(AgentExecutionStatus) == (
        AgentExecutionStatus.START,
        AgentExecutionStatus.CONTEXT,
        AgentExecutionStatus.THINK,
        AgentExecutionStatus.ACTION_PROPOSED,
        AgentExecutionStatus.RUNTIME_VALIDATE,
        AgentExecutionStatus.TOOL_CALL,
        AgentExecutionStatus.RESPOND,
        AgentExecutionStatus.RETRY,
        AgentExecutionStatus.COMPLETED,
        AgentExecutionStatus.FAILED,
    )


def test_agent_execution_state_represents_status() -> None:
    state = AgentExecutionState(status=AgentExecutionStatus.THINK)
    assert state.status is AgentExecutionStatus.THINK
