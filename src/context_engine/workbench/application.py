"""Streamlit workbench adapter over the core application facade."""

from __future__ import annotations

from context_engine.core.application import ContextEngineApplication
from context_engine.core.composition import (
    ApplicationDependencyError as WorkbenchDependencyError,
)
from context_engine.core.composition import (
    build_live_application,
    configure_evidence_selection,
    configure_reranking,
)
from context_engine.core.prompts import PROMPT_PRESETS, SYSTEM_PROMPT
from context_engine.core.runs import InvalidPromptError, RunAlreadyActiveError
from context_engine.models import ModelGateway
from context_engine.tools import ToolRegistry
from context_engine.workbench.config import WorkbenchSettings
from context_engine.workbench.documents import DocumentCatalog, UploadCandidate
from context_engine.workbench.presentation import (
    WorkbenchRunView,
    build_failed_run_view,
    build_run_view,
)

__all__ = [
    "PROMPT_PRESETS",
    "SYSTEM_PROMPT",
    "WorkbenchApplication",
    "WorkbenchDependencyError",
    "build_live_workbench",
    "configure_evidence_selection",
    "configure_reranking",
]


class WorkbenchApplication:
    """Presents core runs as workbench display models for the Streamlit UI."""

    def __init__(
        self,
        *,
        settings: WorkbenchSettings,
        document_catalog: DocumentCatalog,
        model_gateway: ModelGateway,
        tool_registry: ToolRegistry,
    ) -> None:
        self._core = ContextEngineApplication(
            settings=settings,
            document_catalog=document_catalog,
            model_gateway=model_gateway,
            tool_registry=tool_registry,
        )
        self.settings = settings
        self.documents = document_catalog

    @classmethod
    def from_core(cls, core: ContextEngineApplication) -> WorkbenchApplication:
        """Wrap an already composed core application."""
        instance = cls.__new__(cls)
        instance._core = core
        instance.settings = core.settings
        instance.documents = core.documents
        return instance

    @property
    def core(self) -> ContextEngineApplication:
        """Return the wrapped core application."""
        return self._core

    def prepare(self) -> None:
        """Prepare the idempotent preloaded corpus."""
        self._core.prepare()

    def ingest_uploads(self, candidates: tuple[UploadCandidate, ...]) -> tuple[str, ...]:
        """Ingest source revisions and return stable source IDs, not passage IDs."""
        return self._core.ingest_uploads(candidates).source_ids

    def clear_uploads(self) -> tuple[str, ...]:
        """Clear only uploads tracked by this workbench."""
        return self._core.clear_uploads()

    def run_prompt(self, prompt: str) -> WorkbenchRunView:
        """Execute every prompt through the same live Agent Runtime path."""
        try:
            record = self._core.run_prompt(prompt)
        except InvalidPromptError as exc:
            return build_failed_run_view(prompt=prompt, phase="prompt_validation", message=str(exc))
        except RunAlreadyActiveError as exc:
            return build_failed_run_view(
                prompt=prompt.strip(), phase="agent_runtime", message=str(exc)
            )
        if record.result is None:
            return build_failed_run_view(
                prompt=record.prompt,
                phase=record.error_phase or "agent_runtime",
                message=record.error_message or "Run ended without a runtime result.",
            )
        return build_run_view(
            prompt=record.prompt,
            result=record.result,
            tool_results=record.tool_results,
            traces=record.traces,
        )


def build_live_workbench(settings: WorkbenchSettings | None = None) -> WorkbenchApplication:
    """Compose the live core application and wrap it for the workbench."""
    return WorkbenchApplication.from_core(build_live_application(settings))
