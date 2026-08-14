import pytest

from context_engine.agent import (
    AgentExecutionState,
    AgentExecutionStatus,
    AgentRuntime,
    AgentRuntimeExecutionOutcome,
    AgentRuntimeModelInteractionError,
    InvalidAgentStateTransitionError,
    ModelDecision,
    ModelDecisionInterpretationError,
    ModelDecisionKind,
)
from context_engine.agent.transitions import (
    transition_agent_state as runtime_transition_agent_state,
)
from context_engine.models import (
    ModelFinishReason,
    ModelGatewayExecutionError,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ModelRole,
    normalize_messages,
)


class _RecordingStubModelGateway:
    def __init__(
        self,
        *,
        output_text: str = "stub",
        finish_reason: ModelFinishReason = ModelFinishReason.STOP,
    ) -> None:
        self.requests: list[ModelRequest] = []
        self.output_text = output_text
        self.finish_reason = finish_reason

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        return ModelResponse(
            model_id=request.model_id,
            output_text=self.output_text,
            finish_reason=self.finish_reason,
        )


class _FailingStubModelGateway:
    def generate(self, request: ModelRequest) -> ModelResponse:
        raise ModelGatewayExecutionError(f"generation failed for model {request.model_id}")


class _InvalidFinishReasonStubModelGateway:
    def generate(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            model_id=request.model_id,
            output_text="invalid",
            finish_reason="invalid",  # type: ignore[arg-type]
        )


class _SequenceStubModelGateway:
    def __init__(self, responses: list[ModelResponse]) -> None:
        self.requests: list[ModelRequest] = []
        self._responses = responses

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        response = self._responses.pop(0)
        return ModelResponse(
            model_id=request.model_id,
            output_text=response.output_text,
            finish_reason=response.finish_reason,
        )


def _capture_runtime_transitions(monkeypatch: pytest.MonkeyPatch) -> list[AgentExecutionStatus]:
    transitions: list[AgentExecutionStatus] = []
    original_transition = runtime_transition_agent_state

    def recording_transition(
        state: AgentExecutionState,
        to_status: AgentExecutionStatus,
    ) -> AgentExecutionState:
        transitions.append(to_status)
        return original_transition(state, to_status)

    monkeypatch.setattr("context_engine.agent.runtime.transition_agent_state", recording_transition)
    return transitions


def test_runtime_starts_in_start() -> None:
    runtime = AgentRuntime()

    assert runtime.state == AgentExecutionState(status=AgentExecutionStatus.START)


def test_runtime_can_depend_on_provider_independent_model_gateway() -> None:
    gateway = _RecordingStubModelGateway()
    runtime = AgentRuntime(model_gateway=gateway)

    assert runtime.model_gateway is gateway
    assert runtime.model_gateway is not None
    assert runtime.model_gateway.generate(
        ModelRequest(
            model_id="mock-model",
            messages=(ModelMessage(role=ModelRole.USER, content="hello"),),
        )
    ) == ModelResponse(
        model_id="mock-model",
        output_text="stub",
        finish_reason=ModelFinishReason.STOP,
    )


def test_runtime_propose_action_builds_typed_request_and_transitions() -> None:
    gateway = _RecordingStubModelGateway()
    runtime = AgentRuntime(model_gateway=gateway)
    runtime.transition_to(AgentExecutionStatus.CONTEXT)
    runtime.transition_to(AgentExecutionStatus.THINK)

    decision = runtime.propose_action(
        model_id="mock-model",
        user_prompt="hello",
        system_prompt="You are precise.",
        max_output_tokens=64,
        temperature=0.1,
    )

    assert gateway.requests == [
        ModelRequest(
            model_id="mock-model",
            messages=normalize_messages(
                [
                    ModelMessage(role=ModelRole.SYSTEM, content="You are precise."),
                    ModelMessage(role=ModelRole.USER, content="hello"),
                ]
            ),
            max_output_tokens=64,
            temperature=0.1,
        )
    ]
    assert decision == ModelDecision(
        kind=ModelDecisionKind.RESPOND,
        proposed_response="stub",
    )
    assert runtime.state == AgentExecutionState(status=AgentExecutionStatus.RESPOND)


