"""Domain facade shared by the embedded Python API and HTTP adapters."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from uuid import uuid4

from context_engine.agent import AgentRuntime
from context_engine.core.prompts import PROMPT_PRESETS, SYSTEM_PROMPT
from context_engine.core.runs import (
    InvalidPromptError,
    RunRecord,
    RunRegistry,
    RunStatus,
    derive_error,
    derive_run_status,
)
from context_engine.core.settings import ApplicationSettings
from context_engine.core.sources import DocumentCatalog, IngestionReport, UploadCandidate
from context_engine.knowledge.ingestion import IngestionOutcome
from context_engine.models import ModelGateway
from context_engine.observability import RunEvent, RunEventEmitter
from context_engine.retrieval.source_store import SourceIndexRevision
from context_engine.tools import AllowAllToolPolicy, ToolRegistry, ToolRuntime


@dataclass(frozen=True, slots=True)
class ToolDescription:
    """Name and description of one registered tool."""

    name: str
    description: str


@dataclass(frozen=True, slots=True)
class DependencyStatus:
    """Composition-time state of one dependency. This is not continuous health monitoring."""

    name: str
    state: str
    detail: str


@dataclass(frozen=True, slots=True)
class SystemDescription:
    """Read-only description of the composed application."""

    settings: ApplicationSettings
    tools: tuple[ToolDescription, ...]
    prompt_presets: tuple[tuple[str, str], ...]
    dependencies: tuple[DependencyStatus, ...]
    active_run_id: str | None


@dataclass(frozen=True, slots=True)
class SourceListing:
    """Indexed sources grouped by how they entered the index."""

    preloaded: tuple[SourceIndexRevision, ...]
    uploaded: tuple[SourceIndexRevision, ...]


class _RegistrySink:
    """Forwards run events to the registry record of their run."""

    def __init__(self, registry: RunRegistry) -> None:
        self._registry = registry

    def record(self, event: RunEvent) -> None:
        self._registry.append_event(event)


class ContextEngineApplication:
    """Runs prompts and manages sources through the runtime and policy boundaries.

    Runs are held in memory for the lifetime of the object and one run is active at a
    time. Each run executes on its own worker thread and records its events as they occur.
    """

    def __init__(
        self,
        *,
        settings: ApplicationSettings,
        document_catalog: DocumentCatalog,
        model_gateway: ModelGateway,
        tool_registry: ToolRegistry,
        wall_clock: Callable[[], float] = time.time,
    ) -> None:
        self.settings = settings
        self.documents = document_catalog
        self._model_gateway = model_gateway
        self._tool_registry = tool_registry
        self._wall_clock = wall_clock
        self._runs = RunRegistry()

    # -- sources ---------------------------------------------------------------------

    def prepare(self) -> IngestionReport:
        """Recover interrupted index writes and ingest the idempotent preloaded corpus."""
        return self.documents.prepare()

    def recover_source_index(self) -> tuple[IngestionOutcome, ...]:
        """Recover interrupted index writes and return the recovery outcomes."""
        self.documents.prepare()
        return self.documents.recovery_outcomes

    def list_sources(self) -> SourceListing:
        """Return the indexed preloaded and uploaded sources."""
        return SourceListing(
            preloaded=self.documents.preloaded_sources,
            uploaded=self.documents.uploaded_sources,
        )

    def ingest_uploads(self, candidates: Sequence[UploadCandidate]) -> IngestionReport:
        """Validate and ingest uploaded source revisions."""
        return self.documents.ingest_uploads(candidates)

    def delete_upload(self, source_id: str) -> IngestionOutcome:
        """Delete one indexed uploaded source."""
        return self.documents.delete_upload(source_id)

    def clear_uploads(self) -> tuple[str, ...]:
        """Delete every uploaded source and return the deleted source ids."""
        return self.documents.clear_uploads()

    # -- system ----------------------------------------------------------------------

    def describe_system(self) -> SystemDescription:
        """Return the effective configuration, tools, presets and dependency states."""
        return SystemDescription(
            settings=self.settings,
            tools=tuple(
                ToolDescription(name=tool.name, description=tool.description)
                for tool in self._tool_registry.list_tools()
            ),
            prompt_presets=tuple(PROMPT_PRESETS.items()),
            dependencies=(
                DependencyStatus("model", "configured", self.settings.model_id),
                DependencyStatus("embeddings", "ready", self.settings.embedding_model_id),
                DependencyStatus("vector_store", "ready", self.settings.qdrant_url),
            ),
            active_run_id=self._runs.active_run_id,
        )

    # -- runs ------------------------------------------------------------------------

    def start_run(self, prompt: str) -> RunRecord:
        """Start a run on a worker thread and return its initial record.

        Raises ``InvalidPromptError`` for a blank prompt and ``RunAlreadyActiveError``
        while another run is active.
        """
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise InvalidPromptError("Prompt must contain non-whitespace characters.")
        record = RunRecord(
            run_id=uuid4().hex,
            prompt=normalized_prompt,
            model_id=self.settings.model_id,
            max_model_iterations=self.settings.max_model_iterations,
            status=RunStatus.RUNNING,
            started_at=self._wall_clock(),
        )
        self._runs.begin(record)
        threading.Thread(
            target=self._execute,
            args=(record.run_id, normalized_prompt),
            name=f"context-engine-run-{record.run_id[:8]}",
            daemon=True,
        ).start()
        return record

    def run_prompt(self, prompt: str, *, timeout: float | None = None) -> RunRecord:
        """Start a run and block until it finishes or ``timeout`` elapses."""
        record = self.start_run(prompt)
        return self._runs.wait_until_finished(record.run_id, timeout=timeout)

    def get_run(self, run_id: str) -> RunRecord:
        """Return the current snapshot of one run."""
        return self._runs.get(run_id)

    def list_runs(self) -> tuple[RunRecord, ...]:
        """Return every run of this process in start order."""
        return self._runs.list_runs()

    def wait_for_run_events(
        self, run_id: str, *, after_sequence: int = 0, timeout: float | None = None
    ) -> tuple[tuple[RunEvent, ...], bool]:
        """Return events newer than ``after_sequence`` and whether the run has finished."""
        return self._runs.wait_for_events(run_id, after_sequence=after_sequence, timeout=timeout)

    def _execute(self, run_id: str, prompt: str) -> None:
        emitter = RunEventEmitter(
            _RegistrySink(self._runs), run_id=run_id, wall_clock=self._wall_clock
        )
        tool_runtime = ToolRuntime(self._tool_registry, policy=AllowAllToolPolicy(), events=emitter)
        runtime = AgentRuntime(
            model_gateway=self._model_gateway, tool_runtime=tool_runtime, events=emitter
        )
        try:
            result = runtime.run(
                model_id=self.settings.model_id,
                user_prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                max_output_tokens=self.settings.max_output_tokens,
                temperature=0.0,
                max_model_iterations=self.settings.max_model_iterations,
            )
        except Exception as exc:  # defensive application boundary
            message = f"{type(exc).__name__}: {exc}"
            self._runs.finish(
                run_id,
                lambda record: replace(
                    record,
                    status=RunStatus.FAILED,
                    finished_at=self._wall_clock(),
                    tool_results=runtime.tool_results,
                    traces=tool_runtime.execution_traces,
                    error_phase="agent_runtime",
                    error_message=message,
                ),
            )
            return
        traces = tool_runtime.execution_traces
        status = derive_run_status(result, traces)
        error_phase, error_message = derive_error(result, traces, status)
        self._runs.finish(
            run_id,
            lambda record: replace(
                record,
                status=status,
                finished_at=self._wall_clock(),
                result=result,
                tool_results=runtime.tool_results,
                traces=traces,
                error_phase=error_phase,
                error_message=error_message,
            ),
        )
