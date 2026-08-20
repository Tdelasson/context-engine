from collections.abc import Sequence

from context_engine.retrieval.embeddings import (
    Document,
    Embedding,
    EmbeddingProvider,
)
from context_engine.retrieval.vector_store import (
    VectorStore,
    VectorStoreRecord,
)


class IngestorError(Exception):
    """Base exception for ingestor failures."""


class LengthMismatchError(IngestorError, ValueError):
    """Raised when the number of embeddings does not match the number of documents."""


class Ingestor:
    def __init__(self, embedding_provider: EmbeddingProvider, vector_store: VectorStore):
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def ingest_documents(self, documents: Sequence[Document]) -> None:
        if not documents:
            return

        embeddings: Sequence[Embedding] = self._embedding_provider.embed_documents(documents)

        if len(embeddings) != len(documents):
            raise LengthMismatchError("Number of embeddings must match number of documents.")

        vector_store_records: list[VectorStoreRecord] = []

        for i, embedding in enumerate(embeddings):
            vector_store_record: VectorStoreRecord = VectorStoreRecord(
                document=documents[i], embedding=embedding
            )
            vector_store_records.append(vector_store_record)

        self._vector_store.upsert(vector_store_records)
