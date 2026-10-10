"""Environment-backed configuration for the local workbench application."""

from __future__ import annotations

import os
from dataclasses import dataclass
from math import isfinite


class WorkbenchConfigurationError(ValueError):
    """Raised when workbench configuration is invalid."""


@dataclass(frozen=True, slots=True)
class WorkbenchSettings:
    """Typed local dependency and execution settings."""

    retrieval_strategy: str = "dense"
    lexical_collection_name: str = "context-engine-workbench-m5-bm25-v1"
    model_id: str = "llama3.2:1b"
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout_seconds: float = 30.0
    embedding_model_id: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_model_reference: str = "sentence-transformers/all-MiniLM-L6-v2"
    qdrant_url: str = "http://localhost:6333"
    qdrant_timeout_seconds: float = 5.0
    collection_name: str = "context-engine-workbench-m5-v1"
    chunk_max_input_tokens: int = 128
    chunk_overlap_tokens: int = 16
    max_uploads: int = 5
    max_upload_bytes: int = 256 * 1024
    max_output_tokens: int = 256
    max_model_iterations: int = 4
    max_pdf_upload_bytes: int = 10 * 1024 * 1024
    max_pdf_pages: int = 100
    max_pdf_text_characters: int = 1024 * 1024

    def __post_init__(self) -> None:
        if self.retrieval_strategy not in {"dense", "lexical"}:
            raise WorkbenchConfigurationError("retrieval_strategy must be dense or lexical.")
        string_fields = {
            "lexical_collection_name": self.lexical_collection_name,
            "model_id": self.model_id,
            "ollama_base_url": self.ollama_base_url,
            "embedding_model_id": self.embedding_model_id,
            "embedding_model_reference": self.embedding_model_reference,
            "qdrant_url": self.qdrant_url,
            "collection_name": self.collection_name,
        }
        empty_fields = tuple(name for name, value in string_fields.items() if not value.strip())
        if empty_fields:
            raise WorkbenchConfigurationError(
                f"Workbench settings must not be empty: {', '.join(empty_fields)}."
            )
        positive_numbers = {
            "ollama_timeout_seconds": self.ollama_timeout_seconds,
            "qdrant_timeout_seconds": self.qdrant_timeout_seconds,
            "max_uploads": self.max_uploads,
            "max_upload_bytes": self.max_upload_bytes,
            "max_pdf_upload_bytes": self.max_pdf_upload_bytes,
            "max_pdf_pages": self.max_pdf_pages,
            "max_pdf_text_characters": self.max_pdf_text_characters,
            "max_output_tokens": self.max_output_tokens,
            "max_model_iterations": self.max_model_iterations,
            "chunk_max_input_tokens": self.chunk_max_input_tokens,
        }
        invalid = tuple(
            name for name, value in positive_numbers.items() if not isfinite(value) or value <= 0
        )
        if invalid:
            raise WorkbenchConfigurationError(
                f"Workbench settings must be finite and greater than zero: {', '.join(invalid)}."
            )
        if (
            type(self.chunk_max_input_tokens) is not int
            or type(self.chunk_overlap_tokens) is not int
            or not 0 <= self.chunk_overlap_tokens < self.chunk_max_input_tokens
        ):
            raise WorkbenchConfigurationError(
                "Chunk overlap must be nonnegative and below the token limit."
            )

    @classmethod
    def from_environment(cls) -> WorkbenchSettings:
        """Build settings from documented environment variables."""
        defaults = cls()
        return cls(
            retrieval_strategy=os.getenv(
                "CONTEXT_ENGINE_RETRIEVAL_STRATEGY", defaults.retrieval_strategy
            ),
            lexical_collection_name=os.getenv(
                "CONTEXT_ENGINE_LEXICAL_COLLECTION", defaults.lexical_collection_name
            ),
            model_id=os.getenv("CONTEXT_ENGINE_WORKBENCH_MODEL", defaults.model_id),
            ollama_base_url=os.getenv("CONTEXT_ENGINE_OLLAMA_BASE_URL", defaults.ollama_base_url),
            ollama_timeout_seconds=_read_float(
                "CONTEXT_ENGINE_OLLAMA_TIMEOUT_SECONDS", defaults.ollama_timeout_seconds
            ),
            embedding_model_id=os.getenv(
                "CONTEXT_ENGINE_EMBEDDING_MODEL", defaults.embedding_model_id
            ),
            embedding_model_reference=os.getenv(
                "CONTEXT_ENGINE_EMBEDDING_MODEL_REFERENCE",
                os.getenv("CONTEXT_ENGINE_EMBEDDING_MODEL", defaults.embedding_model_reference),
            ),
            qdrant_url=os.getenv("CONTEXT_ENGINE_QDRANT_URL", defaults.qdrant_url),
            qdrant_timeout_seconds=_read_float(
                "CONTEXT_ENGINE_QDRANT_TIMEOUT_SECONDS", defaults.qdrant_timeout_seconds
            ),
            collection_name=os.getenv(
                "CONTEXT_ENGINE_WORKBENCH_COLLECTION", defaults.collection_name
            ),
            max_uploads=_read_int("CONTEXT_ENGINE_WORKBENCH_MAX_UPLOADS", defaults.max_uploads),
            chunk_max_input_tokens=_read_int(
                "CONTEXT_ENGINE_WORKBENCH_CHUNK_TOKENS", defaults.chunk_max_input_tokens
            ),
            chunk_overlap_tokens=_read_int(
                "CONTEXT_ENGINE_WORKBENCH_CHUNK_OVERLAP_TOKENS", defaults.chunk_overlap_tokens
            ),
            max_pdf_upload_bytes=_read_int(
                "CONTEXT_ENGINE_WORKBENCH_MAX_PDF_BYTES", defaults.max_pdf_upload_bytes
            ),
            max_pdf_pages=_read_int(
                "CONTEXT_ENGINE_WORKBENCH_MAX_PDF_PAGES", defaults.max_pdf_pages
            ),
            max_pdf_text_characters=_read_int(
                "CONTEXT_ENGINE_WORKBENCH_MAX_PDF_TEXT_CHARACTERS", defaults.max_pdf_text_characters
            ),
            max_upload_bytes=_read_int(
                "CONTEXT_ENGINE_WORKBENCH_MAX_UPLOAD_BYTES", defaults.max_upload_bytes
            ),
        )


def _read_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise WorkbenchConfigurationError(f"{name} must be an integer.") from exc


def _read_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError as exc:
        raise WorkbenchConfigurationError(f"{name} must be a number.") from exc
