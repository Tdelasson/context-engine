"""Provider-independent vector-store domain models and contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from context_engine.retrieval.embeddings import Document, Embedding


class VectorStoreError(Exception):
    """Base exception for vector-store failures."""


class VectorStoreConfigurationError(VectorStoreError, ValueError):
    """Raised when vector-store configuration is invalid."""


class VectorStoreCompatibilityError(VectorStoreError, ValueError):
    """Raised when vectors are incompatible with the configured collection."""


class VectorDistanceMetric(StrEnum):
    """Provider-independent vector distance metrics."""

    COSINE = "cosine"
    DOT = "dot"
    EUCLIDEAN = "euclidean"


MetadataFilterValue = str | int | float | bool


@dataclass(frozen=True, slots=True)
class MetadataFilter:
    """Provider-independent metadata filter representation.

    The initial M4 representation supports exact-match predicates joined by logical AND.
    """

    equals: tuple[tuple[str, MetadataFilterValue], ...] = ()

    @classmethod
    def from_mapping(
        cls, equals: Mapping[str, MetadataFilterValue] | None = None
    ) -> MetadataFilter:
        """Construct a metadata filter from an exact-match mapping."""
        if equals is None:
            return cls()
        normalized = tuple(sorted(equals.items()))
        return cls(equals=normalized)

    def as_mapping(self) -> dict[str, MetadataFilterValue]:
        """Return the filter as a mutable mapping."""
        return dict(self.equals)


@dataclass(frozen=True, slots=True)
class VectorStoreCollectionConfig:
    """Collection-level vector-store configuration."""

    collection_name: str
    embedding_model_id: str
    dimensions: int
    distance_metric: VectorDistanceMetric = VectorDistanceMetric.COSINE

    def __post_init__(self) -> None:
        if not self.collection_name:
            raise VectorStoreConfigurationError("collection_name must be a non-empty string.")
        if not self.embedding_model_id:
            raise VectorStoreConfigurationError("embedding_model_id must be a non-empty string.")
        if self.dimensions <= 0:
            raise VectorStoreConfigurationError("dimensions must be greater than zero.")

    def ensure_embedding_compatible(self, embedding: Embedding) -> None:
        """Raise when the embedding does not match the collection configuration."""
        if embedding.model_id != self.embedding_model_id:
            raise VectorStoreCompatibilityError(
                "Embedding model mismatch: "
                f"expected '{self.embedding_model_id}' but got '{embedding.model_id}'."
            )
        if embedding.dimensions != self.dimensions:
            raise VectorStoreCompatibilityError(
                "Embedding dimensionality mismatch: "
                f"expected {self.dimensions} but got {embedding.dimensions}."
            )


@dataclass(frozen=True, slots=True)
class VectorStoreRecord:
    """A stored document paired with its embedding."""

    document: Document
    embedding: Embedding


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Provider-independent similarity-search result."""

    document: Document
    score: float


@runtime_checkable
class VectorStore(Protocol):
    """Provider-independent vector persistence and similarity-search abstraction."""

    def upsert(self, records: Sequence[VectorStoreRecord]) -> None:
        """Insert or update one or more document embeddings."""

    def search(
        self,
        query_embedding: Embedding,
        *,
        top_k: int = 5,
        metadata_filter: MetadataFilter | None = None,
    ) -> Sequence[SearchResult]:
        """Run a similarity search for the query embedding."""

    def delete(self, document_ids: Sequence[str]) -> None:
        """Delete stored records by stable document ID."""
