from __future__ import annotations

from collections.abc import Sequence

import pytest

from context_engine.retrieval import (
    Document,
    Embedding,
    EmbeddingProvider,
    EmbeddingVectorStoreRetriever,
    MetadataFilter,
    RetrievalRequest,
    Retriever,
    RetrieverConfigurationError,
    SearchResult,
    VectorStore,
)


class _FakeEmbeddingProvider(EmbeddingProvider):
    def __init__(self, embedding: Embedding) -> None:
        self._embedding = embedding
        self.queries: list[str] = []

    def embed_documents(self, documents: Sequence[Document]) -> Sequence[Embedding]:
        del documents
        raise AssertionError("This fake should not be used for document embedding in retriever tests.")

    def embed_query(self, query: str) -> Embedding:
        self.queries.append(query)
        return self._embedding


class _FakeVectorStore(VectorStore):
    def __init__(self, results: Sequence[SearchResult]) -> None:
        self.results = results
        self.calls: list[tuple[Embedding, int, MetadataFilter | None]] = []

    def upsert(self, records: Sequence[object]) -> None:  # pragma: no cover - protocol placeholder
        del records

    def search(
        self,
        query_embedding: Embedding,
        *,
        top_k: int = 5,
        metadata_filter: MetadataFilter | None = None,
    ) -> Sequence[SearchResult]:
        self.calls.append((query_embedding, top_k, metadata_filter))
        return self.results

    def delete(self, document_ids: Sequence[str]) -> None:  # pragma: no cover - protocol placeholder
        del document_ids


def test_embedding_vector_store_retriever_satisfies_retriever_protocol() -> None:
    provider = _FakeEmbeddingProvider(
        Embedding.from_sequence(vector=(1.0, 0.0), model_id="test-model", dimensions=2)
    )
    store = _FakeVectorStore(results=())

    retriever = EmbeddingVectorStoreRetriever(embedding_provider=provider, vector_store=store)

    assert isinstance(retriever, Retriever)


def test_retriever_embeds_query_and_searches_vector_store() -> None:
    query_embedding = Embedding.from_sequence(vector=(0.8, 0.2), model_id="test-model", dimensions=2)
    provider = _FakeEmbeddingProvider(query_embedding)
    expected_results = (
        SearchResult(document=Document.from_mapping(document_id="doc-1", content="music"), score=0.9),
    )
    store = _FakeVectorStore(results=expected_results)
    retriever = EmbeddingVectorStoreRetriever(embedding_provider=provider, vector_store=store)
    metadata_filter = MetadataFilter.from_mapping({"genre": "music"})

    request = RetrievalRequest(
        query="What music did I listen to?",
        top_k=3,
        metadata_filter=metadata_filter,
    )
    results = retriever.retrieve(request)

    assert provider.queries == ["What music did I listen to?"]
    assert store.calls == [(query_embedding, 3, metadata_filter)]
    assert results is expected_results


@pytest.mark.parametrize("invalid_top_k", [0, -1, True])
def test_retrieval_request_rejects_invalid_top_k(invalid_top_k: int) -> None:
    with pytest.raises(RetrieverConfigurationError, match="top_k must be an integer greater than zero"):
        RetrievalRequest(query="valid query", top_k=invalid_top_k)


def test_retrieval_request_rejects_empty_query() -> None:
    with pytest.raises(RetrieverConfigurationError, match="query must be a non-empty string"):
        RetrievalRequest(query="")
