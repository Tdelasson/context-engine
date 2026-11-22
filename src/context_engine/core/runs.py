"""Structured run records and the in-memory run registry."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, replace
from enum import StrEnum

from context_engine.agent import AgentRuntimeExecutionOutcome, AgentRuntimeExecutionResult
from context_engine.observability import RunEvent, ToolApprovalRequested, ToolApprovalResolved
from context_engine.tools import (
    ToolApprovalDecision,
    ToolApprovalResolution,
    ToolExecutionTrace,
    ToolResult,
    ToolResultStatus,
)


class RunStatus(StrEnum):
    """Application-level status of one run."""

    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    SUCCESS = "success"
    FAILED = "failed"
    LIMIT_REACHED = "limit_reached"

    @property
    def is_finished(self) -> bool:
        """Return whether the run has ended."""
        return self not in (RunStatus.RUNNING, RunStatus.AWAITING_APPROVAL)


class RunAlreadyActiveError(RuntimeError):
    """Raised when a run is started while another run is still active."""

    def __init__(self, active_run_id: str) -> None:
        super().__init__(f"Run {active_run_id} is still active; only one run may be active.")
        self.active_run_id = active_run_id


class UnknownRunError(LookupError):
    """Raised when a run id is not present in the registry."""

    def __init__(self, run_id: str) -> None:
        super().__init__(f"Unknown run: {run_id}")
        self.run_id = run_id


class InvalidPromptError(ValueError):
    """Raised when a prompt cannot start a run."""


class NoPendingApprovalError(RuntimeError):
    """Raised when an approval decision targets a run with no unanswered approval request."""

    def __init__(self, run_id: str) -> None:
        super().__init__(f"Run {run_id} has no pending approval request.")
        self.run_id = run_id


@dataclass(frozen=True, slots=True)
class PendingApproval:
    """The tool invocation a run is waiting for a person to approve or reject."""

    tool_name: str
    arguments: tuple[tuple[str, object], ...]
    invocation_id: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class RunRecord:
    """Immutable structured snapshot of one run.

    ``result`` is ``None`` while the run is active and when it failed outside the
    runtime result contract; ``error_phase`` then names where it failed.
    """

    run_id: str
    prompt: str
    model_id: str
    max_model_iterations: int
    status: RunStatus
    started_at: float
    finished_at: float | None = None
    result: AgentRuntimeExecutionResult | None = None
    tool_results: tuple[ToolResult, ...] = ()
    traces: tuple[ToolExecutionTrace, ...] = ()
    events: tuple[RunEvent, ...] = ()
    pending_approval: PendingApproval | None = None
    error_phase: str | None = None
    error_message: str | None = None

    @property
    def final_response(self) -> str | None:
        """Return the model's final response, when the runtime produced one."""
        return None if self.result is None else self.result.proposed_response

    @property
    def model_iterations(self) -> int:
        """Return how many model iterations the runtime reported."""
        return 0 if self.result is None else self.result.model_iterations


def derive_run_status(
    result: AgentRuntimeExecutionResult, traces: tuple[ToolExecutionTrace, ...]
) -> RunStatus:
    """Map a runtime result to an application status without inventing success.

    A run that responded after any tool error is reported as failed.
    """
    if result.outcome is AgentRuntimeExecutionOutcome.LIMIT_REACHED:
        return RunStatus.LIMIT_REACHED
    if result.outcome is AgentRuntimeExecutionOutcome.RESPONDED:
        if any(trace.status is ToolResultStatus.ERROR for trace in traces):
            return RunStatus.FAILED
        return RunStatus.SUCCESS
    return RunStatus.FAILED


def derive_error(
    result: AgentRuntimeExecutionResult,
    traces: tuple[ToolExecutionTrace, ...],
    status: RunStatus,
) -> tuple[str | None, str | None]:
    """Return the failing phase and message for a finished runtime result."""
    if status is RunStatus.SUCCESS:
        return None, None
    first_trace_error = next((trace.error for trace in traces if trace.error is not None), None)
    if first_trace_error is not None:
        return "tool_execution", f"{first_trace_error.error_type}: {first_trace_error.message}"
    return "agent_runtime", result.error_message


