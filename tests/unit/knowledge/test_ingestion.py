"""Lifecycle invariants across source revisions, restarts, and partial failures."""

from collections.abc import Sequence
from dataclasses import replace

import pytest

from context_engine.knowledge.ingestion import IngestionStatus
from context_engine.knowledge.processing import SourceFormat, SourceInput
from context_engine.retrieval import Document, Embedding, VectorStoreCompatibilityError
from context_engine.retrieval.source_store import SourceIndexUnavailableError
from tests.source_index_fixtures import (
    FixtureEmbeddingProvider,
    MemorySourceStore,
    coordinator,
    fixture_chunker,
)


def source(
    text: bytes = b"First passage. " * 12, *, source_id: str = "source-a", name: str = "facts.txt"
) -> SourceInput:
    return SourceInput(source_id, name, text, SourceFormat.TEXT)


def test_create_repeat_replace_fewer_chunks_restart_and_delete() -> None:
    store = MemorySourceStore(fixture_chunker())
    provider = FixtureEmbeddingProvider()
    first = coordinator(store, provider).ingest(source())
    assert first.status is IngestionStatus.CREATED and first.chunk_count > 1
    unchanged = coordinator(store, provider).ingest(source())
    assert unchanged.status is IngestionStatus.UNCHANGED
    assert provider.calls == 1
    updated = coordinator(store, provider).ingest(source(b"New fact."))
    assert updated.status is IngestionStatus.REPLACED
    assert updated.chunk_count == 1 and updated.previous_chunk_count == first.chunk_count
    assert set(store.records) == set(updated.chunk_ids)
    assert not set(first.chunk_ids) & set(store.records)
    assert coordinator(store).list_sources()[0].chunk_ids == updated.chunk_ids
    deleted = coordinator(store).delete_source("source-a")
    assert deleted.status is IngestionStatus.DELETED
    assert not store.records and not coordinator(store).list_sources()
    assert coordinator(store).delete_source("source-a").status is IngestionStatus.UNCHANGED


def test_same_name_distinct_identity_and_other_source_survives_deletion() -> None:
    store = MemorySourceStore(fixture_chunker())
    ingestion = coordinator(store)
    first = ingestion.ingest(source())
    second = ingestion.ingest(source(source_id="source-b"))
    assert set(first.chunk_ids).isdisjoint(second.chunk_ids)
    ingestion.delete_source("source-a")
    assert set(store.records) == set(second.chunk_ids)
    assert (
        ingestion.ingest(source(source_id="source-b", name="renamed.txt")).status
        is IngestionStatus.FAILED
    )


