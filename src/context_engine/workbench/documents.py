"""Deterministic preloaded-document and upload adapters for the workbench."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from hashlib import sha256
from importlib import resources
from pathlib import PurePath

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
from context_engine.retrieval import Document, Ingestor, VectorStore

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
    """Structured result for one document-ingestion operation."""

    document_ids: tuple[str, ...]
    source_names: tuple[str, ...]


def load_preloaded_documents() -> tuple[Document, ...]:
    """Load the version-controlled project corpus as deterministic M4 documents."""
    package_root = resources.files(_DEMO_PACKAGE)
    documents: list[Document] = []
    for entry in sorted(package_root.iterdir(), key=lambda item: item.name):
        if not entry.is_file() or PurePath(entry.name).suffix.lower() not in _SUPPORTED_SUFFIXES:
            continue
        try:
            processed = process_source(
                SourceInput(
                    source_id=f"preloaded-{PurePath(entry.name).stem}",
                    source_name=entry.name,
                    source_kind="preloaded",
                    content=entry.read_bytes(),
                    format=(
                        SourceFormat.PDF
                        if entry.name.endswith(".pdf")
                        else SourceFormat.MARKDOWN
                        if entry.name.endswith(".md")
                        else SourceFormat.TEXT
                    ),
                )
            )
        except ProcessingError as exc:
            raise WorkbenchDocumentError(str(exc)) from exc
        documents.append(to_document(processed))
    if not documents:
        raise WorkbenchDocumentError("No preloaded workbench project documents were found.")
    return tuple(documents)


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
    """Own workbench-specific ingestion state without leaking storage details to the UI."""

    def __init__(
        self,
        *,
        ingestor: Ingestor,
        vector_store: VectorStore,
        upload_limits: UploadLimits | None = None,
        preloaded_documents: Sequence[Document] | None = None,
    ) -> None:
        self._ingestor = ingestor
        self._vector_store = vector_store
        self._upload_limits = upload_limits or UploadLimits()
        self._preloaded_documents = tuple(preloaded_documents or load_preloaded_documents())
        self._uploaded_documents: dict[str, Document] = {}
        self._prepared = False
        self._upload_diagnostics: dict[str, tuple[ProcessingDiagnostic, ...]] = {}

    @property
    def preloaded_documents(self) -> tuple[Document, ...]:
        return self._preloaded_documents

    @property
    def uploaded_documents(self) -> tuple[Document, ...]:
        return tuple(self._uploaded_documents[key] for key in sorted(self._uploaded_documents))

    @property
    def upload_diagnostics(self) -> tuple[tuple[str, ProcessingDiagnostic], ...]:
        return tuple(
            (name, diagnostic)
            for name in sorted(self._upload_diagnostics)
            for diagnostic in self._upload_diagnostics[name]
        )

    def prepare(self) -> IngestionReport:
        """Ingest the preloaded corpus once per application composition."""
        if not self._prepared:
            self._ingestor.ingest_documents(self._preloaded_documents)
            self._prepared = True
        return _report_for(self._preloaded_documents)

    def ingest_uploads(self, candidates: Sequence[UploadCandidate]) -> IngestionReport:
        """Validate a batch before ingesting it and track only successfully ingested uploads."""
        processed = tuple(
            process_uploaded_source(candidate, self._upload_limits) for candidate in candidates
        )
        documents = tuple(to_document(source) for source in processed)
        distinct_documents = {document.document_id: document for document in documents}
        projected_ids = set(self._uploaded_documents) | set(distinct_documents)
        if len(projected_ids) > self._upload_limits.max_files:
            raise WorkbenchDocumentError(
                f"At most {self._upload_limits.max_files} uploaded documents are allowed."
            )
        self._ingestor.ingest_documents(tuple(distinct_documents.values()))
        self._uploaded_documents.update(distinct_documents)
        self._upload_diagnostics.update(
            {source.provenance.source_name: source.diagnostics for source in processed}
        )
        return _report_for(tuple(distinct_documents.values()))

    def clear_uploads(self) -> tuple[str, ...]:
        """Delete uploaded records while preserving every preloaded project record."""
        uploaded_ids = tuple(sorted(self._uploaded_documents))
        self._vector_store.delete(uploaded_ids)
        self._uploaded_documents.clear()
        self._upload_diagnostics.clear()
        return uploaded_ids


def _report_for(documents: Sequence[Document]) -> IngestionReport:
    return IngestionReport(
        document_ids=tuple(document.document_id for document in documents),
        source_names=tuple(
            str(document.metadata_as_mapping().get("source_name", document.document_id))
            for document in documents
        ),
    )
