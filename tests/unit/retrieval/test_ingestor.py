from collections.abc import Sequence

from context_engine.retrieval import Document, Embedding, Ingestor
from context_engine.retrieval.vector_store import (
    MetadataFilter,
    SearchResult,
    VectorStore,
    VectorStoreCollectionConfig,
    VectorStoreRecord,
)


class _FakeEmbeddingProvider:
    def __init__(self) -> None:
        self.model_id = "mini-model"
        self.dimensions = 3

    def embed_documents(self, documents: Sequence[Document]) -> Sequence[Embedding]:
        self.provided_documents = documents
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
        self.provided_records = records
        for record in records:
            self._config.ensure_embedding_compatible(record.embedding)
            self._records[record.document.document_id] = record

    def search(
        self,
        query_embedding: Embedding,
        *,
        top_k: int = 5,
        metadata_filter: MetadataFilter | None = None,
    ) -> Sequence[SearchResult]:
        del query_embedding, top_k, metadata_filter
        return ()

    def delete(self, document_ids: Sequence[str]) -> None:
        for document_id in document_ids:
            self._records.pop(document_id, None)


def _build_store() -> _InMemoryVectorStore:
    return _InMemoryVectorStore(
        VectorStoreCollectionConfig(
            collection_name="unit-test-collection",
            embedding_model_id="mini-model",
            dimensions=3,
        )
    )


def test_ingestor_handles_empty_document_list() -> None:
    vector_store = _build_store()
    ingestor = Ingestor(embedding_provider=_FakeEmbeddingProvider(), vector_store=vector_store)
    ingestor.ingest_documents([])
    assert len(vector_store._records) == 0


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
    assert embedding_provider.provided_documents == documents


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
    assert vector_store._records["doc1"].document == documents[0]
    assert vector_store._records["doc1"].embedding == embedding_provider.embeddings[0]
    assert vector_store._records["doc1"].embedding.model_id == embedding_provider.model_id
    assert vector_store._records["doc1"].embedding.dimensions == embedding_provider.dimensions
    assert vector_store._records["doc2"].document == documents[1]
    assert vector_store._records["doc2"].embedding == embedding_provider.embeddings[1]
    assert vector_store._records["doc2"].embedding.model_id == embedding_provider.model_id
    assert vector_store._records["doc2"].embedding.dimensions == embedding_provider.dimensions
