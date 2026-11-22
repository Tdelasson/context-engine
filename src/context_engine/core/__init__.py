"""Core application layer: the domain facade, composition, settings, sources and runs."""

from context_engine.core.application import (
    ContextEngineApplication,
    DependencyStatus,
    SourceListing,
    SystemDescription,
    ToolDescription,
)
from context_engine.core.composition import ApplicationDependencyError, build_live_application
from context_engine.core.prompts import PROMPT_PRESETS, SYSTEM_PROMPT
from context_engine.core.runs import (
    InvalidPromptError,
    NoPendingApprovalError,
    PendingApproval,
    RunAlreadyActiveError,
    RunRecord,
    RunRegistry,
    RunStatus,
    UnknownRunError,
)
from context_engine.core.settings import ApplicationConfigurationError, ApplicationSettings
from context_engine.core.sources import (
    DocumentCatalog,
    IngestionReport,
    SourceCatalogError,
    UploadCandidate,
    UploadLimits,
)

__all__ = [
    "PROMPT_PRESETS",
    "SYSTEM_PROMPT",
    "ApplicationConfigurationError",
    "ApplicationDependencyError",
    "ApplicationSettings",
    "ContextEngineApplication",
    "DependencyStatus",
    "DocumentCatalog",
    "IngestionReport",
    "InvalidPromptError",
    "NoPendingApprovalError",
    "PendingApproval",
    "RunAlreadyActiveError",
    "RunRecord",
    "RunRegistry",
    "RunStatus",
    "SourceCatalogError",
    "SourceListing",
    "SystemDescription",
    "ToolDescription",
    "UnknownRunError",
    "UploadCandidate",
    "UploadLimits",
    "build_live_application",
]