@pytest.mark.parametrize("failure", ["processing", "chunking", "embedding", "read"])
def test_preparation_failures_preserve_previous_revision(
    failure: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = MemorySourceStore(fixture_chunker())
    provider = FixtureEmbeddingProvider()
    ingestion = coordinator(store, provider)
    original = ingestion.ingest(source())
    value = source(b"replacement")
    if failure == "processing":
        value = source(b"\xff")
    elif failure == "chunking":
        monkeypatch.setattr(ingestion.chunker.counter, "count_tokens", lambda *args, **kwargs: -1)
    elif failure == "embedding":
        provider.fail = True
    else:
        store.fail_on["read"] = 1
    result = ingestion.ingest(value)
    assert result.status is IngestionStatus.FAILED and not result.requires_recovery
    assert set(store.records) == set(original.chunk_ids)
    assert store.states["source-a"].active is not None


@pytest.mark.parametrize(
    ("operation", "count", "before", "new_visible"),
    [
        ("save", 1, False, False),
        ("save", 1, True, False),
        ("upsert", 1, False, False),
        ("save", 2, True, False),
        ("save", 2, False, True),
        ("delete", 1, False, True),
        ("save", 3, True, True),
        ("save", 3, False, True),
    ],
)
def test_partial_storage_failure_and_restart_recovery(
    operation: str, count: int, before: bool, new_visible: bool
) -> None:
    store = MemorySourceStore(fixture_chunker())
    old = coordinator(store).ingest(source())
    store.fail_on[operation] = count
    store.fail_before_save = before
    result = coordinator(store).ingest(source(b"Replacement fact. " * 5))
    assert result.status is IngestionStatus.FAILED and result.requires_recovery
    if store.states["source-a"].phase.value != "active":
        with pytest.raises(SourceIndexUnavailableError):
            store.search(Embedding.from_sequence(vector=(1, 1), model_id="fixture-embedding"))
    recovery = coordinator(store).recover()
    assert not any(item.requires_recovery for item in recovery)
    active = coordinator(store).list_sources()[0]
    assert set(store.records) == set(active.chunk_ids)
    if new_visible:
        assert active.chunk_ids != old.chunk_ids
        assert any("Replacement" in record.document.content for record in store.records.values())
    else:
        assert active.chunk_ids == old.chunk_ids
    assert coordinator(store).recover() == ()


def test_partial_creation_rollback_removes_orphan_chunks() -> None:
    store = MemorySourceStore(fixture_chunker())
    store.fail_on["upsert"] = 1
    assert coordinator(store).ingest(source()).requires_recovery
    recovered = coordinator(store).recover()[0]
    assert recovered.recovered and recovered.status is IngestionStatus.FAILED
    assert not store.records and not coordinator(store).list_sources()


def test_partial_deletion_recovery_is_idempotent_and_preserves_other_sources() -> None:
    store = MemorySourceStore(fixture_chunker())
    ingestion = coordinator(store)
    ingestion.ingest(source())
    other = ingestion.ingest(source(source_id="source-b"))
    store.fail_on["delete"] = 1
    assert ingestion.delete_source("source-a").requires_recovery
    store.fail_on["delete"] = 1
    assert coordinator(store).recover()[0].requires_recovery
    assert coordinator(store).recover()[0].status is IngestionStatus.DELETED
    assert set(store.records) == set(other.chunk_ids)


def test_config_changes_and_m4_collections_require_explicit_rebuild() -> None:
    store = MemorySourceStore(fixture_chunker())
    with pytest.raises(VectorStoreCompatibilityError):
        coordinator(store, chunker=fixture_chunker(limit=32))
    store.collection_config = replace(store.collection_config, index_version="m4-documents-v1")
    with pytest.raises(VectorStoreCompatibilityError):
        coordinator(store)


def test_incorrect_embedding_count_or_space_never_mutates_store() -> None:
    class BadProvider(FixtureEmbeddingProvider):
        def embed_documents(self, documents: Sequence[Document]) -> tuple[Embedding, ...]:
            return ()

    store = MemorySourceStore(fixture_chunker())
    assert coordinator(store, BadProvider()).ingest(source()).status is IngestionStatus.FAILED
    assert not store.states and not store.records


def test_pdf_chunk_provenance_and_diagnostics_survive_source_manifest() -> None:
    from tests.pdf_fixtures import make_pdf

    chunker = fixture_chunker(limit=128)
    store = MemorySourceStore(chunker)
    result = coordinator(store, chunker=chunker).ingest(
        SourceInput(
            "pdf", "facts.pdf", make_pdf(("Fact one", None, "Fact three")), SourceFormat.PDF
        )
    )
    assert result.status is IngestionStatus.CREATED
    assert result.diagnostics
    metadata = next(iter(store.records.values())).document.metadata_as_mapping()
    assert metadata["page_numbers"] == [1, 3]
    assert metadata["spans"]
    assert dict(coordinator(store, chunker=chunker).list_sources()[0].metadata)[
        "source_processing_diagnostics"
    ]


def test_incompatible_embedding_space_fails_before_pending_manifest() -> None:
    class WrongSpace(FixtureEmbeddingProvider):
        def embed_documents(self, documents: Sequence[Document]) -> tuple[Embedding, ...]:
            return tuple(
                Embedding.from_sequence(vector=(1, 1), model_id="other-model") for _ in documents
            )

    store = MemorySourceStore(fixture_chunker())
    outcome = coordinator(store, WrongSpace()).ingest(source())
    assert outcome.status is IngestionStatus.FAILED and outcome.error_phase == "embedding"
    assert not store.records and not store.states


def test_recovered_ready_revision_reports_persisted_processing_diagnostics() -> None:
    from tests.pdf_fixtures import make_pdf

    chunker = fixture_chunker(limit=128)
    store = MemorySourceStore(chunker)
    coordinator(store, chunker=chunker).ingest(
        SourceInput("pdf", "facts.pdf", make_pdf(("Old fact",)), SourceFormat.PDF)
    )
    store.fail_on["save"] = 2
    outcome = coordinator(store, chunker=chunker).ingest(
        SourceInput("pdf", "facts.pdf", make_pdf(("New fact", None)), SourceFormat.PDF)
    )
    assert outcome.requires_recovery
    recovered = coordinator(store, chunker=chunker).recover()[0]
    assert recovered.diagnostics == outcome.diagnostics
    assert recovered.status is IngestionStatus.REPLACED
