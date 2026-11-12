"""Typed, ordered run events emitted by the Agent and Tool runtimes.

Event contracts are provider-independent and deliberately hold only primitive values, so
this module imports nothing from the agent, tool, or model packages.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import ClassVar, Protocol, runtime_checkable
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class RunStarted:
    """A runtime execution loop began."""

    kind: ClassVar[str] = "run_started"

    model_id: str
    max_model_iterations: int


@dataclass(frozen=True, slots=True)
class StateTransitioned:
    """The runtime applied one validated state-machine transition."""

    kind: ClassVar[str] = "state_transitioned"

    from_status: str
    to_status: str


@dataclass(frozen=True, slots=True)
class ModelCallStarted:
    """The runtime sent one request to the model gateway."""

    kind: ClassVar[str] = "model_call_started"

    iteration: int


@dataclass(frozen=True, slots=True)
class ModelCallCompleted:
    """The model gateway returned or failed."""

    kind: ClassVar[str] = "model_call_completed"

    iteration: int
    duration_seconds: float
    finish_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ToolProposed:
    """The model proposed a tool call that the runtime will hand to the tool runtime."""

    kind: ClassVar[str] = "tool_proposed"

    tool_name: str
    arguments: tuple[tuple[str, object], ...]
    invocation_id: str | None = None


@dataclass(frozen=True, slots=True)
class ToolValidated:
    """Registry lookup and input-schema validation finished."""

    kind: ClassVar[str] = "tool_validated"

    tool_name: str
    accepted: bool
    invocation_id: str | None = None
    error_type: str | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class ToolPolicyDecided:
    """The tool policy evaluated one validated invocation."""

    kind: ClassVar[str] = "tool_policy_decided"

    tool_name: str
    decision: str
    invocation_id: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ToolApprovalRequested:
    """The runtime asked the approval resolver to decide one invocation."""

    kind: ClassVar[str] = "tool_approval_requested"

    tool_name: str
    arguments: tuple[tuple[str, object], ...]
    invocation_id: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ToolApprovalResolved:
    """The approval resolver returned a decision."""

    kind: ClassVar[str] = "tool_approval_resolved"

    tool_name: str
    decision: str
    invocation_id: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ToolCallFinished:
    """One tool invocation ended, whether or not tool code ran.

    ``executed`` is false when validation, policy, or approval stopped the invocation
    before execution; ``duration_seconds`` is then ``None``.
    """

    kind: ClassVar[str] = "tool_call_finished"

    tool_name: str
    status: str
    executed: bool
    invocation_id: str | None = None
    duration_seconds: float | None = None
    error_type: str | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class RunFinished:
    """A runtime execution loop ended. Exactly one is emitted per started run."""

    kind: ClassVar[str] = "run_finished"

    outcome: str
    terminal_status: str
    model_iterations: int
    error_message: str | None = None


RunEventPayload = (
    RunStarted
    | StateTransitioned
    | ModelCallStarted
    | ModelCallCompleted
    | ToolProposed
    | ToolValidated
    | ToolPolicyDecided
    | ToolApprovalRequested
    | ToolApprovalResolved
    | ToolCallFinished
    | RunFinished
)


@dataclass(frozen=True, slots=True)
class RunEvent:
    """Envelope giving one payload its run identity, order, and wall-clock time."""

    run_id: str
    sequence: int
    timestamp: float
    payload: RunEventPayload

    @property
    def kind(self) -> str:
        """Return the stable event-type name of the payload."""
        return self.payload.kind


@runtime_checkable
class RunEventSink(Protocol):
    """Receives run events in emission order."""

    def record(self, event: RunEvent) -> None:
        """Record one event. Failures are contained by the emitter."""


class RecordingRunEventSink:
    """In-memory sink that keeps events in the order they were recorded."""

    def __init__(self) -> None:
        self._events: list[RunEvent] = []

    def record(self, event: RunEvent) -> None:
        self._events.append(event)

    @property
    def events(self) -> tuple[RunEvent, ...]:
        """Return recorded events in emission order."""
        return tuple(self._events)


class RunEventEmitter:
    """Stamps payloads for one run and delivers them to a sink.

    Use one emitter per run and share it between the Agent and Tool runtimes so that both
    contribute to a single sequence. Telemetry must not determine runtime behavior: any
    exception raised by the sink is contained and counted, never propagated.

    The emitter is not synchronized; a run emits from a single thread.
    """

    def __init__(
        self,
        sink: RunEventSink,
        *,
        run_id: str | None = None,
        wall_clock: Callable[[], float] = time.time,
        monotonic_clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        if run_id is not None and not run_id.strip():
            raise ValueError("run_id must be a nonblank string when supplied.")
        self._sink = sink
        self._run_id = run_id if run_id is not None else uuid4().hex
        self._wall_clock = wall_clock
        self._monotonic_clock = monotonic_clock
        self._next_sequence = 1
        self._sink_failures = 0

    @property
    def run_id(self) -> str:
        """Return the identity stamped on every event from this emitter."""
        return self._run_id

    @property
    def sink_failures(self) -> int:
        """Return how many events the sink failed to record."""
        return self._sink_failures

    def monotonic(self) -> float:
        """Return the monotonic clock reading used to measure durations."""
        return self._monotonic_clock()

    def emit(self, payload: RunEventPayload) -> None:
        """Stamp and deliver one payload, containing any sink failure."""
        event = RunEvent(
            run_id=self._run_id,
            sequence=self._next_sequence,
            timestamp=self._wall_clock(),
            payload=payload,
        )
        self._next_sequence += 1
        try:
            self._sink.record(event)
        except Exception:
            self._sink_failures += 1
