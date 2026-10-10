"""Deterministic preloaded-document and upload adapters for the workbench."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from hashlib import sha256
from importlib import resources
from pathlib import PurePath

from context_engine.knowledge.ingestion import (
    IngestionOutcome,
    IngestionStatus,
    SourceIngestionCoordinator,
    source_diagnostics,
)
from context_engine.knowledge.processing import (
    ProcessedSource,
    ProcessingDiagnostic,
    ProcessingError,
    ProcessingLimits,
    SourceFormat,
    SourceInput,
    process_source,
    to_document,
)
from context_engine.retrieval import Document
from context_engine.retrieval.source_store import SourceIndexRevision

_DEMO_PACKAGE = "context_engine.workbench.demo_documents"
_SUPPORTED_SUFFIXES = frozenset({".md", ".txt", ".pdf"})


class WorkbenchDocumentError(ValueError):
    """Raised when a workbench document cannot be safely constructed or managed."""


@dataclass(frozen=True, slots=True)
class UploadLimits:
    """Explicit resource limits for workbench uploads."""

    max_files: int = 5
    max_bytes_per_file: int = 256 * 1024
    max_pdf_bytes_per_file: int = 10 * 1024 * 1024
    max_pdf_pages: int = 100
    max_pdf_text_characters: int = 1024 * 1024

    def __post_init__(self) -> None:
        if any(
            type(value) is not int or value <= 0
            for value in (
                self.max_files,
                self.max_bytes_per_file,
                self.max_pdf_bytes_per_file,
                self.max_pdf_pages,
                self.max_pdf_text_characters,
            )
        ):
            raise WorkbenchDocumentError("Upload limits must be greater than zero.")


@dataclass(frozen=True, slots=True)
class UploadCandidate:
    """Framework-independent uploaded file payload."""

    name: str
    content: bytes


@dataclass(frozen=True, slots=True)
class IngestionReport:
    """Source-level outcomes; retrieved document IDs refer to chunks."""

    source_ids: tuple[str, ...]
    source_names: tuple[str, ...]
    outcomes: tuple[IngestionOutcome, ...]

    @property
    def chunk_count(self) -> int:
        return sum(outcome.chunk_count for outcome in self.outcomes)


def load_preloaded_sources() -> tuple[SourceInput, ...]:
    package_root = resources.files(_DEMO_PACKAGE)
    sources = tuple(
        SourceInput(
            source_id=f"preloaded-{sha256(entry.name.encode()).hexdigest()}",
            source_name=entry.name,
            source_kind="preloaded",
            content=entry.read_bytes(),
            format=_format_for(entry.name),
        )
        for entry in sorted(package_root.iterdir(), key=lambda item: item.name)
        if entry.is_file() and PurePath(entry.name).suffix.lower() in _SUPPORTED_SUFFIXES
    )

    if not sources:
        raise WorkbenchDocumentError("No preloaded workbench project sources were found.")
    return sources


def _format_for(name: str) -> SourceFormat:
    suffix = PurePath(name).suffix.lower()
    return (
        SourceFormat.PDF
        if suffix == ".pdf"
        else SourceFormat.MARKDOWN
        if suffix == ".md"
        else SourceFormat.TEXT
    )


def load_preloaded_documents() -> tuple[Document, ...]:
    """Load the version-controlled project corpus as deterministic M4 documents."""
    try:
        documents = tuple(
            to_document(process_source(source)) for source in load_preloaded_sources()
        )
    except ProcessingError as exc:
        raise WorkbenchDocumentError(str(exc)) from exc
    if not documents:
        raise WorkbenchDocumentError("No preloaded workbench project documents were found.")
    return documents


def process_uploaded_source(candidate: UploadCandidate, limits: UploadLimits) -> ProcessedSource:
    """Validate an upload and retain extraction diagnostics and page blocks."""
    normalized_name = PurePath(candidate.name).name
    if not normalized_name or normalized_name != candidate.name:
        raise WorkbenchDocumentError("Uploaded file name must not contain a path.")
    suffix = PurePath(normalized_name).suffix.lower()
    if suffix not in _SUPPORTED_SUFFIXES:
        raise WorkbenchDocumentError(
            "Only UTF-8 .txt/.md files and text-based .pdf files are supported."
        )
    # Filename is the logical identity in this UI namespace; bytes identify its revision.
    digest = sha256(normalized_name.encode("utf-8")).hexdigest()
    try:
        processed = process_source(
            SourceInput(
                source_id=f"uploaded-{digest}",
                source_name=normalized_name,
                source_kind="uploaded",
                content=candidate.content,
                format=(
                    SourceFormat.PDF
                    if suffix == ".pdf"
                    else SourceFormat.MARKDOWN
                    if suffix == ".md"
                    else SourceFormat.TEXT
                ),
            ),
            ProcessingLimits(
                max_bytes=(
                    limits.max_pdf_bytes_per_file if suffix == ".pdf" else limits.max_bytes_per_file
                ),
                max_text_characters=(
                    limits.max_pdf_text_characters
                    if suffix == ".pdf"
                    else limits.max_bytes_per_file
                ),
                max_pages=limits.max_pdf_pages,
            ),
        )
    except ProcessingError as exc:
        raise WorkbenchDocumentError(str(exc)) from exc
    return processed


def construct_uploaded_document(candidate: UploadCandidate, limits: UploadLimits) -> Document:
    """Convert an upload to the existing whole-document retrieval contract."""
    return to_document(process_uploaded_source(candidate, limits))


class DocumentCatalog:
    """Manage indexed sources through the durable ingestion coordinator."""

    def __init__(
        self,
        *,
        ingestion: SourceIngestionCoordinator,
        upload_limits: UploadLimits | None = None,
        preloaded_sources: Sequence[SourceInput] | None = None,
    ) -> None:
        self._ingestion = ingestion
        self._upload_limits = upload_limits or UploadLimits()
        self._preloaded = tuple(
            load_preloaded_sources() if preloaded_sources is None else preloaded_sources
        )
        self.last_report = IngestionReport((), (), ())
        self.recovery_outcomes: tuple[IngestionOutcome, ...] = ()

    @property
    def preloaded_sources(self) -> tuple[SourceIndexRevision, ...]:
        return tuple(
            source for source in self._ingestion.list_sources() if source.source_kind == "preloaded"
        )

    @property
    def uploaded_sources(self) -> tuple[SourceIndexRevision, ...]:
        return tuple(
            source for source in self._ingestion.list_sources() if source.source_kind == "uploaded"
        )

    @property
    def upload_diagnostics(self) -> tuple[tuple[str, ProcessingDiagnostic], ...]:
        return tuple(
            (source.source_name, diagnostic)
            for source in self.uploaded_sources
            for diagnostic in source_diagnostics(source)
        )

    def prepare(self) -> IngestionReport:
        self.recovery_outcomes = self._ingestion.recover()
        self._ensure_success(
            tuple(item for item in self.recovery_outcomes if item.requires_recovery)
        )
        outcomes = tuple(self._ingestion.ingest(source) for source in self._preloaded)
        self.last_report = IngestionReport(
            tuple(source.source_id for source in self._preloaded),
            tuple(source.source_name for source in self._preloaded),
            outcomes,
        )
        self._ensure_success(outcomes)
        return self.last_report

    def ingest_uploads(self, candidates: Sequence[UploadCandidate]) -> IngestionReport:
        # Validate every file before committing any member of the batch. Each source
        # has its own transaction; storage failures can leave earlier sources committed.
        processed = tuple(
            process_uploaded_source(candidate, self._upload_limits) for candidate in candidates
        )
        distinct = {source.provenance.source_id: source for source in processed}
        if len(distinct) != len(processed):
            raise WorkbenchDocumentError("Select each upload filename only once per batch.")
        projected = {source.source_id for source in self.uploaded_sources} | set(distinct)
        if len(projected) > self._upload_limits.max_files:
            raise WorkbenchDocumentError(
                f"At most {self._upload_limits.max_files} uploaded documents are allowed."
            )
        outcomes = []
        for source in distinct.values():
            outcome = self._ingestion.ingest_processed(source)
            outcomes.append(outcome)
            if outcome.status is IngestionStatus.FAILED:
                break
        attempted = tuple(distinct[item.source_id] for item in outcomes)
        self.last_report = IngestionReport(
            tuple(source.provenance.source_id for source in attempted),
            tuple(source.provenance.source_name for source in attempted),
            tuple(outcomes),
        )
        self._ensure_success(tuple(outcomes))
        return self.last_report

    def delete_upload(self, source_id: str) -> IngestionOutcome:
        source = next((item for item in self.uploaded_sources if item.source_id == source_id), None)
        if source is None:
            raise WorkbenchDocumentError("Only an indexed uploaded source can be deleted here.")
        outcome = self._ingestion.delete_source(source_id)
        self.last_report = IngestionReport((source_id,), (source.source_name,), (outcome,))
        self._ensure_success((outcome,))
        return outcome

    def clear_uploads(self) -> tuple[str, ...]:
        sources = self.uploaded_sources
        outcomes = []
        for source in sources:
            outcome = self._ingestion.delete_source(source.source_id)
            outcomes.append(outcome)
            if outcome.status is IngestionStatus.FAILED:
                break
        self.last_report = IngestionReport(
            tuple(item.source_id for item in outcomes),
            tuple(source.source_name for source in sources[: len(outcomes)]),
            tuple(outcomes),
        )
        self._ensure_success(tuple(outcomes))
        return tuple(item.source_id for item in outcomes)

    @staticmethod
    def _ensure_success(outcomes: tuple[IngestionOutcome, ...]) -> None:
        failed = next((item for item in outcomes if item.status is IngestionStatus.FAILED), None)
        if failed is not None:
            suffix = (
                " Restart/recover the index before searching or retrying."
                if failed.requires_recovery
                else ""
            )
            raise WorkbenchDocumentError(f"{failed.error_phase}: {failed.error_message}.{suffix}")
