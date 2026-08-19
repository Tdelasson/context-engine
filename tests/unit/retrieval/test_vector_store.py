from __future__ import annotations

from collections.abc import Sequence
from math import sqrt

import pytest

from context_engine.retrieval import (
    Document,
    Embedding,
    MetadataFilter,
    SearchResult,
    VectorStore,
    VectorStoreCollectionConfig,
    VectorStoreCompatibilityError,
    VectorStoreConfigurationError,
    VectorStoreRecord,
)


class _InMemoryVectorStore(VectorStore):
    def __init__(self, config: VectorStoreCollectionConfig) -> None:
        self._config = config
        self._records: dict[str, VectorStoreRecord] = {}

    def upsert(self, records: Sequence[VectorStoreRecord]) -> None:
        for record in records:
            self._config.ensure_embedding_compatible(record.embedding)
            self._records[record.document.document_id] = record

    def search(
        self,
        query_embedding: Embedding,
        *,
        top_k: int = 5,
        metadata_filter: MetadataFilter | None = None,
    ) -> tuple[SearchResult, ...]:
        if top_k <= 0:
            raise VectorStoreConfigurationError("top_k must be greater than zero.")
        self._config.ensure_embedding_compatible(query_embedding)

        scored: list[SearchResult] = []
        for record in self._records.values():
            if metadata_filter is not None and not _matches_filter(
                record.document.metadata_as_mapping(), metadata_filter
            ):
                continue
            scored.append(
                SearchResult(
                    document=record.document,
                    score=_cosine_similarity(query_embedding.vector, record.embedding.vector),
                )
            )
        scored.sort(key=lambda result: (-result.score, result.document.document_id))
        return tuple(scored[:top_k])

    def delete(self, document_ids: Sequence[str]) -> None:
        for document_id in document_ids:
            self._records.pop(document_id, None)


def _matches_filter(metadata: dict[str, object], metadata_filter: MetadataFilter) -> bool:
    return all(metadata.get(key) == value for key, value in metadata_filter.equals)


def _cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    dot = sum(lhs * rhs for lhs, rhs in zip(left, right, strict=True))
    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def _record(
    *,
    document_id: str,
    content: str,
    metadata: dict[str, object] | None = None,
    vector: tuple[float, ...],
    model_id: str = "mini-model",
) -> VectorStoreRecord:
    return VectorStoreRecord(
        document=Document.from_mapping(
            document_id=document_id,
            content=content,
            metadata={} if metadata is None else metadata,
        ),
        embedding=Embedding.from_sequence(vector=vector, model_id=model_id, dimensions=2),
    )


def _query(vector: tuple[float, ...], model_id: str = "mini-model") -> Embedding:
    return Embedding.from_sequence(vector=vector, model_id=model_id, dimensions=2)


def _build_store() -> _InMemoryVectorStore:
    return _InMemoryVectorStore(
        VectorStoreCollectionConfig(
            collection_name="unit-test-collection",
            embedding_model_id="mini-model",
            dimensions=2,
        )
    )


def test_in_memory_vector_store_satisfies_vector_store_protocol() -> None:
    store = _build_store()
    assert isinstance(store, VectorStore)


def test_vector_store_returns_ranked_search_results_with_top_k() -> None:
    store = _build_store()
    store.upsert(
        (
            _record(document_id="doc-1", content="alpha", vector=(1.0, 0.0)),
            _record(document_id="doc-2", content="beta", vector=(0.2, 0.8)),
            _record(document_id="doc-3", content="gamma", vector=(0.8, 0.2)),
        )
    )

    results = store.search(_query((1.0, 0.0)), top_k=2)

    assert [result.document.document_id for result in results] == ["doc-1", "doc-3"]
    assert len(results) == 2


def test_vector_store_applies_provider_independent_metadata_filter() -> None:
    store = _build_store()
    store.upsert(
        (
            _record(
                document_id="doc-1",
                content="jazz",
                metadata={"genre": "music", "lang": "en"},
                vector=(0.9, 0.1),
            ),
            _record(
                document_id="doc-2",
                content="python",
                metadata={"genre": "code", "lang": "en"},
                vector=(0.8, 0.2),
            ),
            _record(
                document_id="doc-3",
                content="electro",
                metadata={"genre": "music", "lang": "fr"},
                vector=(0.7, 0.3),
            ),
        )
    )

    results = store.search(
        _query((1.0, 0.0)),
        metadata_filter=MetadataFilter.from_mapping({"genre": "music", "lang": "fr"}),
    )

    assert [result.document.document_id for result in results] == ["doc-3"]


def test_vector_store_upsert_preserves_stable_document_id() -> None:
    store = _build_store()
    store.upsert((_record(document_id="doc-1", content="v1", vector=(0.1, 0.9)),))
    store.upsert((_record(document_id="doc-1", content="v2", vector=(0.9, 0.1)),))

    results = store.search(_query((1.0, 0.0)))

    assert [result.document.document_id for result in results] == ["doc-1"]
    assert results[0].document.content == "v2"


def test_vector_store_delete_removes_records_by_document_id() -> None:
    store = _build_store()
    store.upsert(
        (
            _record(document_id="doc-1", content="one", vector=(1.0, 0.0)),
            _record(document_id="doc-2", content="two", vector=(0.0, 1.0)),
        )
    )
    store.delete(("doc-1",))

    results = store.search(_query((1.0, 0.0)))

    assert [result.document.document_id for result in results] == ["doc-2"]


def test_vector_store_rejects_incompatible_embedding_model() -> None:
    store = _build_store()
    with pytest.raises(VectorStoreCompatibilityError, match="Embedding model mismatch"):
        store.upsert(
            (_record(document_id="doc-1", content="alpha", vector=(1.0, 0.0), model_id="x"),)
        )


def test_vector_store_rejects_incompatible_embedding_dimensions() -> None:
    store = _build_store()
    with pytest.raises(VectorStoreCompatibilityError, match="dimensionality mismatch"):
        store.upsert(
            (
                VectorStoreRecord(
                    document=Document.from_mapping(document_id="doc-1", content="alpha"),
                    embedding=Embedding.from_sequence(
                        vector=(1.0, 0.0, 0.1),
                        model_id="mini-model",
                        dimensions=3,
                    ),
                ),
            )
        )


def test_vector_store_rejects_invalid_top_k() -> None:
    store = _build_store()
    with pytest.raises(VectorStoreConfigurationError, match="top_k must be greater than zero"):
        store.search(_query((1.0, 0.0)), top_k=0)
