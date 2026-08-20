"""Provider-independent retrieval abstraction."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from context_engine.retrieval.embeddings import EmbeddingProvider
from context_engine.retrieval.vector_store import MetadataFilter, SearchResult, VectorStore


class RetrieverError(Exception):
    """Base exception for retriever failures."""


class RetrieverConfigurationError(RetrieverError, ValueError):
    """Raised when retriever inputs are invalid."""


@dataclass(frozen=True, slots=True)
class RetrievalRequest:
    """Provider-independent retrieval request."""

    query: str
    top_k: int = 5
    metadata_filter: MetadataFilter | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.query, str) or not self.query:
            raise RetrieverConfigurationError("query must be a non-empty string.")
        if isinstance(self.top_k, bool) or not isinstance(self.top_k, int) or self.top_k <= 0:
            raise RetrieverConfigurationError("top_k must be an integer greater than zero.")


@runtime_checkable
class Retriever(Protocol):
    """Application-facing retrieval abstraction."""

    def retrieve(self, request: RetrievalRequest) -> Sequence[SearchResult]:
        """Retrieve relevant documents for a query request."""


class EmbeddingVectorStoreRetriever(Retriever):
    """Retriever that orchestrates embedding and vector search."""

    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def retrieve(self, request: RetrievalRequest) -> Sequence[SearchResult]:
        query_embedding = self._embedding_provider.embed_query(request.query)
        return self._vector_store.search(
            query_embedding,
            top_k=request.top_k,
            metadata_filter=request.metadata_filter,
        )
