"""Explicit, provider-independent state model for agent execution."""

from dataclasses import dataclass
from enum import StrEnum


class AgentExecutionStatus(StrEnum):
    """Lifecycle states for a single agent execution."""

    START = "start"
    CONTEXT = "context"
    THINK = "think"
    ACTION_PROPOSED = "action_proposed"
    RUNTIME_VALIDATE = "runtime_validate"
    TOOL_CALL = "tool_call"
    RESPOND = "respond"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class AgentExecutionState:
    """Typed representation of the runtime's current execution state."""

    status: AgentExecutionStatus
