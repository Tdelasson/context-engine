"""Retrieval domain contracts."""

from context_engine.retrieval.embeddings import (
    Document,
    Embedding,
    EmbeddingProvider,
    normalize_document_metadata,
)
from context_engine.retrieval.evaluation import (
    RetrievalEvaluationError,
    RetrievalQualityMetrics,
    evaluate_rankings,
    ndcg_at_k,
    recall_at_k,
    reciprocal_rank,
)
from context_engine.retrieval.ingestor import (
    Ingestor,
    IngestorError,
    LengthMismatchError,
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
    "RetrievalEvaluationError",
    "RetrievalQualityMetrics",
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
    "Ingestor",
    "IngestorError",
    "LengthMismatchError",
    "evaluate_rankings",
    "ndcg_at_k",
    "recall_at_k",
    "reciprocal_rank",
]
