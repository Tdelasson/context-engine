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
    ModelToolCall,
    ModelToolResultStatus,
    normalize_messages,
)
from context_engine.tools import (
    ToolInputField,
    ToolInputSchema,
    ToolInvocation,
    ToolRegistry,
    ToolResultStatus,
    ToolRuntime,
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
            tool_call=response.tool_call,
        )


class _AddTool:
    name = "add"
    description = "Add two integers."
    input_schema = ToolInputSchema(
        fields=(ToolInputField(name="a", value_type=int), ToolInputField(name="b", value_type=int))
    )

    def __init__(self) -> None:
        self.was_executed = False

    def execute(self, invocation: ToolInvocation) -> dict[str, object]:
        self.was_executed = True
        arguments = invocation.arguments_as_mapping()
        a = arguments["a"]
        b = arguments["b"]
        if not isinstance(a, int) or not isinstance(b, int):
            raise RuntimeError("validated add tool received invalid argument types")
        return {"value": a + b}


class _FailingTool:
    name = "explode"
    description = "Raise an execution error."
    input_schema = ToolInputSchema(fields=(ToolInputField(name="message", value_type=str),))

    def execute(self, invocation: ToolInvocation) -> dict[str, object]:
        message = invocation.arguments_as_mapping()["message"]
        raise RuntimeError(f"failed: {message}")


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


def _patch_interpret_model_decisions(
    monkeypatch: pytest.MonkeyPatch,
    decisions: list[ModelDecision],
) -> None:
    queue = list(decisions)

    def decision_sequence(_: ModelResponse) -> ModelDecision:
        if not queue:
            raise AssertionError("No model decision remaining in deterministic sequence")
        return queue.pop(0)

    monkeypatch.setattr(
        "context_engine.agent.runtime.interpret_model_response",
        decision_sequence,
    )


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


def test_runtime_can_depend_on_provider_independent_tool_runtime() -> None:
    registry = ToolRegistry()
    registry.register(_AddTool())
    runtime = AgentRuntime(tool_runtime=ToolRuntime(registry))

    assert runtime.tool_runtime is not None


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


