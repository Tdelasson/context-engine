from types import SimpleNamespace

import pytest

from context_engine.retrieval.qdrant_vector_store import (
    QdrantVectorStore,
    _qdrant_point_id_for_document_id,
)
from context_engine.retrieval.vector_store import VectorStoreCompatibilityError


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
