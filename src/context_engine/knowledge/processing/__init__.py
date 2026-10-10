"""Public deterministic source-processing contracts and composition helpers."""

from context_engine.knowledge.processing.adapters import to_document
from context_engine.knowledge.processing.contracts import (
    BlockKind,
    BlockLocation,
    DiagnosticCode,
    ExtractedBlock,
    ProcessedSource,
    ProcessingDiagnostic,
    ProcessingError,
    ProcessingErrorCode,
    ProcessingLimits,
    SourceFormat,
    SourceInput,
    SourceProvenance,
)
from context_engine.knowledge.processing.pdf import process_pdf
from context_engine.knowledge.processing.readers import process_source

__all__ = [
    "BlockKind",
    "BlockLocation",
    "DiagnosticCode",
    "ExtractedBlock",
    "ProcessedSource",
    "ProcessingDiagnostic",
    "ProcessingError",
    "ProcessingErrorCode",
    "ProcessingLimits",
    "SourceFormat",
    "SourceInput",
    "SourceProvenance",
    "process_source",
    "process_pdf",
    "to_document",
]
