"""Opt-in sequential hybrid visibility against the actual shared lifecycle store."""

from collections.abc import Sequence

import pytest

from context_engine.retrieval.hybrid import (
    HybridConsistencyError,
    HybridRetriever,
    lifecycle_visibility_reader,
)
from context_engine.retrieval.retriever import EmbeddingVectorStoreRetriever, RetrievalRequest
from context_engine.retrieval.vector_store import SearchResult
from tests.integration.test_qdrant_lexical_integration import StoreFixture, setup_store, source
from tests.source_index_fixtures import FixtureEmbeddingProvider

# Reuse the native opt-in fixture, including isolated collection cleanup.
__all__ = ["setup_store"]


def test_hybrid_replacement_and_delete_visibility(setup_store: StoreFixture) -> None:
    store, coordinator, lexical, *_ = setup_store
    dense = EmbeddingVectorStoreRetriever(
        embedding_provider=FixtureEmbeddingProvider(), vector_store=store
    )
    hybrid = HybridRetriever(
        dense_retriever=dense,
        lexical_retriever=lexical,
        visibility_reader=lifecycle_visibility_reader(store),
    )
    coordinator.ingest(source("COBALT-742 old revision"))
    before = hybrid.retrieve(RetrievalRequest("COBALT-742", 5))
    assert before
    coordinator.ingest(source("COBALT-742 new revision"))
    after = hybrid.retrieve(RetrievalRequest("COBALT-742", 5))
    assert after and not {r.document.document_id for r in before} & {
        r.document.document_id for r in after
    }
    coordinator.delete_source("technical")
    assert not hybrid.retrieve(RetrievalRequest("COBALT-742", 5))


def test_completed_update_between_branches_is_rejected(setup_store: StoreFixture) -> None:
    store, coordinator, lexical, *_ = setup_store
    coordinator.ingest(source("COBALT-742 old revision"))
    dense = EmbeddingVectorStoreRetriever(
        embedding_provider=FixtureEmbeddingProvider(), vector_store=store
    )

    class MutatingDense:
        def retrieve(self, request: RetrievalRequest) -> Sequence[SearchResult]:
            results = dense.retrieve(request)
            coordinator.ingest(source("COBALT-742 new revision"))
            return results

    hybrid = HybridRetriever(
        dense_retriever=MutatingDense(),
        lexical_retriever=lexical,
        visibility_reader=lifecycle_visibility_reader(store),
    )
    with pytest.raises(HybridConsistencyError, match="changed"):
        hybrid.retrieve(RetrievalRequest("COBALT-742", 5))
