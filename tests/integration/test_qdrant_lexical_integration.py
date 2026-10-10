"""Opt-in native BM25 tokenizer and complete-point lifecycle verification."""

import os
from collections.abc import Generator
from typing import Any
from uuid import uuid4

import pytest

from context_engine.knowledge.chunking import ChunkingConfig, StructureAwareChunker
from context_engine.knowledge.ingestion import SourceIngestionCoordinator, indexing_configuration_id
from context_engine.knowledge.processing import SourceFormat, SourceInput
from context_engine.retrieval.lexical import (
    LexicalCompatibilityError,
    LexicalIndexConfig,
    LexicalRetriever,
)
from context_engine.retrieval.qdrant_lexical_index import QdrantBM25ChunkStore, QdrantLexicalIndex
from context_engine.retrieval.qdrant_vector_store import QdrantVectorStore
from context_engine.retrieval.retriever import RetrievalRequest
from context_engine.retrieval.source_store import SourceIndexUnavailableError
from context_engine.retrieval.vector_store import (
    MetadataFilter,
    VectorStoreCollectionConfig,
    VectorStoreCompatibilityError,
)
from tests.source_index_fixtures import CharacterCounter, FixtureEmbeddingProvider

StoreFixture = tuple[
    QdrantBM25ChunkStore,
    SourceIngestionCoordinator,
    LexicalRetriever,
    StructureAwareChunker,
    VectorStoreCollectionConfig,
    str,
]


@pytest.fixture
def setup_store() -> Generator[StoreFixture]:
    if os.getenv("CONTEXT_ENGINE_RUN_QDRANT_LEXICAL_INTEGRATION") != "1":
        pytest.skip("Set CONTEXT_ENGINE_RUN_QDRANT_LEXICAL_INTEGRATION=1 for native server tests.")
    chunker = StructureAwareChunker(
        ChunkingConfig(model_id="fixture-embedding", max_input_tokens=240, overlap_tokens=0),
        CharacterCounter(),
    )
    config = VectorStoreCollectionConfig(
        f"ce-lexical-it-{uuid4().hex}",
        "fixture-embedding",
        2,
        index_version="m5-chunks-v1",
        index_configuration_id=indexing_configuration_id(chunker, embedding_identity="fixture-v1"),
    )
    url = os.getenv("CONTEXT_ENGINE_QDRANT_URL", "http://localhost:6333")
    store = QdrantBM25ChunkStore(config, url=url)
    coordinator = SourceIngestionCoordinator(
        chunker=chunker,
        embedding_provider=FixtureEmbeddingProvider(),
        vector_store=store,
        embedding_identity="fixture-v1",
    )
    retriever = LexicalRetriever(lexical_index=QdrantLexicalIndex(chunk_store=store))
    yield store, coordinator, retriever, chunker, config, url
    store._client.delete_collection(config.collection_name)


def source(text: str, identity: str = "technical") -> SourceInput:
    return SourceInput(identity, identity + ".txt", text.encode(), SourceFormat.TEXT)


@pytest.mark.parametrize(
    "query",
    [
        "ToolApprovalRequiredError",
        "toolapprovalrequirederror",
        "search_documents",
        "search",
        "documents",
        "COBALT-742",
        "cobalt",
        "742",
        "context_engine/knowledge/ingestion.py",
        "context",
        "knowledge",
        "ingestion",
        "py",
        "café",
        "CAFÉ",
        "東京",
    ],
)
def test_native_tokenization_technical_names_and_unicode(
    setup_store: StoreFixture, query: str
) -> None:
    store, coordinator, retriever, *_ = setup_store
    outcome = coordinator.ingest(
        source(
            "ToolApprovalRequiredError search_documents COBALT-742 "
            "context_engine/knowledge/ingestion.py café 東京"
        )
    )
    assert outcome.status == "created"
    results = retriever.retrieve(RetrievalRequest(query))
    assert results and results[0].document.document_id in outcome.chunk_ids
    assert results[0].document.metadata_as_mapping()["source_id"] == "technical"
    assert results[0].diagnostics[0].score_kind == "bm25"