@pytest.mark.parametrize(
    ("finish_reason", "expected_kind", "expected_status"),
    [
        (ModelFinishReason.STOP, ModelDecisionKind.RESPOND, AgentExecutionStatus.RESPOND),
        (ModelFinishReason.LENGTH, ModelDecisionKind.RETRY, AgentExecutionStatus.THINK),
        (ModelFinishReason.OTHER, ModelDecisionKind.FAIL, AgentExecutionStatus.FAILED),
    ],
)  # type: ignore[misc]
def test_runtime_propose_action_maps_decision_to_runtime_state(
    finish_reason: ModelFinishReason,
    expected_kind: ModelDecisionKind,
    expected_status: AgentExecutionStatus,
) -> None:
    gateway = _RecordingStubModelGateway(output_text="payload", finish_reason=finish_reason)
    runtime = AgentRuntime(model_gateway=gateway)
    runtime.transition_to(AgentExecutionStatus.CONTEXT)
    runtime.transition_to(AgentExecutionStatus.THINK)

    decision = runtime.propose_action(model_id="mock-model", user_prompt="hello")

    assert decision.kind == expected_kind
    assert decision.proposed_response == (
        "payload" if expected_kind is ModelDecisionKind.RESPOND else None
    )
    assert runtime.state == AgentExecutionState(status=expected_status)


def test_runtime_propose_action_translates_gateway_failure_into_runtime_boundary_error() -> None:
    runtime = AgentRuntime(model_gateway=_FailingStubModelGateway())
    runtime.transition_to(AgentExecutionStatus.CONTEXT)
    runtime.transition_to(AgentExecutionStatus.THINK)

    with pytest.raises(
        AgentRuntimeModelInteractionError,
        match="Model gateway failed during runtime model interaction",
    ):
        runtime.propose_action(model_id="mock-model", user_prompt="hello")

    assert runtime.state == AgentExecutionState(status=AgentExecutionStatus.THINK)


def test_runtime_propose_action_interpretation_error_keeps_runtime_in_think() -> None:
    runtime = AgentRuntime(model_gateway=_InvalidFinishReasonStubModelGateway())
    runtime.transition_to(AgentExecutionStatus.CONTEXT)
    runtime.transition_to(AgentExecutionStatus.THINK)

    with pytest.raises(ModelDecisionInterpretationError, match="Unsupported model finish reason"):
        runtime.propose_action(model_id="mock-model", user_prompt="hello")

    assert runtime.state == AgentExecutionState(status=AgentExecutionStatus.THINK)


@pytest.mark.parametrize(
    ("decision", "expected_status"),
    [
        (
            ModelDecision(kind=ModelDecisionKind.RESPOND, proposed_response="final"),
            AgentExecutionStatus.RESPOND,
        ),
        (ModelDecision(kind=ModelDecisionKind.RETRY), AgentExecutionStatus.THINK),
        (ModelDecision(kind=ModelDecisionKind.FAIL), AgentExecutionStatus.FAILED),
    ],
)  # type: ignore[misc]
def test_runtime_apply_model_decision_maps_to_valid_runtime_transitions(
    decision: ModelDecision,
    expected_status: AgentExecutionStatus,
) -> None:
    runtime = AgentRuntime()
    runtime.transition_to(AgentExecutionStatus.CONTEXT)
    runtime.transition_to(AgentExecutionStatus.THINK)
    runtime.transition_to(AgentExecutionStatus.ACTION_PROPOSED)

    next_state = runtime.apply_model_decision(decision)

    assert next_state == AgentExecutionState(status=expected_status)
    assert runtime.state == AgentExecutionState(status=expected_status)


def test_runtime_propose_action_invalid_state_raises_and_does_not_call_gateway() -> None:
    gateway = _RecordingStubModelGateway()
    runtime = AgentRuntime(model_gateway=gateway)

    with pytest.raises(
        InvalidAgentStateTransitionError,
        match=f"{AgentExecutionStatus.START.value} -> {AgentExecutionStatus.ACTION_PROPOSED.value}",
    ):
        runtime.propose_action(model_id="mock-model", user_prompt="hello")

    assert gateway.requests == []


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


