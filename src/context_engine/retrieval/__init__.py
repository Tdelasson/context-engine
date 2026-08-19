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
from context_engine.retrieval.qdrant_vector_store import QdrantVectorStore
from context_engine.retrieval.retriever import (
    EmbeddingVectorStoreRetriever,
    RetrievalRequest,
    Retriever,
    RetrieverConfigurationError,
    RetrieverError,
)
from context_engine.retrieval.vector_store import (
    MetadataFilter,
    SearchResult,
    VectorDistanceMetric,
    VectorStore,
    VectorStoreCollectionConfig,
    VectorStoreCompatibilityError,
    VectorStoreConfigurationError,
    VectorStoreError,
    VectorStoreRecord,
)

__all__ = [
    "Document",
    "Embedding",
    "EmbeddingProvider",
    "MetadataFilter",
    "LocalEmbeddingProvider",
    "LocalEmbeddingProviderConfig",
    "LocalEmbeddingProviderConfigurationError",
    "LocalEmbeddingProviderError",
    "LocalEmbeddingProviderInferenceError",
    "LocalEmbeddingProviderInitializationError",
    "QdrantVectorStore",
    "Retriever",
    "RetrieverError",
    "RetrieverConfigurationError",
    "RetrievalRequest",
    "EmbeddingVectorStoreRetriever",
    "SearchResult",
    "VectorDistanceMetric",
    "VectorStore",
    "VectorStoreCollectionConfig",
    "VectorStoreCompatibilityError",
    "VectorStoreConfigurationError",
    "VectorStoreError",
    "VectorStoreRecord",
    "normalize_document_metadata",
]
