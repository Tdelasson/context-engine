"""Retrieval domain contracts."""

from context_engine.retrieval.embeddings import (
    Document,
    Embedding,
    EmbeddingProvider,
    normalize_document_metadata,
)
from context_engine.retrieval.local_embedding_provider import (
    LocalEmbeddingProvider,
    LocalEmbeddingProviderConfig,
    LocalEmbeddingProviderConfigurationError,
    LocalEmbeddingProviderError,
    LocalEmbeddingProviderInferenceError,
    LocalEmbeddingProviderInitializationError,
)

__all__ = [
    "Document",
    "Embedding",
    "EmbeddingProvider",
    "LocalEmbeddingProvider",
    "LocalEmbeddingProviderConfig",
    "LocalEmbeddingProviderConfigurationError",
    "LocalEmbeddingProviderError",
    "LocalEmbeddingProviderInferenceError",
    "LocalEmbeddingProviderInitializationError",
    "normalize_document_metadata",
]
