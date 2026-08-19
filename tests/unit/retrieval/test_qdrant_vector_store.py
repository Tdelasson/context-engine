from context_engine.retrieval.qdrant_vector_store import _qdrant_point_id_for_document_id


def test_qdrant_point_id_mapping_is_deterministic_per_collection() -> None:
    point_id_one = _qdrant_point_id_for_document_id(collection_name="docs", document_id="doc-1")
    point_id_two = _qdrant_point_id_for_document_id(collection_name="docs", document_id="doc-1")
    assert point_id_one == point_id_two


def test_qdrant_point_id_mapping_scopes_by_collection_name() -> None:
    point_id_one = _qdrant_point_id_for_document_id(collection_name="docs-a", document_id="doc-1")
    point_id_two = _qdrant_point_id_for_document_id(collection_name="docs-b", document_id="doc-1")
    assert point_id_one != point_id_two
