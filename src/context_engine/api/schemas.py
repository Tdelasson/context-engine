"""Typed HTTP request and response schemas for the ``/api/v1`` adapter.

Responses carry structured data only. Display strings, lifecycle views and pipeline
views are derived by clients.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, Field, JsonValue

from context_engine.core import (
    IngestionReport,
    PendingApproval,
    RunRecord,
    RunStatus,
    SourceListing,
    SystemDescription,
)
from context_engine.knowledge.ingestion import IngestionOutcome, source_diagnostics
from context_engine.knowledge.processing import ProcessingDiagnostic
from context_engine.observability import RunEvent
from context_engine.retrieval.source_store import SourceIndexRevision
from context_engine.tools import ToolExecutionTrace, ToolResult


def to_json_value(value: object) -> JsonValue:
    """Convert a tool argument or output value to a JSON-compatible value."""
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, Mapping):
        return {str(key): to_json_value(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set | frozenset):
        return [to_json_value(item) for item in value]
    return str(value)


def _pairs(pairs: tuple[tuple[str, object], ...] | None) -> dict[str, JsonValue]:
    return {} if pairs is None else {name: to_json_value(item) for name, item in pairs}


# -- errors ---------------------------------------------------------------------------


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, JsonValue] | None = None


class ErrorResponse(BaseModel):
    """Structured error envelope used by every non-2xx response."""

    error: ErrorBody


# -- runs -----------------------------------------------------------------------------


class StartRunRequest(BaseModel):
    prompt: str


class ApprovalDecisionRequest(BaseModel):
    """A person's explicit decision on the run's pending tool approval request."""

    decision: Literal["approved", "rejected"]
    reason: str | None = Field(default=None, max_length=1000)


class PendingApprovalModel(BaseModel):
    tool_name: str
    arguments: dict[str, JsonValue]
    invocation_id: str | None
    reason: str | None

    @classmethod
    def from_core(cls, pending: PendingApproval) -> PendingApprovalModel:
        return cls(
            tool_name=pending.tool_name,
            arguments=_pairs(pending.arguments),
            invocation_id=pending.invocation_id,
            reason=pending.reason,
        )


class ToolErrorModel(BaseModel):
    error_type: str
    message: str


class ToolResultModel(BaseModel):
    tool_name: str
    invocation_id: str | None
    arguments: dict[str, JsonValue]
    status: str
    output: dict[str, JsonValue] | None
    error: ToolErrorModel | None

    @classmethod
    def from_core(cls, result: ToolResult) -> ToolResultModel:
        return cls(
            tool_name=result.invocation.tool_name,
            invocation_id=result.invocation.invocation_id,
            arguments=_pairs(result.invocation.arguments),
            status=str(result.status),
            output=None if result.output is None else _pairs(result.output),
            error=None
            if result.error is None
            else ToolErrorModel(**dataclasses.asdict(result.error)),
        )


class ToolTraceModel(BaseModel):
    tool_name: str
    invocation_id: str | None
    arguments: dict[str, JsonValue]
    policy_decision: str | None
    approval_decision: str | None
    status: str
    output: dict[str, JsonValue] | None
    error: ToolErrorModel | None

    @classmethod
    def from_core(cls, trace: ToolExecutionTrace) -> ToolTraceModel:
        return cls(
            tool_name=trace.invocation.tool_name,
            invocation_id=trace.invocation.invocation_id,
            arguments=_pairs(trace.invocation.arguments),
            policy_decision=None if trace.policy_decision is None else str(trace.policy_decision),
            approval_decision=(
                None if trace.approval_decision is None else str(trace.approval_decision)
            ),
            status=str(trace.status),
            output=None if trace.output is None else _pairs(trace.output),
            error=None
            if trace.error is None
            else ToolErrorModel(**dataclasses.asdict(trace.error)),
        )


class RunEventModel(BaseModel):
    """One run event; ``payload`` holds the fields of the typed event named by ``kind``."""

    run_id: str
    sequence: int
    timestamp: float
    kind: str
    payload: dict[str, JsonValue]

    @classmethod
    def from_core(cls, event: RunEvent) -> RunEventModel:
        payload = {
            field.name: to_json_value(getattr(event.payload, field.name))
            for field in dataclasses.fields(event.payload)
        }
        return cls(
            run_id=event.run_id,
            sequence=event.sequence,
            timestamp=event.timestamp,
            kind=event.kind,
            payload=payload,
        )


class RunSummaryModel(BaseModel):
    run_id: str
    prompt: str
    model_id: str
    max_model_iterations: int
    status: RunStatus
    started_at: float
    finished_at: float | None
    pending_approval: PendingApprovalModel | None
    model_iterations: int
    final_response: str | None
    outcome: str | None
    error_phase: str | None
    error_message: str | None

    @classmethod
    def from_core(cls, record: RunRecord) -> RunSummaryModel:
        return cls(
            run_id=record.run_id,
            prompt=record.prompt,
            model_id=record.model_id,
            max_model_iterations=record.max_model_iterations,
            status=record.status,
            started_at=record.started_at,
            finished_at=record.finished_at,
            pending_approval=(
                None
                if record.pending_approval is None
                else PendingApprovalModel.from_core(record.pending_approval)
            ),
            model_iterations=record.model_iterations,
            final_response=record.final_response,
            outcome=None if record.result is None else str(record.result.outcome),
            error_phase=record.error_phase,
            error_message=record.error_message,
        )


class RunDetailModel(RunSummaryModel):
    tool_results: list[ToolResultModel]
    traces: list[ToolTraceModel]
    events: list[RunEventModel]

    @classmethod
    def from_core(cls, record: RunRecord) -> RunDetailModel:
        return cls(
            **RunSummaryModel.from_core(record).model_dump(),
            tool_results=[ToolResultModel.from_core(item) for item in record.tool_results],
            traces=[ToolTraceModel.from_core(item) for item in record.traces],
            events=[RunEventModel.from_core(item) for item in record.events],
        )


class RunListResponse(BaseModel):
    runs: list[RunSummaryModel]


# -- sources --------------------------------------------------------------------------


class DiagnosticModel(BaseModel):
    code: str
    message: str
    location: dict[str, JsonValue] | None

    @classmethod
    def from_core(cls, diagnostic: ProcessingDiagnostic) -> DiagnosticModel:
        location = diagnostic.location
        return cls(
            code=str(diagnostic.code),
            message=diagnostic.message,
            location=None if location is None else to_json_value(dataclasses.asdict(location)),  # type: ignore[arg-type]
        )


class SourceModel(BaseModel):
    source_id: str
    source_name: str
    source_kind: str
    content_sha256: str
    chunk_count: int
    diagnostics: list[DiagnosticModel]

    @classmethod
    def from_core(cls, source: SourceIndexRevision) -> SourceModel:
        return cls(
            source_id=source.source_id,
            source_name=source.source_name,
            source_kind=source.source_kind,
            content_sha256=source.content_sha256,
            chunk_count=len(source.chunk_ids),
            diagnostics=[DiagnosticModel.from_core(item) for item in source_diagnostics(source)],
        )


class SourceListResponse(BaseModel):
    preloaded: list[SourceModel]
    uploaded: list[SourceModel]

    @classmethod
    def from_core(cls, listing: SourceListing) -> SourceListResponse:
        return cls(
            preloaded=[SourceModel.from_core(item) for item in listing.preloaded],
            uploaded=[SourceModel.from_core(item) for item in listing.uploaded],
        )


class IngestionOutcomeModel(BaseModel):
    source_id: str
    status: str
    chunk_count: int
    previous_chunk_count: int
    diagnostics: list[DiagnosticModel]
    error_phase: str | None
    error_message: str | None
    requires_recovery: bool
    recovered: bool

    @classmethod
    def from_core(cls, outcome: IngestionOutcome) -> IngestionOutcomeModel:
        return cls(
            source_id=outcome.source_id,
            status=str(outcome.status),
            chunk_count=outcome.chunk_count,
            previous_chunk_count=outcome.previous_chunk_count,
            diagnostics=[DiagnosticModel.from_core(item) for item in outcome.diagnostics],
            error_phase=outcome.error_phase,
            error_message=outcome.error_message,
            requires_recovery=outcome.requires_recovery,
            recovered=outcome.recovered,
        )


class IngestionReportResponse(BaseModel):
    source_ids: list[str]
    source_names: list[str]
    chunk_count: int
    outcomes: list[IngestionOutcomeModel]

    @classmethod
    def from_core(cls, report: IngestionReport) -> IngestionReportResponse:
        return cls(
            source_ids=list(report.source_ids),
            source_names=list(report.source_names),
            chunk_count=report.chunk_count,
            outcomes=[IngestionOutcomeModel.from_core(item) for item in report.outcomes],
        )


class DeleteSourceResponse(BaseModel):
    outcome: IngestionOutcomeModel


class ClearUploadsResponse(BaseModel):
    deleted_source_ids: list[str]


class RecoverSourcesResponse(BaseModel):
    outcomes: list[IngestionOutcomeModel]


# -- system ---------------------------------------------------------------------------


class ToolDescriptionModel(BaseModel):
    name: str
    description: str


class PromptPresetModel(BaseModel):
    name: str
    prompt: str


class DependencyStatusModel(BaseModel):
    name: str
    state: str
    detail: str


class SystemResponse(BaseModel):
    """Read-only description of the composed application and its effective configuration."""

    settings: dict[str, JsonValue]
    tools: list[ToolDescriptionModel]
    prompt_presets: list[PromptPresetModel]
    dependencies: list[DependencyStatusModel]
    active_run_id: str | None

    @classmethod
    def from_core(cls, system: SystemDescription) -> SystemResponse:
        return cls(
            settings={
                key: to_json_value(value)
                for key, value in dataclasses.asdict(system.settings).items()
            },
            tools=[
                ToolDescriptionModel(name=t.name, description=t.description) for t in system.tools
            ],
            prompt_presets=[PromptPresetModel(name=n, prompt=p) for n, p in system.prompt_presets],
            dependencies=[
                DependencyStatusModel(name=d.name, state=d.state, detail=d.detail)
                for d in system.dependencies
            ],
            active_run_id=system.active_run_id,
        )
