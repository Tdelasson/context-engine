"""Local embedding provider backed by direct in-process inference."""

from __future__ import annotations

import importlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from context_engine.retrieval.embeddings import Document, Embedding, EmbeddingProvider


class LocalEmbeddingProviderError(Exception):
    """Base exception for local embedding provider failures."""


class LocalEmbeddingProviderConfigurationError(LocalEmbeddingProviderError, ValueError):
    """Raised when local embedding provider configuration is invalid."""


class LocalEmbeddingProviderInitializationError(LocalEmbeddingProviderError, RuntimeError):
    """Raised when local embedding runtime/model initialization fails."""


class LocalEmbeddingProviderInferenceError(LocalEmbeddingProviderError, RuntimeError):
    """Raised when local embedding inference fails or returns invalid vectors."""


@dataclass(frozen=True, slots=True)
class LocalEmbeddingProviderConfig:
    """Configuration for local embedding inference."""

    model_id: str
    model_reference: str
    batch_size: int = 32
    normalize_embeddings: bool = False
    document_prefix: str = ""
    query_prefix: str = ""
    trust_remote_code: bool = False

    def __post_init__(self) -> None:
        if not self.model_id:
            raise LocalEmbeddingProviderConfigurationError(
                "model_id must be a non-empty string for LocalEmbeddingProvider."
            )
        if not self.model_reference:
            raise LocalEmbeddingProviderConfigurationError(
                "model_reference must be a non-empty string for LocalEmbeddingProvider."
            )
        if self.batch_size <= 0:
            raise LocalEmbeddingProviderConfigurationError(
                "batch_size must be greater than zero for LocalEmbeddingProvider."
            )


class _LocalEmbeddingInferenceBackend(Protocol):
    @property
    def model_id(self) -> str: ...

    @property
    def dimensions(self) -> int: ...

    @property
    def model_parameter_bytes(self) -> int | None: ...

    def embed_documents(
        self,
        texts: Sequence[str],
        *,
        batch_size: int,
        normalize_embeddings: bool,
    ) -> Sequence[Sequence[float]]: ...

    def embed_query(self, text: str, *, normalize_embeddings: bool) -> Sequence[float]: ...


_BackendFactory = Callable[[LocalEmbeddingProviderConfig], _LocalEmbeddingInferenceBackend]


class LocalEmbeddingProvider(EmbeddingProvider):
    """Embedding provider implementation using local in-process model inference."""

    def __init__(
        self,
        config: LocalEmbeddingProviderConfig,
        *,
        backend_factory: _BackendFactory | None = None,
    ) -> None:
        self._config = config
        factory = (
            _build_sentence_transformer_backend if backend_factory is None else backend_factory
        )
        try:
            self._backend = factory(config)
        except LocalEmbeddingProviderError:
            raise
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise LocalEmbeddingProviderInitializationError(
                "Failed to initialize LocalEmbeddingProvider backend."
            ) from exc

        if not self._backend.model_id:
            raise LocalEmbeddingProviderInitializationError(
                "Local embedding backend returned an empty model_id."
            )
        if self._backend.dimensions <= 0:
            raise LocalEmbeddingProviderInitializationError(
                "Local embedding backend dimensions must be greater than zero."
            )

    @property
    def model_id(self) -> str:
        """Return the stable model identity reported by the inference backend."""
        return self._backend.model_id

    @property
    def dimensions(self) -> int:
        """Return the embedding dimensionality reported by the inference backend."""
        return self._backend.dimensions

    @property
    def model_parameter_bytes(self) -> int | None:
        """Return the in-memory parameter footprint when it can be measured."""
        return self._backend.model_parameter_bytes

    def embed_documents(self, documents: Sequence[Document]) -> tuple[Embedding, ...]:
        if not documents:
            return ()

        texts = tuple(f"{self._config.document_prefix}{document.content}" for document in documents)
        try:
            vectors = self._backend.embed_documents(
                texts,
                batch_size=self._config.batch_size,
                normalize_embeddings=self._config.normalize_embeddings,
            )
        except LocalEmbeddingProviderError:
            raise
        except Exception as exc:
            raise LocalEmbeddingProviderInferenceError(
                "Local embedding backend failed while embedding documents."
            ) from exc

        if len(vectors) != len(documents):
            raise LocalEmbeddingProviderInferenceError(
                "Local embedding backend returned a different number of vectors than documents."
            )

        return tuple(self._build_embedding(vector) for vector in vectors)

    def embed_query(self, query: str) -> Embedding:
        if not query:
            raise LocalEmbeddingProviderConfigurationError(
                "query must be a non-empty string for LocalEmbeddingProvider.embed_query()."
            )

        text = f"{self._config.query_prefix}{query}"
        try:
            vector = self._backend.embed_query(
                text,
                normalize_embeddings=self._config.normalize_embeddings,
            )
        except LocalEmbeddingProviderError:
            raise
        except Exception as exc:
            raise LocalEmbeddingProviderInferenceError(
                "Local embedding backend failed while embedding query."
            ) from exc

        return self._build_embedding(vector)

    def _build_embedding(self, vector: Sequence[float]) -> Embedding:
        try:
            return Embedding.from_sequence(
                vector=vector,
                model_id=self._backend.model_id,
                dimensions=self._backend.dimensions,
            )
        except ValueError as exc:
            raise LocalEmbeddingProviderInferenceError(
                "Local embedding backend returned an invalid embedding vector."
            ) from exc