def test_runtime_can_reach_completed() -> None:
    runtime = AgentRuntime()
    runtime.transition_to(AgentExecutionStatus.CONTEXT)
    runtime.transition_to(AgentExecutionStatus.THINK)
    runtime.transition_to(AgentExecutionStatus.ACTION_PROPOSED)
    runtime.transition_to(AgentExecutionStatus.RUNTIME_VALIDATE)
    runtime.transition_to(AgentExecutionStatus.RESPOND)
    final_state = runtime.complete()

    assert final_state == AgentExecutionState(status=AgentExecutionStatus.COMPLETED)
    assert runtime.is_terminal is True


def test_runtime_can_reach_failed() -> None:
    runtime = AgentRuntime()
    runtime.transition_to(AgentExecutionStatus.CONTEXT)
    runtime.transition_to(AgentExecutionStatus.THINK)
    runtime.transition_to(AgentExecutionStatus.ACTION_PROPOSED)
    runtime.transition_to(AgentExecutionStatus.RUNTIME_VALIDATE)
    final_state = runtime.fail()

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

    with pytest.raises(
        InvalidAgentStateTransitionError,
        match=f"{AgentExecutionStatus.START.value} -> {AgentExecutionStatus.THINK.value}",
    ):
        runtime.transition_to(AgentExecutionStatus.THINK)


def test_runtime_run_single_pass_reaches_completed_and_returns_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transitions = _capture_runtime_transitions(monkeypatch)
    gateway = _SequenceStubModelGateway(
        responses=[
            ModelResponse(
                model_id="mock-model",
                output_text="final answer",
                finish_reason=ModelFinishReason.STOP,
            )
        ]
    )
    runtime = AgentRuntime(model_gateway=gateway)

    result = runtime.run(model_id="mock-model", user_prompt="hello")

    assert result.outcome is AgentRuntimeExecutionOutcome.RESPONDED
    assert result.proposed_response == "final answer"
    assert result.model_iterations == 1
    assert result.terminal_state == AgentExecutionState(status=AgentExecutionStatus.COMPLETED)
    assert runtime.state == AgentExecutionState(status=AgentExecutionStatus.COMPLETED)
    assert len(gateway.requests) == 1
    assert transitions == [
        AgentExecutionStatus.CONTEXT,
        AgentExecutionStatus.THINK,
        AgentExecutionStatus.ACTION_PROPOSED,
        AgentExecutionStatus.RUNTIME_VALIDATE,
        AgentExecutionStatus.RESPOND,
        AgentExecutionStatus.COMPLETED,
    ]


def test_runtime_run_retry_then_respond_retries_deterministically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transitions = _capture_runtime_transitions(monkeypatch)
    gateway = _SequenceStubModelGateway(
        responses=[
            ModelResponse(
                model_id="mock-model",
                output_text="partial",
                finish_reason=ModelFinishReason.LENGTH,
            ),
            ModelResponse(
                model_id="mock-model",
                output_text="final answer",
                finish_reason=ModelFinishReason.STOP,
            ),
        ]
    )
    runtime = AgentRuntime(model_gateway=gateway)

    result = runtime.run(model_id="mock-model", user_prompt="hello", max_model_iterations=3)

    assert result.outcome is AgentRuntimeExecutionOutcome.RESPONDED
    assert result.proposed_response == "final answer"
    assert result.model_iterations == 2
    assert result.terminal_state == AgentExecutionState(status=AgentExecutionStatus.COMPLETED)
    assert len(gateway.requests) == 2
    assert transitions == [
        AgentExecutionStatus.CONTEXT,
        AgentExecutionStatus.THINK,
        AgentExecutionStatus.ACTION_PROPOSED,
        AgentExecutionStatus.RUNTIME_VALIDATE,
        AgentExecutionStatus.THINK,
        AgentExecutionStatus.ACTION_PROPOSED,
        AgentExecutionStatus.RUNTIME_VALIDATE,
        AgentExecutionStatus.RESPOND,
        AgentExecutionStatus.COMPLETED,
    ]


