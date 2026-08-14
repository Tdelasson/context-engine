"""Deterministic runtime orchestration for a single agent execution."""

from dataclasses import dataclass
from enum import StrEnum

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
    normalize_messages,
)


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

    def apply_model_decision(self, decision: ModelDecision) -> AgentExecutionState:
        """Apply a decision through runtime-owned validation transitions."""
        runtime_validated_state = transition_agent_state(
            self._state, AgentExecutionStatus.RUNTIME_VALIDATE
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
    ) -> ModelDecision:
        """Generate and interpret a model decision for THINK -> ACTION_PROPOSED."""
        if self._model_gateway is None:
            raise AgentRuntimeModelInteractionError(
                "Model gateway is required for runtime model interaction."
            )

        self._state = transition_agent_state(self._state, AgentExecutionStatus.ACTION_PROPOSED)

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
        self.apply_model_decision(decision)
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

        while not self.is_terminal:
            if self._state.status is AgentExecutionStatus.START:
                self.transition_to(AgentExecutionStatus.CONTEXT)
                continue

            if self._state.status is AgentExecutionStatus.CONTEXT:
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

            if self._state.status is AgentExecutionStatus.TOOL_CALL:
                self.transition_to(AgentExecutionStatus.THINK)
                continue

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
