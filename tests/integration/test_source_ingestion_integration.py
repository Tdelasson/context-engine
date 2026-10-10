"""Opt-in Qdrant lifecycle tests with deterministic embeddings and exact token counts."""

import os
from collections.abc import Iterator, Sequence
from dataclasses import replace
from uuid import uuid4

import pytest

from context_engine.knowledge.ingestion import IngestionStatus, SourceIngestionCoordinator
from context_engine.knowledge.processing import SourceFormat, SourceInput
from context_engine.retrieval import (
    MetadataFilter,
    QdrantVectorStore,
    VectorStoreCompatibilityError,
    VectorStoreRecord,
)
from context_engine.retrieval.source_store import SourceIndexUnavailableError
from tests.source_index_fixtures import FixtureEmbeddingProvider, MemorySourceStore, fixture_chunker


class FaultStore(QdrantVectorStore):
    fail_upsert = False
    fail_delete = False

    def upsert(self, records: Sequence[VectorStoreRecord]) -> None:
        if self.fail_upsert:
            self.fail_upsert = False
            super().upsert(records[:1])
            raise RuntimeError("partial real upsert")
        super().upsert(records)

    def delete(self, document_ids: Sequence[str]) -> None:
        if self.fail_delete:
            self.fail_delete = False
            super().delete(document_ids[:1])
            raise RuntimeError("partial real delete")
        super().delete(document_ids)


@pytest.fixture
def store() -> Iterator[FaultStore]:
    if os.getenv("CONTEXT_ENGINE_RUN_QDRANT_INTEGRATION") != "1":
        pytest.skip("Set CONTEXT_ENGINE_RUN_QDRANT_INTEGRATION=1 for source lifecycle integration.")
    pytest.importorskip("qdrant_client")
    config = replace(
        MemorySourceStore(fixture_chunker()).collection_config,
        collection_name=f"context-engine-source-it-{uuid4().hex}",
    )
    actual = FaultStore(config, url=os.getenv("CONTEXT_ENGINE_QDRANT_URL", "http://localhost:6333"))
    try:
        yield actual
    finally:
        actual._client.delete_collection(config.collection_name)
        actual._client.close()


def ingestion(store: QdrantVectorStore) -> SourceIngestionCoordinator:
    return SourceIngestionCoordinator(
        chunker=fixture_chunker(),
        embedding_provider=FixtureEmbeddingProvider(),
        vector_store=store,
        embedding_identity="fixture-v1",
    )


def reopen(store: QdrantVectorStore) -> QdrantVectorStore:
    return QdrantVectorStore(
        store.collection_config, url=os.getenv("CONTEXT_ENGINE_QDRANT_URL", "http://localhost:6333")
    )


def source(text: bytes, source_id: str = "facts") -> SourceInput:
    return SourceInput(source_id, "facts.txt", text, SourceFormat.TEXT)


def test_live_source_revision_replacement_restart_and_delete(store: FaultStore) -> None:
    coordinator = ingestion(store)
    original = source(b"Original fact. " * 10)
    created = coordinator.ingest(original)
    assert created.status is IngestionStatus.CREATED and created.chunk_count > 1
    reopened = reopen(store)
    try:
        restarted = ingestion(reopened)
        assert restarted.ingest(original).status is IngestionStatus.UNCHANGED
        other = restarted.ingest(source(b"Other source fact", "other"))
        replacement = restarted.ingest(source(b"Replacement fact."))
        assert replacement.status is IngestionStatus.REPLACED and replacement.chunk_count == 1
        results = reopened.search(FixtureEmbeddingProvider().embed_query("fact"), top_k=100)
        assert {item.document.document_id for item in results} == set(
            replacement.chunk_ids + other.chunk_ids
        )
        match = next(
            item.document for item in results if item.document.document_id in replacement.chunk_ids
        )
        assert match.metadata_as_mapping()["spans"]
        assert match.metadata_as_mapping()["source_id"] == "facts"
        assert restarted.delete_source("facts").status is IngestionStatus.DELETED
        assert restarted.delete_source("facts").status is IngestionStatus.UNCHANGED
        remaining = reopened.search(FixtureEmbeddingProvider().embed_query("fact"), top_k=100)
        assert {item.document.document_id for item in remaining} == set(other.chunk_ids)
        with pytest.raises(VectorStoreCompatibilityError):
            QdrantVectorStore(
                replace(store.collection_config, index_configuration_id="incompatible"),
                url=os.getenv("CONTEXT_ENGINE_QDRANT_URL", "http://localhost:6333"),
            )
        with pytest.raises(VectorStoreCompatibilityError):
            QdrantVectorStore(
                replace(
                    store.collection_config,
                    index_version="m4-documents-v1",
                    index_configuration_id=None,
                ),
                url=os.getenv("CONTEXT_ENGINE_QDRANT_URL", "http://localhost:6333"),
            )
    finally:
        reopened._client.close()


@pytest.mark.parametrize("failure", ["upsert", "delete"])
def test_live_partial_write_recovery_after_application_restart(
    store: FaultStore, failure: str
) -> None:
    initial = ingestion(store).ingest(source(b"Original fact. " * 10))
    store.fail_upsert = failure == "upsert"
    store.fail_delete = failure == "delete"
    outcome = ingestion(store).ingest(source(b"Replacement passage. " * 5))
    assert outcome.status is IngestionStatus.FAILED and outcome.requires_recovery
    with pytest.raises(SourceIndexUnavailableError):
        store.search(FixtureEmbeddingProvider().embed_query("fact"))
    reopened = reopen(store)
    try:
        recovery = ingestion(reopened).recover()
        assert recovery and not recovery[0].requires_recovery
        current = ingestion(reopened).list_sources()[0]
        results = reopened.search(
            FixtureEmbeddingProvider().embed_query("fact"),
            top_k=100,
            metadata_filter=MetadataFilter.from_mapping({"source_id": "facts"}),
        )
        assert {item.document.document_id for item in results} == set(current.chunk_ids)
        assert (current.chunk_ids == initial.chunk_ids) == (failure == "upsert")
    finally:
        reopened._client.close()
