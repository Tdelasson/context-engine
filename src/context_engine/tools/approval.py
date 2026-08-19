"""Provider-independent deterministic approval contracts for tool invocation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from context_engine.tools.policy import ToolPolicyEvaluation
    from context_engine.tools.runtime import ToolInvocation


class ToolApprovalDecision(StrEnum):
    """Explicit deterministic outcomes for approval-required tool invocations."""

    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ToolApprovalRequest:
    """Structured immutable approval request for one tool invocation."""

    invocation: ToolInvocation
    policy_evaluation: ToolPolicyEvaluation


@dataclass(frozen=True, slots=True)
class ToolApprovalResolution:
    """Deterministic approval resolution for one approval request."""

    decision: ToolApprovalDecision
    reason: str | None = None


@runtime_checkable
class ToolApprovalResolver(Protocol):
    """Provider-independent approval resolver contract."""

    def resolve(self, request: ToolApprovalRequest) -> ToolApprovalResolution:
        """Resolve one approval request deterministically."""
