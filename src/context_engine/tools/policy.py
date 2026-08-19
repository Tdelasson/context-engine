"""Provider-independent deterministic policy contracts for tool invocation."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from context_engine.tools.runtime import ToolInvocation


class ToolPolicyDecision(StrEnum):
    """Explicit deterministic decisions made by a tool policy."""

    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True, slots=True)
class ToolPolicyEvaluation:
    """Structured policy evaluation for one proposed tool invocation."""

    decision: ToolPolicyDecision
    reason: str | None = None


@runtime_checkable
class ToolPolicy(Protocol):
    """Provider-independent tool policy contract."""

    def evaluate(self, invocation: "ToolInvocation") -> ToolPolicyEvaluation:
        """Evaluate one proposed tool invocation deterministically."""


class AllowAllToolPolicy:
    """Simple deterministic policy that allows every invocation."""

    def evaluate(self, invocation: "ToolInvocation") -> ToolPolicyEvaluation:
        del invocation
        return ToolPolicyEvaluation(decision=ToolPolicyDecision.ALLOW)


@dataclass(frozen=True, slots=True)
class ToolNamePolicy:
    """Deterministic name-based policy suitable for tests and extension."""

    tool_decisions: tuple[tuple[str, ToolPolicyDecision], ...]
    default_decision: ToolPolicyDecision = ToolPolicyDecision.ALLOW

    @classmethod
    def from_mapping(
        cls,
        tool_decisions: Mapping[str, ToolPolicyDecision],
        *,
        default_decision: ToolPolicyDecision = ToolPolicyDecision.ALLOW,
    ) -> "ToolNamePolicy":
        return cls(
            tool_decisions=tuple(sorted(tool_decisions.items())),
            default_decision=default_decision,
        )

    def evaluate(self, invocation: "ToolInvocation") -> ToolPolicyEvaluation:
        decisions = dict(self.tool_decisions)
        decision = decisions.get(invocation.tool_name, self.default_decision)
        if decision is ToolPolicyDecision.DENY:
            return ToolPolicyEvaluation(
                decision=ToolPolicyDecision.DENY,
                reason=f"Tool invocation denied by policy: {invocation.tool_name}",
            )
        return ToolPolicyEvaluation(decision=ToolPolicyDecision.ALLOW)
