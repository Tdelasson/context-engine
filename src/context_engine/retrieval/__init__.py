"""Retrieval domain contracts."""

from context_engine.retrieval.embeddings import (
    Document,
    Embedding,
    EmbeddingProvider,
    normalize_document_metadata,
)

__all__ = [
    "Document",
    "Embedding",
    "EmbeddingProvider",
    "normalize_document_metadata",
]
