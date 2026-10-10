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

    evidence_selection_enabled: bool = False
    evidence_token_budget: int = 4096
    evidence_overlap_threshold: float = 0.8
    evidence_candidate_limit: int = 20
    evidence_max_results: int = 5
    evidence_tokenizer_directory: str = ""
    retrieval_strategy: str = "dense"
    lexical_collection_name: str = "context-engine-workbench-m5-bm25-v1"
    hybrid_dense_candidates: int = 20
    hybrid_lexical_candidates: int = 20
    hybrid_final_results: int = 20
    hybrid_smoothing: int = 60
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
    reranking_enabled: bool = False
    reranking_model_reference: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    reranking_revision: str | None = None
    reranking_device: str = "cpu"
    reranking_candidate_limit: int = 20
    reranking_final_limit: int = 5
    reranking_batch_size: int = 8
    reranking_input_tokens: int = 512

    def __post_init__(self) -> None:
        from context_engine.retrieval.evidence_selection import EvidenceSelectionConfig

        if type(self.evidence_selection_enabled) is not bool:
            raise WorkbenchConfigurationError("Evidence selection flag must be boolean.")
        try:
            EvidenceSelectionConfig(
                self.evidence_token_budget,
                self.evidence_max_results,
                overlap_threshold=self.evidence_overlap_threshold,
            )
        except ValueError as exc:
            raise WorkbenchConfigurationError(str(exc)) from exc
        if (
            type(self.evidence_candidate_limit) is not int
            or not 1 <= self.evidence_candidate_limit <= 1000
        ):
            raise WorkbenchConfigurationError("Evidence candidate limit must be in [1, 1000].")
        if self.evidence_selection_enabled and (
            self.model_id != "qwen2.5:0.5b" or not self.evidence_tokenizer_directory.strip()
        ):
            raise WorkbenchConfigurationError(
                "Selection supports qwen2.5:0.5b with a local tokenizer directory."
            )
        from context_engine.retrieval.local_cross_encoder import LocalCrossEncoderConfig
        from context_engine.retrieval.reranking import RerankingRetrieverConfig

        if type(self.reranking_enabled) is not bool:
            raise WorkbenchConfigurationError("reranking_enabled must be boolean.")
        try:
            LocalCrossEncoderConfig(
                model_reference=self.reranking_model_reference,
                revision=self.reranking_revision,
                device=self.reranking_device,
                batch_size=self.reranking_batch_size,
                max_input_tokens=self.reranking_input_tokens,
            )
            RerankingRetrieverConfig(self.reranking_candidate_limit, self.reranking_final_limit)
        except ValueError as exc:
            raise WorkbenchConfigurationError(str(exc)) from exc
        if self.retrieval_strategy not in {"dense", "lexical", "hybrid"}:
            raise WorkbenchConfigurationError(
                "retrieval_strategy must be dense, lexical, or hybrid."
            )
        from context_engine.retrieval.hybrid import HybridConfigurationError, HybridRetrieverConfig

        try:
            HybridRetrieverConfig(
                self.hybrid_dense_candidates,
                self.hybrid_lexical_candidates,
                self.hybrid_final_results,
                self.hybrid_smoothing,
            )
        except HybridConfigurationError as exc:
            raise WorkbenchConfigurationError(str(exc)) from exc
        if (
            self.reranking_enabled
            and self.retrieval_strategy == "hybrid"
            and self.reranking_candidate_limit > self.hybrid_final_results
        ):
            raise WorkbenchConfigurationError(
                "Reranking candidate limit cannot exceed the hybrid final result ceiling."
            )
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
            evidence_selection_enabled=_read_bool(
                "CONTEXT_ENGINE_EVIDENCE_SELECTION_ENABLED", False
            ),
            evidence_token_budget=_read_int(
                "CONTEXT_ENGINE_EVIDENCE_TOKEN_BUDGET", defaults.evidence_token_budget
            ),
            evidence_overlap_threshold=_read_float(
                "CONTEXT_ENGINE_EVIDENCE_OVERLAP_THRESHOLD", defaults.evidence_overlap_threshold
            ),
            evidence_candidate_limit=_read_int(
                "CONTEXT_ENGINE_EVIDENCE_CANDIDATES", defaults.evidence_candidate_limit
            ),
            evidence_max_results=_read_int(
                "CONTEXT_ENGINE_EVIDENCE_MAX_RESULTS", defaults.evidence_max_results
            ),
            evidence_tokenizer_directory=os.getenv(
                "CONTEXT_ENGINE_EVIDENCE_TOKENIZER_DIRECTORY", ""
            ),
            retrieval_strategy=os.getenv(
                "CONTEXT_ENGINE_RETRIEVAL_STRATEGY", defaults.retrieval_strategy
            ),
            lexical_collection_name=os.getenv(
                "CONTEXT_ENGINE_LEXICAL_COLLECTION", defaults.lexical_collection_name
            ),
            reranking_enabled=_read_bool("CONTEXT_ENGINE_RERANKING_ENABLED", False),
            reranking_model_reference=os.getenv(
                "CONTEXT_ENGINE_RERANKING_MODEL_REFERENCE", defaults.reranking_model_reference
            ),
            reranking_revision=os.getenv("CONTEXT_ENGINE_RERANKING_REVISION"),
            reranking_device=os.getenv(
                "CONTEXT_ENGINE_RERANKING_DEVICE", defaults.reranking_device
            ),
            reranking_candidate_limit=_read_int(
                "CONTEXT_ENGINE_RERANKING_CANDIDATES", defaults.reranking_candidate_limit
            ),
            reranking_final_limit=_read_int(
                "CONTEXT_ENGINE_RERANKING_FINAL_LIMIT", defaults.reranking_final_limit
            ),
            reranking_batch_size=_read_int(
                "CONTEXT_ENGINE_RERANKING_BATCH_SIZE", defaults.reranking_batch_size
            ),
            reranking_input_tokens=_read_int(
                "CONTEXT_ENGINE_RERANKING_INPUT_TOKENS", defaults.reranking_input_tokens
            ),
            hybrid_dense_candidates=_read_int(
                "CONTEXT_ENGINE_HYBRID_DENSE_CANDIDATES", defaults.hybrid_dense_candidates
            ),
            hybrid_lexical_candidates=_read_int(
                "CONTEXT_ENGINE_HYBRID_LEXICAL_CANDIDATES", defaults.hybrid_lexical_candidates
            ),
            hybrid_final_results=_read_int(
                "CONTEXT_ENGINE_HYBRID_FINAL_RESULTS", defaults.hybrid_final_results
            ),
            hybrid_smoothing=_read_int(
                "CONTEXT_ENGINE_HYBRID_SMOOTHING", defaults.hybrid_smoothing
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


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    if value.lower() not in {"true", "false"}:
        raise WorkbenchConfigurationError(f"{name} must be true or false.")
    return value.lower() == "true"
