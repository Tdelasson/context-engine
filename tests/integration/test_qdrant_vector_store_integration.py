from __future__ import annotations

import os
import uuid

import pytest

from context_engine.retrieval import (
    Document,
    Embedding,
    MetadataFilter,
    QdrantVectorStore,
    VectorDistanceMetric,
    VectorStoreCollectionConfig,
    VectorStoreCompatibilityError,
    VectorStoreConfigurationError,
    VectorStoreRecord,
)


def _skip_unless_qdrant_integration_enabled() -> None:
    if os.getenv("CONTEXT_ENGINE_RUN_QDRANT_INTEGRATION") != "1":
        pytest.skip("Set CONTEXT_ENGINE_RUN_QDRANT_INTEGRATION=1 to run Qdrant integration tests.")


def _build_store(
    *,
    collection_name: str | None = None,
    embedding_model_id: str = "integration-model",
) -> QdrantVectorStore:
    resolved_collection_name = collection_name or f"context-engine-it-{uuid.uuid4().hex}"
    url = os.getenv("CONTEXT_ENGINE_QDRANT_URL", "http://localhost:6333")
    api_key = os.getenv("CONTEXT_ENGINE_QDRANT_API_KEY")
    timeout_seconds = float(os.getenv("CONTEXT_ENGINE_QDRANT_TIMEOUT_SECONDS", "5"))

    return QdrantVectorStore(
        VectorStoreCollectionConfig(
            collection_name=resolved_collection_name,
            embedding_model_id=embedding_model_id,
            dimensions=2,
            distance_metric=VectorDistanceMetric.COSINE,
        ),
        url=url,
        api_key=api_key,
        timeout_seconds=timeout_seconds,
    )


def _record(
    *,
    document_id: str,
    content: str,
    metadata: dict[str, object],
    vector: tuple[float, float],
) -> VectorStoreRecord:
    return VectorStoreRecord(
        document=Document.from_mapping(document_id=document_id, content=content, metadata=metadata),
        embedding=Embedding.from_sequence(
            vector=vector, model_id="integration-model", dimensions=2
        ),
    )


def _query(vector: tuple[float, float]) -> Embedding:
    return Embedding.from_sequence(vector=vector, model_id="integration-model", dimensions=2)


def test_qdrant_vector_store_upsert_search_filter_and_delete() -> None:
    _skip_unless_qdrant_integration_enabled()
    try:
        store = _build_store()
    except VectorStoreConfigurationError as exc:
        pytest.skip(f"Qdrant integration dependencies/runtime unavailable: {exc}")

    store.upsert(
        (
            _record(
                document_id="doc-1",
                content="Context Engine architecture notes",
                metadata={"topic": "architecture", "lang": "en"},
                vector=(1.0, 0.0),
            ),
            _record(
                document_id="doc-2",
                content="Vector search implementation details",
                metadata={"topic": "retrieval", "lang": "en"},
                vector=(0.6, 0.4),
            ),
            _record(
                document_id="doc-3",
                content="French architecture doc",
                metadata={"topic": "architecture", "lang": "fr"},
                vector=(0.7, 0.3),
            ),
        )
    )

    ranked = store.search(_query((1.0, 0.0)), top_k=2)
    assert [result.document.document_id for result in ranked] == ["doc-1", "doc-3"]

    filtered = store.search(
        _query((1.0, 0.0)),
        top_k=5,
        metadata_filter=MetadataFilter.from_mapping({"topic": "architecture", "lang": "fr"}),
    )
    assert [result.document.document_id for result in filtered] == ["doc-3"]

    store.delete(("doc-1",))
    after_delete = store.search(_query((1.0, 0.0)), top_k=5)
    assert "doc-1" not in {result.document.document_id for result in after_delete}


def test_qdrant_vector_store_rejects_collection_with_different_embedding_model() -> None:
    _skip_unless_qdrant_integration_enabled()
    collection_name = f"context-engine-it-{uuid.uuid4().hex}"
    try:
        _build_store(collection_name=collection_name, embedding_model_id="model-a")
    except VectorStoreConfigurationError as exc:
        pytest.skip(f"Qdrant integration dependencies/runtime unavailable: {exc}")

    with pytest.raises(VectorStoreCompatibilityError, match="embedding model mismatch"):
        _build_store(collection_name=collection_name, embedding_model_id="model-b")