def test_native_camelcase_partial_and_ascii_folding_are_not_assumed(
    setup_store: StoreFixture,
) -> None:
    _, coordinator, retriever, *_ = setup_store
    coordinator.ingest(source("ToolApprovalRequiredError café"))
    assert retriever.retrieve(RetrievalRequest("Approval")) == ()
    assert retriever.retrieve(RetrievalRequest("cafe")) == ()
    assert retriever.retrieve(RetrievalRequest("---")) == ()


def test_restart_shorter_replacement_deletion_and_dense_preservation(
    setup_store: StoreFixture,
) -> None:
    store, coordinator, retriever, chunker, config, url = setup_store
    initial = coordinator.ingest(source("COBALT-742 stale information. " * 30))
    other = coordinator.ingest(source("COBALT-742 independent information", "other"))
    assert initial.status == other.status == "created"
    assert coordinator.ingest(source("COBALT-742 stale information. " * 30)).status == "unchanged"
    restarted = QdrantBM25ChunkStore(config, url=url)
    lifecycle = SourceIngestionCoordinator(
        chunker=chunker,
        embedding_provider=FixtureEmbeddingProvider(),
        vector_store=restarted,
        embedding_identity="fixture-v1",
    )
    replacement = lifecycle.ingest(source("COBALT-742 fresh"))
    assert replacement.status == "replaced" and replacement.chunk_count < initial.chunk_count
    assert not retriever.retrieve(RetrievalRequest("stale"))
    results = retriever.retrieve(
        RetrievalRequest(
            "COBALT-742", metadata_filter=MetadataFilter.from_mapping({"source_id": "technical"})
        )
    )
    assert len(results) == 1 and results[0].document.document_id in replacement.chunk_ids
    assert restarted.search(FixtureEmbeddingProvider().embed_query("COBALT"))
    assert lifecycle.delete_source("technical").status == "deleted"
    assert {
        r.document.metadata_as_mapping()["source_id"]
        for r in retriever.retrieve(RetrievalRequest("COBALT"))
    } == {"other"}
    with pytest.raises(VectorStoreCompatibilityError):
        QdrantVectorStore(config, url=url)
    with pytest.raises(LexicalCompatibilityError):
        QdrantBM25ChunkStore(config, lexical_config=LexicalIndexConfig(k=2), url=url)


@pytest.mark.parametrize("phase", ["upsert", "delete"])
def test_partial_write_or_delete_recovery_survives_restart(
    setup_store: StoreFixture, monkeypatch: pytest.MonkeyPatch, phase: str
) -> None:
    store, coordinator, retriever, chunker, config, url = setup_store
    coordinator.ingest(source("COBALT-742 old " * 30))
    operation = getattr(store, phase)

    def fail_after_write(*args: Any, **kwargs: Any) -> None:
        operation(*args, **kwargs)
        raise RuntimeError("Lost acknowledgement after write")

    monkeypatch.setattr(store, phase, fail_after_write)
    outcome = coordinator.ingest(source("COBALT-742 new"))
    assert outcome.requires_recovery
    with pytest.raises(SourceIndexUnavailableError):
        retriever.retrieve(RetrievalRequest("COBALT"))
    restarted = QdrantBM25ChunkStore(config, url=url)
    lifecycle = SourceIngestionCoordinator(
        chunker=chunker,
        embedding_provider=FixtureEmbeddingProvider(),
        vector_store=restarted,
        embedding_identity="fixture-v1",
    )
    assert lifecycle.recover()[0].recovered
    results = LexicalRetriever(lexical_index=QdrantLexicalIndex(chunk_store=restarted)).retrieve(
        RetrievalRequest("COBALT")
    )
    expected = "old" if phase == "upsert" else "new"
    assert results and all(expected in result.document.content for result in results)
