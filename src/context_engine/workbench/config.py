"""Environment-backed configuration for the local workbench application."""

from __future__ import annotations

import os
from dataclasses import dataclass


class WorkbenchConfigurationError(ValueError):
    """Raised when workbench configuration is invalid."""


@dataclass(frozen=True, slots=True)
class WorkbenchSettings:
    """Typed local dependency and execution settings."""

    model_id: str = "llama3.2:1b"
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout_seconds: float = 30.0
    embedding_model_id: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_model_reference: str = "sentence-transformers/all-MiniLM-L6-v2"
    qdrant_url: str = "http://localhost:6333"
    qdrant_timeout_seconds: float = 5.0
    collection_name: str = "context-engine-workbench"
    max_uploads: int = 5
    max_upload_bytes: int = 256 * 1024
    max_output_tokens: int = 256
    max_model_iterations: int = 4

    def __post_init__(self) -> None:
        string_fields = {
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
            "max_output_tokens": self.max_output_tokens,
            "max_model_iterations": self.max_model_iterations,
        }
        invalid = tuple(name for name, value in positive_numbers.items() if value <= 0)
        if invalid:
            raise WorkbenchConfigurationError(
                f"Workbench settings must be greater than zero: {', '.join(invalid)}."
            )

    @classmethod
    def from_environment(cls) -> WorkbenchSettings:
        """Build settings from documented environment variables."""
        defaults = cls()
        return cls(
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
