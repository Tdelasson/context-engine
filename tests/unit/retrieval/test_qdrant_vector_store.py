from types import SimpleNamespace

import pytest

from context_engine.retrieval.embeddings import Embedding
from context_engine.retrieval.qdrant_vector_store import (
    QdrantVectorStore,
    _qdrant_point_id_for_document_id,
)
from context_engine.retrieval.vector_store import (
    VectorStoreCollectionConfig,
    VectorStoreCompatibilityError,
)


def test_qdrant_point_id_mapping_is_deterministic_per_collection() -> None:
    point_id_one = _qdrant_point_id_for_document_id(collection_name="docs", document_id="doc-1")
    point_id_two = _qdrant_point_id_for_document_id(collection_name="docs", document_id="doc-1")
    assert point_id_one == point_id_two


def test_qdrant_point_id_mapping_scopes_by_collection_name() -> None:
    point_id_one = _qdrant_point_id_for_document_id(collection_name="docs-a", document_id="doc-1")
    point_id_two = _qdrant_point_id_for_document_id(collection_name="docs-b", document_id="doc-1")
    assert point_id_one != point_id_two


def test_extract_vector_params_rejects_named_vector_config() -> None:
    store = object.__new__(QdrantVectorStore)
    vectors_config = {"default": SimpleNamespace(size=2, distance="Cosine")}

    with pytest.raises(VectorStoreCompatibilityError, match="Named-vector or multi-vector"):
        store._extract_vector_params(vectors_config)


def test_search_uses_query_points_and_query_response_points() -> None:
    class _StubClient:
        def __init__(self) -> None:
            self.kwargs: dict[str, object] | None = None

        def query_points(self, **kwargs: object) -> SimpleNamespace:
            self.kwargs = kwargs
            return SimpleNamespace(
                points=[
                    SimpleNamespace(
                        score=0.75,
                        payload={
                            "document_id": "doc-1",
                            "content": "content",
                            "metadata": {"topic": "architecture"},
                        },
                    )
                ]
            )

    store = object.__new__(QdrantVectorStore)
    store._config = VectorStoreCollectionConfig(
        collection_name="docs", embedding_model_id="model-a", dimensions=2
    )
    store._client = _StubClient()
    store._qdrant_models = SimpleNamespace(
        FieldCondition=lambda **kwargs: kwargs,
        MatchValue=lambda **kwargs: kwargs,
        Filter=lambda **kwargs: kwargs,
    )

    results = store.search(
        Embedding.from_sequence(vector=(1.0, 0.0), model_id="model-a", dimensions=2),
        top_k=3,
    )

    assert [result.document.document_id for result in results] == ["doc-1"]
    assert store._client.kwargs == {
        "collection_name": "docs",
        "query": [1.0, 0.0],
        "query_filter": {
            "must": [
                {
                    "key": "embedding_model_id",
                    "match": {"value": "model-a"},
                }
            ]
        },
        "limit": 3,
        "with_payload": True,
        "with_vectors": False,
    }
