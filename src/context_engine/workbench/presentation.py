"""Pure transformations from runtime contracts to workbench display models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from context_engine.agent import AgentRuntimeExecutionOutcome, AgentRuntimeExecutionResult
from context_engine.tools import (
    ToolExecutionTrace,
    ToolResult,
    ToolResultStatus,
)


class WorkbenchRunStatus(StrEnum):
    """Top-level status shown for a live run."""

    SUCCESS = "success"
    FAILED = "failed"
    LIMIT_REACHED = "limit_reached"


@dataclass(frozen=True, slots=True)
class LifecycleStep:
    """One human-readable stage in the integrated lifecycle."""

    name: str
    status: str
    detail: str


@dataclass(frozen=True, slots=True)
class RetrievedEvidence:
    """Normalized display data for one search_documents result."""

    document_id: str
    score: float
    source_kind: str
    source_name: str
    metadata: tuple[tuple[str, object], ...]
    content: str
    content_truncated: bool


@dataclass(frozen=True, slots=True)
class TraceView:
    """Presentation-safe view of a provider-independent tool trace."""

    tool_name: str
    arguments: tuple[tuple[str, object], ...]
    policy: str
    status: str
    error_type: str | None
    error_message: str | None


@dataclass(frozen=True, slots=True)
class WorkbenchRunView:
    """Complete immutable display model for one live agent execution."""

    prompt: str
    status: WorkbenchRunStatus
    final_response: str | None
    error_phase: str | None
    error_message: str | None
    lifecycle: tuple[LifecycleStep, ...]
    evidence: tuple[RetrievedEvidence, ...]
    traces: tuple[TraceView, ...]
    tool_results: tuple[ToolResult, ...]


def build_run_view(
    *,
    prompt: str,
    result: AgentRuntimeExecutionResult,
    tool_results: tuple[ToolResult, ...],
    traces: tuple[ToolExecutionTrace, ...],
) -> WorkbenchRunView:
    """Transform existing runtime contracts without inventing execution state."""
    status = _run_status(result, traces)
    lifecycle = _build_lifecycle(result=result, traces=traces)
    first_trace_error = next((trace.error for trace in traces if trace.error is not None), None)
    return WorkbenchRunView(
        prompt=prompt,
        status=status,
        final_response=result.proposed_response,
        error_phase=(
            None
            if status is WorkbenchRunStatus.SUCCESS
            else "tool_execution" if first_trace_error is not None else "agent_runtime"
        ),
        error_message=(
            f"{first_trace_error.error_type}: {first_trace_error.message}"
            if first_trace_error is not None
            else result.error_message
        ),
        lifecycle=lifecycle,
        evidence=_extract_evidence(tool_results),
        traces=tuple(_trace_view(trace) for trace in traces),
        tool_results=tool_results,
    )


def build_failed_run_view(*, prompt: str, phase: str, message: str) -> WorkbenchRunView:
    """Build an honest failure view for errors outside the runtime result contract."""
    return WorkbenchRunView(
        prompt=prompt,
        status=WorkbenchRunStatus.FAILED,
        final_response=None,
        error_phase=phase,
        error_message=message,
        lifecycle=(
            LifecycleStep(name="User prompt", status="complete", detail=prompt),
            LifecycleStep(name=phase.replace("_", " ").title(), status="failed", detail=message),
        ),
        evidence=(),
        traces=(),
        tool_results=(),
    )


def _run_status(
    result: AgentRuntimeExecutionResult,
    traces: tuple[ToolExecutionTrace, ...],
) -> WorkbenchRunStatus:
    if any(trace.status is ToolResultStatus.ERROR for trace in traces):
        return WorkbenchRunStatus.FAILED
    if result.outcome is AgentRuntimeExecutionOutcome.RESPONDED:
        return WorkbenchRunStatus.SUCCESS
    if result.outcome is AgentRuntimeExecutionOutcome.LIMIT_REACHED:
        return WorkbenchRunStatus.LIMIT_REACHED
    return WorkbenchRunStatus.FAILED


def _build_lifecycle(
    *,
    result: AgentRuntimeExecutionResult,
    traces: tuple[ToolExecutionTrace, ...],
) -> tuple[LifecycleStep, ...]:
    steps = [LifecycleStep(name="User prompt", status="complete", detail="Submitted to runtime")]
    if not traces:
        proposal_status = (
            "complete" if result.outcome is AgentRuntimeExecutionOutcome.RESPONDED else "failed"
        )
        steps.append(
            LifecycleStep(
                name="Model proposal",
                status=proposal_status,
                detail=(
                    "Direct response proposed"
                    if proposal_status == "complete"
                    else result.error_message or "No valid model proposal was produced"
                ),
            )
        )
    for index, trace in enumerate(traces, start=1):
        suffix = "" if len(traces) == 1 else f" #{index}"
        validation_passed = trace.policy_decision is not None
        steps.extend(
            (
                LifecycleStep(
                    name=f"Model tool proposal{suffix}",
                    status="complete",
                    detail=(
                        f"{trace.invocation.tool_name} {trace.invocation.arguments_as_mapping()}"
                    ),
                ),
                LifecycleStep(
                    name=f"Registry + schema validation{suffix}",
                    status="complete" if validation_passed else "failed",
                    detail=(
                        "Registered tool and typed arguments accepted"
                        if validation_passed
                        else _trace_error_detail(trace)
                    ),
                ),
                LifecycleStep(
                    name=f"Policy decision{suffix}",
                    status="complete" if trace.policy_decision is not None else "not_reached",
                    detail=(
                        trace.policy_decision.value
                        if trace.policy_decision is not None
                        else "Policy was not reached"
                    ),
                ),
                LifecycleStep(
                    name=f"Tool execution{suffix}",
                    status=trace.status.value,
                    detail=(
                        "Deterministic execution completed"
                        if trace.status is ToolResultStatus.SUCCESS
                        else _trace_error_detail(trace)
                    ),
                ),
                LifecycleStep(
                    name=f"Structured ToolResult{suffix}",
                    status=trace.status.value,
                    detail=(
                        str(trace.output_as_mapping())
                        if trace.status is ToolResultStatus.SUCCESS
                        else _trace_error_detail(trace)
                    ),
                ),
            )
        )
    steps.append(
        LifecycleStep(
            name="Final model response",
            status="complete" if result.proposed_response is not None else "failed",
            detail=result.proposed_response or result.error_message or "No final response produced",
        )
    )
    return tuple(steps)


def _trace_error_detail(trace: ToolExecutionTrace) -> str:
    if trace.error is None:
        return "No structured error details were returned"
    return f"{trace.error.error_type}: {trace.error.message}"


def _trace_view(trace: ToolExecutionTrace) -> TraceView:
    return TraceView(
        tool_name=trace.invocation.tool_name,
        arguments=trace.invocation.arguments,
        policy=(
            trace.policy_decision.value if trace.policy_decision is not None else "not_reached"
        ),
        status=trace.status.value,
        error_type=None if trace.error is None else trace.error.error_type,
        error_message=None if trace.error is None else trace.error.message,
    )


def _extract_evidence(tool_results: tuple[ToolResult, ...]) -> tuple[RetrievedEvidence, ...]:
    evidence: list[RetrievedEvidence] = []
    for tool_result in tool_results:
        if (
            tool_result.status is not ToolResultStatus.SUCCESS
            or tool_result.invocation.tool_name != "search_documents"
        ):
            continue
        raw_results = tool_result.output_as_mapping().get("results")
        if not isinstance(raw_results, list):
            continue
        for raw_result in raw_results:
            if not isinstance(raw_result, dict):
                continue
            metadata_value = raw_result.get("metadata")
            metadata = metadata_value if isinstance(metadata_value, dict) else {}
            document_id = raw_result.get("document_id")
            score = raw_result.get("score")
            content = raw_result.get("content")
            if not isinstance(document_id, str) or not isinstance(score, (int, float)):
                continue
            if not isinstance(content, str):
                continue
            evidence.append(
                RetrievedEvidence(
                    document_id=document_id,
                    score=float(score),
                    source_kind=str(metadata.get("source_kind", "unknown")),
                    source_name=str(metadata.get("source_name", document_id)),
                    metadata=tuple(sorted(metadata.items())),
                    content=content,
                    content_truncated=bool(raw_result.get("content_truncated", False)),
                )
            )
    return tuple(evidence)
