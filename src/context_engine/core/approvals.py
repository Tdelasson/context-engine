"""Approval resolver that blocks a run worker until a person decides."""

from __future__ import annotations

from context_engine.core.runs import RunRegistry
from context_engine.tools import ToolApprovalRequest, ToolApprovalResolution


class RunApprovalResolver:
    """Waits on the run registry for a decision, resolving as rejected on timeout.

    The pending request itself is published by the registry when the tool runtime emits
    its approval-requested event, so a client that sees the event can always answer it.
    """

    def __init__(self, registry: RunRegistry, run_id: str, *, timeout_seconds: float) -> None:
        self._registry = registry
        self._run_id = run_id
        self._timeout_seconds = timeout_seconds

    def resolve(self, request: ToolApprovalRequest) -> ToolApprovalResolution:
        del request
        return self._registry.await_decision(self._run_id, timeout=self._timeout_seconds)
