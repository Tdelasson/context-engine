"""Provider-independent embedding domain models and contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from typing import Protocol, runtime_checkable


def normalize_document_metadata(metadata: Mapping[str, object]) -> tuple[tuple[str, object], ...]:
    """Return immutable normalized document metadata."""
    return tuple(sorted(metadata.items()))


@dataclass(frozen=True, slots=True)
class Document:
    """Provider-independent document representation for embedding and retrieval."""

    document_id: str
    content: str
    metadata: tuple[tuple[str, object], ...] = ()

    @classmethod
    def from_mapping(
        cls,
        *,
        document_id: str,
        content: str,
        metadata: Mapping[str, object] | None = None,
    ) -> Document:
        """Construct an immutable document from mapping metadata."""
        return cls(
            document_id=document_id,
            content=content,
            metadata=normalize_document_metadata(metadata or {}),
        )

    def __post_init__(self) -> None:
        if not self.document_id:
            raise ValueError("document_id must be a non-empty string.")

    def metadata_as_mapping(self) -> dict[str, object]:
        """Return document metadata as a mutable mapping."""
        return dict(self.metadata)


@dataclass(frozen=True, slots=True)
class Embedding:
    """Provider-independent embedding representation with generation metadata."""

    vector: tuple[float, ...]
    model_id: str
    dimensions: int

    @classmethod
    def from_sequence(
        cls,
        *,
        vector: Sequence[float],
        model_id: str,
        dimensions: int | None = None,
    ) -> Embedding:
        """Construct an immutable embedding from a numeric sequence."""
        normalized_vector = tuple(float(value) for value in vector)
        return cls(
            vector=normalized_vector,
            model_id=model_id,
            dimensions=len(normalized_vector) if dimensions is None else dimensions,
        )

    def __post_init__(self) -> None:
        if not self.model_id:
            raise ValueError("model_id must be a non-empty string.")
        if self.dimensions <= 0:
            raise ValueError("dimensions must be greater than zero.")
        if len(self.vector) != self.dimensions:
            raise ValueError(
                "Embedding dimensionality mismatch: "
                f"vector length is {len(self.vector)} but dimensions is {self.dimensions}."
            )
        if not all(isfinite(value) for value in self.vector):
            raise ValueError("Embedding vector values must be finite numbers.")


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Provider-independent embedding generation abstraction. Returns one embedding for each input document, in the same order as the input documents."""

    def embed_documents(self, documents: Sequence[Document]) -> Sequence[Embedding]:
        """Embed multiple documents in one batch operation."""

    def embed_query(self, query: str) -> Embedding:
        """Embed one query string."""
