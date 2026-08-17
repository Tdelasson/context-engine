"""Deterministic runtime orchestration for a single agent execution."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from context_engine.agent.decision import (
    ModelDecision,
    ModelDecisionInterpretationError,
    ModelDecisionKind,
    interpret_model_response,
)
from context_engine.agent.state import AgentExecutionState, AgentExecutionStatus
from context_engine.agent.transitions import transition_agent_state
from context_engine.models import (
    ModelGateway,
    ModelGatewayError,
    ModelMessage,
    ModelRequest,
    ModelRole,
    ModelToolCall,
    ModelToolDefinition,
    ModelToolResult,
    normalize_messages,
    normalize_model_tools,
)
from context_engine.tools import (
    Tool,
    ToolInvocation,
    ToolResult,
    ToolResultStatus,
    ToolRuntimeError,
)


@runtime_checkable
class AgentToolRuntime(Protocol):
    """Provider-independent tool runtime boundary used by the agent runtime."""

    def execute(self, invocation: ToolInvocation) -> ToolResult:
        """Execute one validated tool invocation."""

    def list_tools(self) -> tuple[Tool, ...]:
        """Return registered tools for provider-independent model declaration."""


class AgentRuntimeModelInteractionError(RuntimeError):
    """Raised when runtime-model interaction fails at the runtime boundary."""


class AgentRuntimeExecutionOutcome(StrEnum):
    """Terminal outcomes of a deterministic runtime execution loop."""

    RESPONDED = "responded"
    FAILED = "failed"
    LIMIT_REACHED = "limit_reached"


@dataclass(frozen=True, slots=True)
class AgentRuntimeExecutionResult:
    """Typed terminal result returned by runtime execution."""

    outcome: AgentRuntimeExecutionOutcome
    terminal_state: AgentExecutionState
    proposed_response: str | None = None
    error_message: str | None = None
    model_iterations: int = 0


class AgentRuntime:
    """Owns execution state and applies validated transitions deterministically."""

    def __init__(
        self,
        initial_state: AgentExecutionState | None = None,
        model_gateway: ModelGateway | None = None,
        tool_runtime: AgentToolRuntime | None = None,
    ) -> None:
        self._state = initial_state or AgentExecutionState(status=AgentExecutionStatus.START)
        self._model_gateway = model_gateway
        self._tool_runtime = tool_runtime
        self._tool_results: list[ToolResult] = []

    @property
    def state(self) -> AgentExecutionState:
        """Return the current immutable execution state."""
        return self._state

    @property
    def model_gateway(self) -> ModelGateway | None:
        """Return the runtime's provider-independent model gateway dependency."""
        return self._model_gateway

    @property
    def tool_runtime(self) -> AgentToolRuntime | None:
        """Return the runtime's provider-independent tool runtime dependency."""
        return self._tool_runtime

    @property
    def tool_results(self) -> tuple[ToolResult, ...]:
        """Return structured immutable tool results captured during execution."""
        return tuple(self._tool_results)

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

    def apply_model_decision(
        self,
        decision: ModelDecision,
        *,
        from_state: AgentExecutionState | None = None,
    ) -> AgentExecutionState:
        """Apply a decision through runtime-owned validation transitions."""
        decision_state = self._state if from_state is None else from_state
        runtime_validated_state = transition_agent_state(
            decision_state, AgentExecutionStatus.RUNTIME_VALIDATE
        )
        target_status = self._target_status_for_decision(decision)
        self._state = transition_agent_state(runtime_validated_state, target_status)
        return self._state

    def propose_action(
        self,
        *,
        model_id: str,
        user_prompt: str,
        system_prompt: str | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        messages: tuple[ModelMessage, ...] | None = None,
    ) -> ModelDecision:
        """Generate and interpret a model decision for THINK -> ACTION_PROPOSED."""
        if self._model_gateway is None:
            raise AgentRuntimeModelInteractionError(
                "Model gateway is required for runtime model interaction."
            )

        action_proposed_state = transition_agent_state(
            self._state, AgentExecutionStatus.ACTION_PROPOSED
        )

        request = self._build_model_request(
            model_id=model_id,
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            messages=messages,
        )

        try:
            response = self._model_gateway.generate(request)
        except ModelGatewayError as exc:
            raise AgentRuntimeModelInteractionError(
                "Model gateway failed during runtime model interaction."
            ) from exc

        decision = interpret_model_response(response)
        self.apply_model_decision(decision, from_state=action_proposed_state)
        return decision

    def run(
        self,
        *,
        model_id: str,
        user_prompt: str,
        system_prompt: str | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        max_model_iterations: int = 8,
    ) -> AgentRuntimeExecutionResult:
        """Run the deterministic runtime loop until a terminal state is reached."""
        if max_model_iterations < 1:
            raise ValueError("max_model_iterations must be >= 1.")

        model_iterations = 0
        conversation_history = self._build_initial_conversation_history(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        while not self.is_terminal:
            if self._state.status is AgentExecutionStatus.START:
                self.transition_to(AgentExecutionStatus.CONTEXT)
                continue

            if self._state.status in {
                AgentExecutionStatus.CONTEXT,
                AgentExecutionStatus.TOOL_CALL,
            }:
                self.transition_to(AgentExecutionStatus.THINK)
                continue

            if self._state.status is AgentExecutionStatus.THINK:
                if model_iterations >= max_model_iterations:
                    self.transition_to(AgentExecutionStatus.ACTION_PROPOSED)
                    self.transition_to(AgentExecutionStatus.RUNTIME_VALIDATE)
                    self.fail()
                    return AgentRuntimeExecutionResult(
                        outcome=AgentRuntimeExecutionOutcome.LIMIT_REACHED,
                        terminal_state=self._state,
                        error_message=(
                            "Agent runtime exceeded max model iterations before reaching "
                            "a terminal response."
                        ),
                        model_iterations=model_iterations,
                    )

                model_iterations += 1
                try:
                    decision = self.propose_action(
                        model_id=model_id,
                        user_prompt=user_prompt,
                        system_prompt=system_prompt,
                        max_output_tokens=max_output_tokens,
                        temperature=temperature,
                        messages=normalize_messages(conversation_history),
                    )
                except (AgentRuntimeModelInteractionError, ModelDecisionInterpretationError) as exc:
                    self._transition_to_failed_terminal()
                    return AgentRuntimeExecutionResult(
                        outcome=AgentRuntimeExecutionOutcome.FAILED,
                        terminal_state=self._state,
                        error_message=str(exc),
                        model_iterations=model_iterations,
                    )

                if decision.kind is ModelDecisionKind.RESPOND:
                    conversation_history.append(
                        ModelMessage(
                            role=ModelRole.ASSISTANT,
                            content=decision.proposed_response or "",
                        )
                    )
                    self.complete()
                    return AgentRuntimeExecutionResult(
                        outcome=AgentRuntimeExecutionOutcome.RESPONDED,
                        terminal_state=self._state,
                        proposed_response=decision.proposed_response,
                        model_iterations=model_iterations,
                    )

                if decision.kind is ModelDecisionKind.FAIL:
                    return AgentRuntimeExecutionResult(
                        outcome=AgentRuntimeExecutionOutcome.FAILED,
                        terminal_state=self._state,
                        model_iterations=model_iterations,
                    )

                if decision.kind is ModelDecisionKind.TOOL_CALL:
                    tool_call = self._build_tool_call_from_decision(decision)
                    conversation_history.append(
                        ModelMessage(
                            role=ModelRole.ASSISTANT,
                            tool_call=tool_call,
                        )
                    )
                    try:
                        tool_result = self._execute_tool_call(decision)
                    except AgentRuntimeModelInteractionError as exc:
                        self._transition_to_failed_from_tool_call()
                        return AgentRuntimeExecutionResult(
                            outcome=AgentRuntimeExecutionOutcome.FAILED,
                            terminal_state=self._state,
                            error_message=str(exc),
                            model_iterations=model_iterations,
                        )
                    self._tool_results.append(tool_result)
                    conversation_history.append(
                        ModelMessage(
                            role=ModelRole.TOOL,
                            tool_result=self._build_model_tool_result_message(
                                tool_result=tool_result,
                                tool_call=tool_call,
                            ),
                        )
                    )
                    if tool_result.status is not ToolResultStatus.SUCCESS:
                        self._transition_to_failed_from_tool_call()
                        return AgentRuntimeExecutionResult(
                            outcome=AgentRuntimeExecutionOutcome.FAILED,
                            terminal_state=self._state,
                            error_message=self._tool_error_message(tool_result),
                            model_iterations=model_iterations,
                        )
                    self.transition_to(AgentExecutionStatus.THINK)
                    continue

                continue

            if self._state.status is AgentExecutionStatus.RESPOND:
                self.complete()
                return AgentRuntimeExecutionResult(
                    outcome=AgentRuntimeExecutionOutcome.RESPONDED,
                    terminal_state=self._state,
                    model_iterations=model_iterations,
                )

            if self._state.status is AgentExecutionStatus.ACTION_PROPOSED:
                self._transition_to_failed_terminal()
                return AgentRuntimeExecutionResult(
                    outcome=AgentRuntimeExecutionOutcome.FAILED,
                    terminal_state=self._state,
                    error_message=(
                        "Runtime execution encountered ACTION_PROPOSED without a model decision."
                    ),
                    model_iterations=model_iterations,
                )

            if self._state.status is AgentExecutionStatus.RUNTIME_VALIDATE:
                self._transition_to_failed_terminal()
                return AgentRuntimeExecutionResult(
                    outcome=AgentRuntimeExecutionOutcome.FAILED,
                    terminal_state=self._state,
                    error_message=(
                        "Runtime execution encountered RUNTIME_VALIDATE without a deterministic "
                        "next action."
                    ),
                    model_iterations=model_iterations,
                )

            msg = f"Unsupported runtime execution state: {self._state.status.value}"
            raise AgentRuntimeModelInteractionError(msg)

        if self._state.status is AgentExecutionStatus.COMPLETED:
            return AgentRuntimeExecutionResult(
                outcome=AgentRuntimeExecutionOutcome.RESPONDED,
                terminal_state=self._state,
                model_iterations=model_iterations,
            )

        return AgentRuntimeExecutionResult(
            outcome=AgentRuntimeExecutionOutcome.FAILED,
            terminal_state=self._state,
            model_iterations=model_iterations,
        )

    def _target_status_for_decision(self, decision: ModelDecision) -> AgentExecutionStatus:
        if decision.kind is ModelDecisionKind.RESPOND:
            return AgentExecutionStatus.RESPOND
        if decision.kind is ModelDecisionKind.TOOL_CALL:
            return AgentExecutionStatus.TOOL_CALL
        if decision.kind is ModelDecisionKind.RETRY:
            return AgentExecutionStatus.THINK
        if decision.kind is ModelDecisionKind.FAIL:
            return AgentExecutionStatus.FAILED
        msg = f"Unsupported model decision kind for runtime transition: {decision.kind!r}"
        raise AgentRuntimeModelInteractionError(msg)

    def _transition_to_failed_terminal(self) -> AgentExecutionState:
        if self._state.status is AgentExecutionStatus.THINK:
            self.transition_to(AgentExecutionStatus.ACTION_PROPOSED)
        if self._state.status is AgentExecutionStatus.ACTION_PROPOSED:
            self.transition_to(AgentExecutionStatus.RUNTIME_VALIDATE)
        if self._state.status is AgentExecutionStatus.RUNTIME_VALIDATE:
            return self.fail()

        msg = (
            f"Cannot transition runtime to FAILED from current status: {self._state.status.value}."
        )
        raise AgentRuntimeModelInteractionError(msg)

    def _build_model_request(
        self,
        *,
        model_id: str,
        user_prompt: str,
        system_prompt: str | None,
        max_output_tokens: int | None,
        temperature: float | None,
        messages: tuple[ModelMessage, ...] | None = None,
    ) -> ModelRequest:
        if messages is None:
            built_messages: list[ModelMessage] = []
            if system_prompt is not None:
                built_messages.append(ModelMessage(role=ModelRole.SYSTEM, content=system_prompt))
            built_messages.append(ModelMessage(role=ModelRole.USER, content=user_prompt))
            normalized_messages = normalize_messages(built_messages)
        else:
            normalized_messages = normalize_messages(messages)

        return ModelRequest(
            model_id=model_id,
            messages=normalized_messages,
            tools=self._build_model_tool_definitions(),
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )

    def _build_model_tool_definitions(self) -> tuple[ModelToolDefinition, ...]:
        if self._tool_runtime is None:
            return ()

        tool_definitions = []
        for tool in self._tool_runtime.list_tools():
            properties: dict[str, object] = {}
            required: list[str] = []
            for field in tool.input_schema.fields:
                properties[field.name] = {"type": self._json_schema_type_name(field.value_type)}
                required.append(field.name)
            tool_definitions.append(
                ModelToolDefinition(
                    name=tool.name,
                    description=tool.description,
                    input_schema={
                        "type": "object",
                        "properties": properties,
                        "required": required,
                        "additionalProperties": False,
                    },
                )
            )

        return normalize_model_tools(tool_definitions)

    def _json_schema_type_name(self, value_type: type[object]) -> str:
        if value_type is bool:
            return "boolean"
        if value_type is int:
            return "integer"
        if value_type is float:
            return "number"
        if value_type is str:
            return "string"
        if value_type is list:
            return "array"
        if value_type is dict:
            return "object"
        return "string"

    def _execute_tool_call(self, decision: ModelDecision) -> ToolResult:
        if self._tool_runtime is None:
            raise AgentRuntimeModelInteractionError(
                "Tool runtime is required to execute TOOL_CALL decisions."
            )
        if decision.tool_name is None:
            raise AgentRuntimeModelInteractionError(
                "TOOL_CALL decision is missing required tool_name."
            )

        invocation = ToolInvocation(
            tool_name=decision.tool_name,
            arguments=decision.tool_arguments or tuple(),
        )

        try:
            return self._tool_runtime.execute(invocation)
        except ToolRuntimeError as exc:
            raise AgentRuntimeModelInteractionError(
                f"Tool runtime rejected invocation: {exc}"
            ) from exc

    def _build_initial_conversation_history(
        self,
        *,
        system_prompt: str | None,
        user_prompt: str,
    ) -> list[ModelMessage]:
        history: list[ModelMessage] = []
        if system_prompt is not None:
            history.append(ModelMessage(role=ModelRole.SYSTEM, content=system_prompt))
        history.append(ModelMessage(role=ModelRole.USER, content=user_prompt))
        return history

    def _build_tool_call_from_decision(self, decision: ModelDecision) -> ModelToolCall:
        if decision.tool_name is None:
            raise AgentRuntimeModelInteractionError(
                "TOOL_CALL decision is missing required tool_name."
            )
        return ModelToolCall.from_mapping(
            tool_name=decision.tool_name,
            arguments=decision.tool_arguments_as_mapping(),
            tool_call_id=f"call-{len(self._tool_results) + 1}",
        )

    def _build_model_tool_result_message(
        self,
        *,
        tool_result: ToolResult,
        tool_call: ModelToolCall,
    ) -> ModelToolResult:
        if tool_result.status is ToolResultStatus.SUCCESS:
            return ModelToolResult.success(
                tool_name=tool_result.invocation.tool_name,
                output=tool_result.output_as_mapping(),
                tool_call_id=tool_call.tool_call_id,
            )
        if tool_result.error is None:
            raise AgentRuntimeModelInteractionError(
                "Tool execution failed for "
                f"{tool_result.invocation.tool_name} without error details."
            )
        return ModelToolResult.error(
            tool_name=tool_result.invocation.tool_name,
            tool_call_id=tool_call.tool_call_id,
            error_type=tool_result.error.error_type,
            error_message=tool_result.error.message,
        )

    def _transition_to_failed_from_tool_call(self) -> AgentExecutionState:
        if self._state.status is not AgentExecutionStatus.TOOL_CALL:
            msg = (
                f"Cannot transition runtime to FAILED from current status: "
                f"{self._state.status.value}."
            )
            raise AgentRuntimeModelInteractionError(msg)

        self.transition_to(AgentExecutionStatus.THINK)
        return self._transition_to_failed_terminal()

    def _tool_error_message(self, result: ToolResult) -> str:
        if result.error is not None:
            return (
                f"Tool execution failed for {result.invocation.tool_name}: "
                f"{result.error.error_type}: {result.error.message}"
            )
        return f"Tool execution failed for {result.invocation.tool_name}"
