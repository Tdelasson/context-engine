"""Deterministic demo-document and upload adapters for the workbench."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from hashlib import sha256
from importlib import resources
from pathlib import PurePath

from context_engine.retrieval import Document, Ingestor, VectorStore

_DEMO_PACKAGE = "context_engine.workbench.demo_documents"
_SUPPORTED_SUFFIXES = frozenset({".md", ".txt"})


class WorkbenchDocumentError(ValueError):
    """Raised when a workbench document cannot be safely constructed or managed."""


@dataclass(frozen=True, slots=True)
class UploadLimits:
    """Explicit resource limits for meeting-time uploads."""

    max_files: int = 5
    max_bytes_per_file: int = 256 * 1024

    def __post_init__(self) -> None:
        if self.max_files <= 0 or self.max_bytes_per_file <= 0:
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
    """Load the version-controlled demo corpus as deterministic M4 documents."""
    package_root = resources.files(_DEMO_PACKAGE)
    documents: list[Document] = []
    for entry in sorted(package_root.iterdir(), key=lambda item: item.name):
        if not entry.is_file() or PurePath(entry.name).suffix.lower() not in _SUPPORTED_SUFFIXES:
            continue
        content = entry.read_text(encoding="utf-8")
        documents.append(
            Document.from_mapping(
                document_id=f"preloaded-{PurePath(entry.name).stem}",
                content=content,
                metadata={"source_kind": "preloaded", "source_name": entry.name},
            )
        )
    if not documents:
        raise WorkbenchDocumentError("No preloaded workbench demo documents were found.")
    return tuple(documents)


def construct_uploaded_document(candidate: UploadCandidate, limits: UploadLimits) -> Document:
    """Validate and convert one upload into one deterministic M4 document."""
    normalized_name = PurePath(candidate.name).name
    if not normalized_name or normalized_name != candidate.name:
        raise WorkbenchDocumentError("Uploaded file name must not contain a path.")
    suffix = PurePath(normalized_name).suffix.lower()
    if suffix not in _SUPPORTED_SUFFIXES:
        raise WorkbenchDocumentError("Only UTF-8 .txt and .md files are supported.")
    if not candidate.content:
        raise WorkbenchDocumentError(f"Uploaded file '{normalized_name}' is empty.")
    if len(candidate.content) > limits.max_bytes_per_file:
        raise WorkbenchDocumentError(
            f"Uploaded file '{normalized_name}' exceeds {limits.max_bytes_per_file} bytes."
        )
    try:
        decoded_content = candidate.content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise WorkbenchDocumentError(
            f"Uploaded file '{normalized_name}' must contain valid UTF-8 text."
        ) from exc
    if not decoded_content.strip():
        raise WorkbenchDocumentError(f"Uploaded file '{normalized_name}' contains only whitespace.")
    digest = sha256(normalized_name.encode("utf-8") + b"\0" + candidate.content).hexdigest()[:20]
    return Document.from_mapping(
        document_id=f"uploaded-{digest}",
        content=decoded_content,
        metadata={"source_kind": "uploaded", "source_name": normalized_name},
    )


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

    @property
    def preloaded_documents(self) -> tuple[Document, ...]:
        return self._preloaded_documents

    @property
    def uploaded_documents(self) -> tuple[Document, ...]:
        return tuple(self._uploaded_documents[key] for key in sorted(self._uploaded_documents))

    def prepare(self) -> IngestionReport:
        """Ingest the preloaded corpus once per application composition."""
        if not self._prepared:
            self._ingestor.ingest_documents(self._preloaded_documents)
            self._prepared = True
        return _report_for(self._preloaded_documents)

    def ingest_uploads(self, candidates: Sequence[UploadCandidate]) -> IngestionReport:
        """Validate a batch before ingesting it and track only successfully ingested uploads."""
        documents = tuple(
            construct_uploaded_document(candidate, self._upload_limits) for candidate in candidates
        )
        distinct_documents = {document.document_id: document for document in documents}
        projected_ids = set(self._uploaded_documents) | set(distinct_documents)
        if len(projected_ids) > self._upload_limits.max_files:
            raise WorkbenchDocumentError(
                f"At most {self._upload_limits.max_files} uploaded documents are allowed."
            )
        self._ingestor.ingest_documents(tuple(distinct_documents.values()))
        self._uploaded_documents.update(distinct_documents)
        return _report_for(tuple(distinct_documents.values()))

    def clear_uploads(self) -> tuple[str, ...]:
        """Delete uploaded records while preserving every preloaded demo record."""
        uploaded_ids = tuple(sorted(self._uploaded_documents))
        self._vector_store.delete(uploaded_ids)
        self._uploaded_documents.clear()
        return uploaded_ids


def _report_for(documents: Sequence[Document]) -> IngestionReport:
    return IngestionReport(
        document_ids=tuple(document.document_id for document in documents),
        source_names=tuple(
            str(document.metadata_as_mapping().get("source_name", document.document_id))
            for document in documents
        ),
    )
