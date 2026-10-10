"""Controlled Qdrant boundary failures and complete representation writes."""

from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest

from context_engine.retrieval.embeddings import Document, Embedding
from context_engine.retrieval.lexical import (
    LexicalConfigurationError,
    LexicalIndexConfig,
    LexicalIndexError,
)
from context_engine.retrieval.qdrant_lexical_index import QdrantBM25ChunkStore, QdrantLexicalIndex
from context_engine.retrieval.retriever import RetrievalRequest
from context_engine.retrieval.source_store import (
    SourceIndexPhase,
    SourceIndexState,
    SourceIndexUnavailableError,
)
from context_engine.retrieval.vector_store import VectorStoreCollectionConfig, VectorStoreRecord


def config() -> VectorStoreCollectionConfig:
    return VectorStoreCollectionConfig(
        "lexical", "model", 2, index_version="m5-chunks-v1", index_configuration_id="a" * 64
    )


@pytest.mark.parametrize("timeout", [True, 0, -1, float("nan"), float("inf"), "bad"])
def test_invalid_timeout_before_service_access(timeout: Any) -> None:
    with pytest.raises(LexicalConfigurationError):
        QdrantBM25ChunkStore(config(), timeout_seconds=timeout)


@pytest.mark.parametrize(
    "url", ["https://example.qdrant.io", "ftp://localhost", "http://user:password@localhost"]
)
def test_remote_or_credentialed_endpoint_requires_explicit_policy(url: str) -> None:
    with pytest.raises(LexicalConfigurationError):
        QdrantBM25ChunkStore(config(), url=url)


def test_missing_dependency_is_actionable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable() -> Any:
        raise ImportError("missing qdrant-client")

    monkeypatch.setattr(
        "context_engine.retrieval.qdrant_lexical_index._load_qdrant_client_dependencies",
        unavailable,
    )
    with pytest.raises(LexicalIndexError, match="client >=1.16"):
        QdrantBM25ChunkStore(config())


def fake_store() -> QdrantBM25ChunkStore:
    store = object.__new__(QdrantBM25ChunkStore)
    store._config = config()
    store.lexical_config = LexicalIndexConfig()
    store._qdrant_models = SimpleNamespace(
        Document=lambda **kwargs: kwargs,
        PointStruct=lambda **kwargs: kwargs,
        FieldCondition=lambda **kwargs: kwargs,
        MatchValue=lambda **kwargs: kwargs,
        Filter=lambda **kwargs: kwargs,
    )
    return store


def test_complete_upsert_contains_both_vectors_and_canonical_payload() -> None:
    store = fake_store()
    writes = []
    store._client = SimpleNamespace(upsert=lambda **kwargs: writes.append(kwargs))
    document = Document.from_mapping(
        document_id="chunk",
        content="COBALT-742",
        metadata={
            "source_id": "source",
            "chunk_configuration_id": "chunker",
            "index_configuration_id": "a" * 64,
        },
    )
    store.upsert(
        (VectorStoreRecord(document, Embedding.from_sequence(vector=(1, 0), model_id="model")),)
    )
    point = writes[0]["points"][0]
    assert point["vector"]["dense"] == [1, 0]
    assert point["vector"]["lexical"]["model"] == "qdrant/bm25"
    assert point["vector"]["lexical"]["text"] == "COBALT-742"
    assert point["payload"]["metadata"] == document.metadata_as_mapping()
    assert writes[0]["wait"] is True


def test_pending_and_changed_manifest_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = fake_store()
    pending = SourceIndexState("s", "operation", SourceIndexPhase.READY)
    monkeypatch.setattr(store, "list_source_states", lambda: (pending,))
    with pytest.raises(SourceIndexUnavailableError):
        store.lexical_search(RetrievalRequest("query"))
    snapshots = iter(((replace(pending, phase=SourceIndexPhase.ACTIVE),), ()))
    monkeypatch.setattr(store, "list_source_states", lambda: next(snapshots))
    store._client = SimpleNamespace(query_points=lambda **kwargs: SimpleNamespace(points=[]))
    with pytest.raises(SourceIndexUnavailableError):
        store.lexical_search(RetrievalRequest("query"))


def test_search_service_error_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    store = fake_store()
    monkeypatch.setattr(store, "list_source_states", lambda: ())

    def unavailable(**kwargs: Any) -> None:
        raise RuntimeError("connection refused")

    store._client = SimpleNamespace(query_points=unavailable)
    with pytest.raises(LexicalIndexError, match="service availability"):
        store.lexical_search(RetrievalRequest("query"))


def test_direct_mutations_cannot_bypass_coordinator(monkeypatch: pytest.MonkeyPatch) -> None:
    from context_engine.retrieval.lexical import LexicalCompatibilityError

    store = fake_store()
    monkeypatch.setattr(store, "list_source_states", lambda: ())
    index = QdrantLexicalIndex(chunk_store=store)
    with pytest.raises(LexicalCompatibilityError):
        index.upsert((Document("chunk", "content"),))
    with pytest.raises(LexicalCompatibilityError):
        index.delete(("chunk",))


def test_dense_subclass_cannot_open_lexical_collection() -> None:
    from context_engine.retrieval.qdrant_vector_store import QdrantVectorStore
    from context_engine.retrieval.vector_store import VectorStoreCompatibilityError

    class InstrumentedDenseStore(QdrantVectorStore):
        pass

    store = object.__new__(InstrumentedDenseStore)
    store._config = config()
    store._client = SimpleNamespace(
        get_collection=lambda name: SimpleNamespace(
            config=SimpleNamespace(metadata={"_context_engine_lexical_config": "lexical"})
        )
    )
    with pytest.raises(VectorStoreCompatibilityError, match="combined writer"):
        store._validate_collection_compatibility()