def test_runtime_propose_action_exposes_registered_tools_to_model_request() -> None:
    gateway = _RecordingStubModelGateway()
    registry = ToolRegistry()
    registry.register(_AddTool())
    runtime = AgentRuntime(model_gateway=gateway, tool_runtime=ToolRuntime(registry))
    runtime.transition_to(AgentExecutionStatus.CONTEXT)
    runtime.transition_to(AgentExecutionStatus.THINK)

    runtime.propose_action(model_id="mock-model", user_prompt="What is 2+3?")

    assert len(gateway.requests) == 1
    assert len(gateway.requests[0].tools) == 1
    assert gateway.requests[0].tools[0].name == "add"
    assert gateway.requests[0].tools[0].description == "Add two integers."
    assert gateway.requests[0].tools[0].input_schema == {
        "type": "object",
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "integer"},
        },
        "required": ["a", "b"],
        "additionalProperties": False,
    }


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
        (
            ModelDecision.tool_call(tool_name="add", arguments={"a": 2, "b": 3}),
            AgentExecutionStatus.TOOL_CALL,
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


def test_runtime_run_tool_call_then_respond_completes_with_structured_tool_observation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transitions = _capture_runtime_transitions(monkeypatch)
    _patch_interpret_model_decisions(
        monkeypatch,
        [
            ModelDecision.tool_call(tool_name="add", arguments={"a": 2, "b": 3}),
            ModelDecision(kind=ModelDecisionKind.RESPOND, proposed_response="The answer is 5"),
        ],
    )

    registry = ToolRegistry()
    add_tool = _AddTool()
    registry.register(add_tool)
    gateway = _SequenceStubModelGateway(
        responses=[
            ModelResponse(
                model_id="mock-model",
                output_text="tool-call",
                finish_reason=ModelFinishReason.STOP,
            ),
            ModelResponse(
                model_id="mock-model",
                output_text="respond",
                finish_reason=ModelFinishReason.STOP,
            ),
        ]
    )
    runtime = AgentRuntime(
        model_gateway=gateway,
        tool_runtime=ToolRuntime(registry),
    )

    result = runtime.run(model_id="mock-model", user_prompt="What is 2+3?")

    assert result.outcome is AgentRuntimeExecutionOutcome.RESPONDED
    assert result.proposed_response == "The answer is 5"
    assert result.model_iterations == 2
    assert runtime.state == AgentExecutionState(status=AgentExecutionStatus.COMPLETED)
    assert add_tool.was_executed is True
    assert len(gateway.requests) == 2
    assert len(runtime.tool_results) == 1
    tool_result = runtime.tool_results[0]
    assert tool_result.status is ToolResultStatus.SUCCESS
    assert tool_result.output_as_mapping() == {"value": 5}
    second_request = gateway.requests[1]
    assert len(second_request.messages) == 3
    assert second_request.messages[0] == ModelMessage(role=ModelRole.USER, content="What is 2+3?")
    assert second_request.messages[1].role is ModelRole.ASSISTANT
    assert second_request.messages[1].tool_call == ModelToolCall.from_mapping(
        tool_name="add",
        arguments={"a": 2, "b": 3},
        tool_call_id="call-1",
    )
    assert second_request.messages[2].role is ModelRole.TOOL
    assert second_request.messages[2].tool_result is not None
    assert second_request.messages[2].tool_result.status is ModelToolResultStatus.SUCCESS
    assert second_request.messages[2].tool_result.tool_name == "add"
    assert second_request.messages[2].tool_result.tool_call_id == "call-1"
    assert second_request.messages[2].tool_result.output_as_mapping() == {"value": 5}
    assert transitions == [
        AgentExecutionStatus.CONTEXT,
        AgentExecutionStatus.THINK,
        AgentExecutionStatus.ACTION_PROPOSED,
        AgentExecutionStatus.RUNTIME_VALIDATE,
        AgentExecutionStatus.TOOL_CALL,
        AgentExecutionStatus.THINK,
        AgentExecutionStatus.ACTION_PROPOSED,
        AgentExecutionStatus.RUNTIME_VALIDATE,
        AgentExecutionStatus.RESPOND,
        AgentExecutionStatus.COMPLETED,
    ]


def test_runtime_preserves_system_and_user_messages_across_tool_iterations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_interpret_model_decisions(
        monkeypatch,
        [
            ModelDecision.tool_call(tool_name="add", arguments={"a": 2, "b": 3}),
            ModelDecision(kind=ModelDecisionKind.RESPOND, proposed_response="The answer is 5"),
        ],
    )
    registry = ToolRegistry()
    registry.register(_AddTool())
    gateway = _SequenceStubModelGateway(
        responses=[
            ModelResponse(
                model_id="mock-model",
                output_text="tool-call",
                finish_reason=ModelFinishReason.STOP,
            ),
            ModelResponse(
                model_id="mock-model",
                output_text="respond",
                finish_reason=ModelFinishReason.STOP,
            ),
        ]
    )
    runtime = AgentRuntime(model_gateway=gateway, tool_runtime=ToolRuntime(registry))

    runtime.run(
        model_id="mock-model",
        user_prompt="What is 2+3?",
        system_prompt="Use tools when available.",
    )

    assert len(gateway.requests) == 2
    second_request = gateway.requests[1]
    assert [message.role for message in second_request.messages] == [
        ModelRole.SYSTEM,
        ModelRole.USER,
        ModelRole.ASSISTANT,
        ModelRole.TOOL,
    ]
    assert second_request.messages[0].content == "Use tools when available."
    assert second_request.messages[1].content == "What is 2+3?"


def test_runtime_run_tool_call_unknown_tool_error_is_returned_to_model_for_recovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_interpret_model_decisions(
        monkeypatch,
        [
            ModelDecision.tool_call(tool_name="missing", arguments={"a": 2, "b": 3}),
            ModelDecision.tool_call(tool_name="add", arguments={"a": 2, "b": 3}),
            ModelDecision(kind=ModelDecisionKind.RESPOND, proposed_response="The answer is 5"),
        ],
    )
    registry = ToolRegistry()
    registry.register(_AddTool())
    gateway = _SequenceStubModelGateway(
        responses=[
            ModelResponse(
                model_id="mock-model",
                output_text="tool-call",
                finish_reason=ModelFinishReason.STOP,
            ),
            ModelResponse(
                model_id="mock-model",
                output_text="tool-call-corrected",
                finish_reason=ModelFinishReason.STOP,
            ),
            ModelResponse(
                model_id="mock-model",
                output_text="respond",
                finish_reason=ModelFinishReason.STOP,
            ),
        ]
    )
    runtime = AgentRuntime(
        model_gateway=gateway,
        tool_runtime=ToolRuntime(registry),
    )

    result = runtime.run(model_id="mock-model", user_prompt="What is 2+3?")

    assert result.outcome is AgentRuntimeExecutionOutcome.RESPONDED
    assert result.proposed_response == "The answer is 5"
    assert result.model_iterations == 3
    assert runtime.state == AgentExecutionState(status=AgentExecutionStatus.COMPLETED)
    assert len(runtime.tool_results) == 2
    assert runtime.tool_results[0].status is ToolResultStatus.ERROR
    assert runtime.tool_results[0].error is not None
    assert runtime.tool_results[0].error.error_type == "UnknownToolError"
    assert runtime.tool_results[0].error.message == "Unknown tool: missing"
    assert runtime.tool_results[1].status is ToolResultStatus.SUCCESS
    second_request = gateway.requests[1]
    assert second_request.messages[-1].role is ModelRole.TOOL
    assert second_request.messages[-1].tool_result is not None
    assert second_request.messages[-1].tool_result.status is ModelToolResultStatus.ERROR
    assert second_request.messages[-1].tool_result.error_type == "UnknownToolError"
    assert second_request.messages[-1].tool_result.error_message == "Unknown tool: missing"


def test_runtime_run_tool_call_invalid_arguments_can_be_corrected_by_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_interpret_model_decisions(
        monkeypatch,
        [
            ModelDecision.tool_call(tool_name="add", arguments={"a": "2", "b": 3}),
            ModelDecision.tool_call(tool_name="add", arguments={"a": 2, "b": 3}),
            ModelDecision(kind=ModelDecisionKind.RESPOND, proposed_response="The answer is 5"),
        ],
    )
    registry = ToolRegistry()
    add_tool = _AddTool()
    registry.register(add_tool)
    gateway = _SequenceStubModelGateway(
        responses=[
            ModelResponse(
                model_id="mock-model",
                output_text="tool-call",
                finish_reason=ModelFinishReason.STOP,
            ),
            ModelResponse(
                model_id="mock-model",
                output_text="tool-call-corrected",
                finish_reason=ModelFinishReason.STOP,
            ),
            ModelResponse(
                model_id="mock-model",
                output_text="respond",
                finish_reason=ModelFinishReason.STOP,
            ),
        ]
    )
    runtime = AgentRuntime(
        model_gateway=gateway,
        tool_runtime=ToolRuntime(registry),
    )

    result = runtime.run(model_id="mock-model", user_prompt="What is 2+3?")

    assert result.outcome is AgentRuntimeExecutionOutcome.RESPONDED
    assert result.proposed_response == "The answer is 5"
    assert result.model_iterations == 3
    assert add_tool.was_executed is True
    assert runtime.state == AgentExecutionState(status=AgentExecutionStatus.COMPLETED)
    assert len(runtime.tool_results) == 2
    first_tool_result = runtime.tool_results[0]
    assert first_tool_result.status is ToolResultStatus.ERROR
    assert first_tool_result.error is not None
    assert first_tool_result.error.error_type == "ToolInputValidationError"
    assert "Type mismatches: a expected int, got str" in first_tool_result.error.message
    second_request = gateway.requests[1]
    assert second_request.messages[-1].role is ModelRole.TOOL
    assert second_request.messages[-1].tool_result is not None
    assert second_request.messages[-1].tool_result.status is ModelToolResultStatus.ERROR
    assert second_request.messages[-1].tool_result.error_type == "ToolInputValidationError"


def test_runtime_run_tool_call_execution_error_is_returned_and_bounded_by_iteration_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transitions = _capture_runtime_transitions(monkeypatch)
    _patch_interpret_model_decisions(
        monkeypatch,
        [
            ModelDecision.tool_call(tool_name="explode", arguments={"message": "boom"}),
            ModelDecision.tool_call(tool_name="explode", arguments={"message": "boom-again"}),
        ],
    )
    registry = ToolRegistry()
    registry.register(_FailingTool())
    gateway = _SequenceStubModelGateway(
        responses=[
            ModelResponse(
                model_id="mock-model",
                output_text="tool-call",
                finish_reason=ModelFinishReason.STOP,
            ),
            ModelResponse(
                model_id="mock-model",
                output_text="tool-call-again",
                finish_reason=ModelFinishReason.STOP,
            ),
        ]
    )
    runtime = AgentRuntime(
        model_gateway=gateway,
        tool_runtime=ToolRuntime(registry),
    )

    result = runtime.run(model_id="mock-model", user_prompt="explode", max_model_iterations=2)

    assert result.outcome is AgentRuntimeExecutionOutcome.LIMIT_REACHED
    assert result.error_message is not None
    assert "exceeded max model iterations" in result.error_message
    assert result.model_iterations == 2
    assert runtime.state == AgentExecutionState(status=AgentExecutionStatus.FAILED)
    assert len(runtime.tool_results) == 2
    assert runtime.tool_results[0].status is ToolResultStatus.ERROR
    assert runtime.tool_results[0].error is not None
    assert runtime.tool_results[0].error.error_type == "RuntimeError"
    assert runtime.tool_results[0].error.message == "failed: boom"
    assert runtime.tool_results[1].status is ToolResultStatus.ERROR
    assert runtime.tool_results[1].error is not None
    assert runtime.tool_results[1].error.error_type == "RuntimeError"
    assert runtime.tool_results[1].error.message == "failed: boom-again"
    assert transitions == [
        AgentExecutionStatus.CONTEXT,
        AgentExecutionStatus.THINK,
        AgentExecutionStatus.ACTION_PROPOSED,
        AgentExecutionStatus.RUNTIME_VALIDATE,
        AgentExecutionStatus.TOOL_CALL,
        AgentExecutionStatus.THINK,
        AgentExecutionStatus.ACTION_PROPOSED,
        AgentExecutionStatus.RUNTIME_VALIDATE,
        AgentExecutionStatus.TOOL_CALL,
        AgentExecutionStatus.THINK,
        AgentExecutionStatus.ACTION_PROPOSED,
        AgentExecutionStatus.RUNTIME_VALIDATE,
        AgentExecutionStatus.FAILED,
    ]


def test_runtime_run_rejects_non_positive_max_model_iterations() -> None:
    runtime = AgentRuntime(model_gateway=_RecordingStubModelGateway())

    with pytest.raises(ValueError, match="max_model_iterations must be >= 1"):
        runtime.run(model_id="mock-model", user_prompt="hello", max_model_iterations=0)