class _SentenceTransformerEmbeddingBackend:
    """Default local embedding backend using sentence-transformers."""

    def __init__(self, config: LocalEmbeddingProviderConfig) -> None:
        try:
            sentence_transformers_module = importlib.import_module("sentence_transformers")
            sentence_transformer_cls = sentence_transformers_module.SentenceTransformer
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise LocalEmbeddingProviderInitializationError(
                "sentence-transformers is required for LocalEmbeddingProvider. "
                "Install it with: pip install sentence-transformers"
            ) from exc

        try:
            self._model: Any = sentence_transformer_cls(
                config.model_reference,
                trust_remote_code=config.trust_remote_code,
            )
        except Exception as exc:
            raise LocalEmbeddingProviderInitializationError(
                f"Failed to load local embedding model '{config.model_reference}'."
            ) from exc

        dimensions = self._model.get_embedding_dimension()
        if dimensions is None or dimensions <= 0:
            raise LocalEmbeddingProviderInitializationError(
                "Unable to determine embedding dimensions from local model."
            )

        self._model_id = config.model_id
        self._dimensions = int(dimensions)

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_parameter_bytes(self) -> int | None:
        try:
            return sum(
                int(parameter.numel()) * int(parameter.element_size())
                for parameter in self._model.parameters()
            )
        except (AttributeError, TypeError):
            return None

    def embed_documents(
        self,
        texts: Sequence[str],
        *,
        batch_size: int,
        normalize_embeddings: bool,
    ) -> tuple[tuple[float, ...], ...]:
        encoded = self._model.encode(
            list(texts),
            batch_size=batch_size,
            normalize_embeddings=normalize_embeddings,
            convert_to_numpy=False,
            show_progress_bar=False,
        )
        return _coerce_vectors(encoded)

    def embed_query(self, text: str, *, normalize_embeddings: bool) -> tuple[float, ...]:
        vectors = self.embed_documents(
            (text,),
            batch_size=1,
            normalize_embeddings=normalize_embeddings,
        )
        if len(vectors) != 1:
            raise LocalEmbeddingProviderInferenceError(
                "Local embedding backend returned an unexpected number of query vectors."
            )
        return vectors[0]


def _coerce_vectors(vectors: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], ...]:
    normalized_vectors: list[tuple[float, ...]] = []
    for raw_vector in vectors:
        normalized_vectors.append(tuple(float(value) for value in raw_vector))
    return tuple(normalized_vectors)


def _build_sentence_transformer_backend(
    config: LocalEmbeddingProviderConfig,
) -> _SentenceTransformerEmbeddingBackend:
    return _SentenceTransformerEmbeddingBackend(config)
