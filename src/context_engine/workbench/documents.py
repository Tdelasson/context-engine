"""Workbench names for the core source catalog.

The catalog moved to ``context_engine.core.sources``; these aliases keep the Streamlit
workbench and its tests working until it is removed.
"""

from context_engine.core.sources import (
    DocumentCatalog,
    IngestionReport,
    UploadCandidate,
    UploadLimits,
    construct_uploaded_document,
    load_preloaded_documents,
    load_preloaded_sources,
    process_uploaded_source,
)
from context_engine.core.sources import SourceCatalogError as WorkbenchDocumentError

__all__ = [
    "DocumentCatalog",
    "IngestionReport",
    "UploadCandidate",
    "UploadLimits",
    "WorkbenchDocumentError",
    "construct_uploaded_document",
    "load_preloaded_documents",
    "load_preloaded_sources",
    "process_uploaded_source",
]
