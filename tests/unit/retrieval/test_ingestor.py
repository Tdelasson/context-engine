from collections.abc import Sequence

from context_engine.retrieval import Document, Embedding, Ingestor
from context_engine.retrieval.vector_store import (
    VectorStore,
    VectorStoreCollectionConfig,
    VectorStoreRecord,
)


class _FakeEmbeddingProvider:
    def __init__(self) -> None:
        self.model_id = "mini-model"
        self.dimensions = 3

    def embed_documents(self, documents: tuple[Document, ...]) -> tuple[Embedding, ...]:
        self.embeddings = list(
            Embedding.from_sequence(
                vector=(float(index), float(len(document.content)), 1.0),
                model_id=self.model_id,
                dimensions=self.dimensions,
            )
            for index, document in enumerate(documents, start=1)
        )
        return tuple(self.embeddings)

    def embed_query(self, query: str) -> Embedding:
        return Embedding.from_sequence(
            vector=(float(len(query)), 0.0, 1.0),
            model_id=self.model_id,
            dimensions=self.dimensions,
        )


class _InMemoryVectorStore(VectorStore):
    def __init__(self, config: VectorStoreCollectionConfig) -> None:
        self._config = config
        self._records: dict[str, VectorStoreRecord] = {}

    def upsert(self, records: Sequence[VectorStoreRecord]) -> None:
        for record in records:
            self._config.ensure_embedding_compatible(record.embedding)
            self._records[record.document.document_id] = record


def _build_store() -> _InMemoryVectorStore:
    return _InMemoryVectorStore(
        VectorStoreCollectionConfig(
            collection_name="unit-test-collection",
            embedding_model_id="mini-model",
            dimensions=3,
        )
    )


def test_ingestor_handles_empty_document_list() -> None:
    ingestor = Ingestor(embedding_provider=_FakeEmbeddingProvider(), vector_store=_build_store())
    result = ingestor.ingest_documents([])
    assert result is None


def test_ingestor_docs_passed_to_provider() -> None:
    embedding_provider = _FakeEmbeddingProvider()
    vector_store = _build_store()
    ingestor = Ingestor(embedding_provider=embedding_provider, vector_store=vector_store)
    documents = [
        Document(document_id="doc1", content="Test document 1"),
        Document(document_id="doc2", content="Test document 2"),
    ]
    ingestor.ingest_documents(documents)

    assert len(embedding_provider.embeddings) == len(documents)


def test_ingestor_docs_and_embeddings_pairing() -> None:
    embedding_provider = _FakeEmbeddingProvider()
    vector_store = _build_store()
    ingestor = Ingestor(embedding_provider=embedding_provider, vector_store=vector_store)
    documents = [
        Document(document_id="doc1", content="Test document 1"),
        Document(document_id="doc2", content="Test document 2"),
    ]
    ingestor.ingest_documents(documents)

    for i, record in enumerate(vector_store._records.values()):
        assert record.document == documents[i]
        assert record.embedding == embedding_provider.embeddings[i]


def test_ingestor_records_passed_to_vector_store() -> None:
    embedding_provider = _FakeEmbeddingProvider()
    vector_store = _build_store()
    ingestor = Ingestor(embedding_provider=embedding_provider, vector_store=vector_store)
    documents = [
        Document(document_id="doc1", content="Test document 1"),
        Document(document_id="doc2", content="Test document 2"),
    ]
    ingestor.ingest_documents(documents)

    assert len(vector_store._records) == len(documents)