def test_runtime_run_fail_decision_reaches_failed_terminal_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transitions = _capture_runtime_transitions(monkeypatch)
    gateway = _SequenceStubModelGateway(
        responses=[
            ModelResponse(
                model_id="mock-model",
                output_text="cannot continue",
                finish_reason=ModelFinishReason.OTHER,
            )
        ]
    )
    runtime = AgentRuntime(model_gateway=gateway)

    result = runtime.run(model_id="mock-model", user_prompt="hello")

    assert result.outcome is AgentRuntimeExecutionOutcome.FAILED
    assert result.proposed_response is None
    assert result.model_iterations == 1
    assert result.terminal_state == AgentExecutionState(status=AgentExecutionStatus.FAILED)
    assert transitions == [
        AgentExecutionStatus.CONTEXT,
        AgentExecutionStatus.THINK,
        AgentExecutionStatus.ACTION_PROPOSED,
        AgentExecutionStatus.RUNTIME_VALIDATE,
        AgentExecutionStatus.FAILED,
    ]


def test_runtime_run_step_limit_fails_deterministically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transitions = _capture_runtime_transitions(monkeypatch)
    gateway = _SequenceStubModelGateway(
        responses=[
            ModelResponse(
                model_id="mock-model",
                output_text="partial-1",
                finish_reason=ModelFinishReason.LENGTH,
            ),
            ModelResponse(
                model_id="mock-model",
                output_text="partial-2",
                finish_reason=ModelFinishReason.LENGTH,
            ),
        ]
    )
    runtime = AgentRuntime(model_gateway=gateway)

    result = runtime.run(model_id="mock-model", user_prompt="hello", max_model_iterations=2)

    assert result.outcome is AgentRuntimeExecutionOutcome.LIMIT_REACHED
    assert result.error_message is not None
    assert "exceeded max model iterations" in result.error_message
    assert result.model_iterations == 2
    assert result.terminal_state == AgentExecutionState(status=AgentExecutionStatus.FAILED)
    assert len(gateway.requests) == 2
    assert transitions == [
        AgentExecutionStatus.CONTEXT,
        AgentExecutionStatus.THINK,
        AgentExecutionStatus.ACTION_PROPOSED,
        AgentExecutionStatus.RUNTIME_VALIDATE,
        AgentExecutionStatus.THINK,
        AgentExecutionStatus.ACTION_PROPOSED,
        AgentExecutionStatus.RUNTIME_VALIDATE,
        AgentExecutionStatus.THINK,
        AgentExecutionStatus.ACTION_PROPOSED,
        AgentExecutionStatus.RUNTIME_VALIDATE,
        AgentExecutionStatus.FAILED,
    ]


def test_runtime_run_gateway_failure_returns_failed_result_and_terminal_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transitions = _capture_runtime_transitions(monkeypatch)
    runtime = AgentRuntime(model_gateway=_FailingStubModelGateway())

    result = runtime.run(model_id="mock-model", user_prompt="hello")

    assert result.outcome is AgentRuntimeExecutionOutcome.FAILED
    assert result.error_message is not None
    assert "Model gateway failed during runtime model interaction" in result.error_message
    assert result.model_iterations == 1
    assert result.terminal_state == AgentExecutionState(status=AgentExecutionStatus.FAILED)
    assert transitions == [
        AgentExecutionStatus.CONTEXT,
        AgentExecutionStatus.THINK,
        AgentExecutionStatus.ACTION_PROPOSED,
        AgentExecutionStatus.ACTION_PROPOSED,
        AgentExecutionStatus.RUNTIME_VALIDATE,
        AgentExecutionStatus.FAILED,
    ]


def test_runtime_run_rejects_non_positive_max_model_iterations() -> None:
    runtime = AgentRuntime(model_gateway=_RecordingStubModelGateway())

    with pytest.raises(ValueError, match="max_model_iterations must be >= 1"):
        runtime.run(model_id="mock-model", user_prompt="hello", max_model_iterations=0)