class RunRegistry:
    """Thread-safe in-memory run store allowing one active run at a time.

    Runs are kept for the lifetime of the process. Events are appended by the run's
    worker thread and read by other threads through snapshots.
    """

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._records: dict[str, RunRecord] = {}
        self._order: list[str] = []
        self._active_run_id: str | None = None
        self._decisions: dict[str, ToolApprovalResolution] = {}

    @property
    def active_run_id(self) -> str | None:
        """Return the id of the active run, if any."""
        with self._condition:
            return self._active_run_id

    def begin(self, record: RunRecord) -> None:
        """Register a new active run, or fail when one is already active."""
        with self._condition:
            if self._active_run_id is not None:
                raise RunAlreadyActiveError(self._active_run_id)
            if record.run_id in self._records:
                raise ValueError(f"Duplicate run id: {record.run_id}")
            self._records[record.run_id] = record
            self._order.append(record.run_id)
            self._active_run_id = record.run_id
            self._condition.notify_all()

    def append_event(self, event: RunEvent) -> None:
        """Append one event to its run."""
        with self._condition:
            record = self._records.get(event.run_id)
            if record is None:
                return
            updated = replace(record, events=(*record.events, event))
            payload = event.payload
            if isinstance(payload, ToolApprovalRequested) and not record.status.is_finished:
                self._decisions.pop(event.run_id, None)
                updated = replace(
                    updated,
                    status=RunStatus.AWAITING_APPROVAL,
                    pending_approval=PendingApproval(
                        tool_name=payload.tool_name,
                        arguments=payload.arguments,
                        invocation_id=payload.invocation_id,
                        reason=payload.reason,
                    ),
                )
            elif isinstance(payload, ToolApprovalResolved) and not record.status.is_finished:
                self._decisions.pop(event.run_id, None)
                updated = replace(updated, status=RunStatus.RUNNING, pending_approval=None)
            self._records[event.run_id] = updated
            self._condition.notify_all()

    def decide(self, run_id: str, resolution: ToolApprovalResolution) -> None:
        """Record the one decision for the run's pending approval request."""
        with self._condition:
            record = self._require(run_id)
            if record.pending_approval is None or run_id in self._decisions:
                raise NoPendingApprovalError(run_id)
            self._decisions[run_id] = resolution
            self._condition.notify_all()

    def await_decision(self, run_id: str, *, timeout: float) -> ToolApprovalResolution:
        """Block until a decision arrives; resolve as rejected when ``timeout`` elapses."""
        with self._condition:
            self._condition.wait_for(lambda: run_id in self._decisions, timeout=timeout)
            if run_id not in self._decisions:
                self._decisions[run_id] = ToolApprovalResolution(
                    decision=ToolApprovalDecision.REJECTED,
                    reason=f"Approval timed out after {timeout:g} seconds.",
                )
            return self._decisions[run_id]

    def finish(self, run_id: str, update: Callable[[RunRecord], RunRecord]) -> RunRecord:
        """Replace an active run with its finished record and free the run slot."""
        with self._condition:
            record = self._require(run_id)
            finished = replace(update(record), pending_approval=None)
            self._decisions.pop(run_id, None)
            if not finished.status.is_finished:
                raise ValueError("A finished run record must have a finished status.")
            self._records[run_id] = finished
            if self._active_run_id == run_id:
                self._active_run_id = None
            self._condition.notify_all()
            return finished

    def get(self, run_id: str) -> RunRecord:
        """Return the current snapshot of one run."""
        with self._condition:
            return self._require(run_id)

    def list_runs(self) -> tuple[RunRecord, ...]:
        """Return all runs in start order."""
        with self._condition:
            return tuple(self._records[run_id] for run_id in self._order)

    def wait_for_events(
        self, run_id: str, *, after_sequence: int, timeout: float | None = None
    ) -> tuple[tuple[RunEvent, ...], bool]:
        """Return events newer than ``after_sequence`` and whether the run has finished.

        Blocks until a newer event exists, the run finishes, or ``timeout`` elapses.
        """
        with self._condition:
            self._require(run_id)

            def ready() -> bool:
                record = self._records[run_id]
                return record.status.is_finished or any(
                    event.sequence > after_sequence for event in record.events
                )

            self._condition.wait_for(ready, timeout=timeout)
            record = self._records[run_id]
            newer = tuple(event for event in record.events if event.sequence > after_sequence)
            return newer, record.status.is_finished

    def wait_until_finished(self, run_id: str, timeout: float | None = None) -> RunRecord:
        """Block until the run finishes or ``timeout`` elapses, then return its snapshot."""
        with self._condition:
            self._require(run_id)
            self._condition.wait_for(
                lambda: self._records[run_id].status.is_finished, timeout=timeout
            )
            return self._records[run_id]

    def _require(self, run_id: str) -> RunRecord:
        record = self._records.get(run_id)
        if record is None:
            raise UnknownRunError(run_id)
        return record
