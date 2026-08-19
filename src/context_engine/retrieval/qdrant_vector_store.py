"""Qdrant-backed vector-store implementation."""

from __future__ import annotations

import importlib
import uuid
from collections.abc import Mapping, Sequence
from typing import Any, cast

from context_engine.retrieval.embeddings import Document, Embedding, normalize_document_metadata
from context_engine.retrieval.vector_store import (
    MetadataFilter,
    SearchResult,
    VectorDistanceMetric,
    VectorStore,
    VectorStoreCollectionConfig,
    VectorStoreCompatibilityError,
    VectorStoreConfigurationError,
    VectorStoreRecord,
)


class QdrantVectorStore(VectorStore):
    """Qdrant implementation of the provider-independent VectorStore contract."""

    def __init__(
        self,
        config: VectorStoreCollectionConfig,
        *,
        url: str = "http://localhost:6333",
        api_key: str | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        if timeout_seconds <= 0:
            raise VectorStoreConfigurationError("timeout_seconds must be greater than zero.")

        self._config = config
        self._qdrant_models = _load_qdrant_models()
        self._client = _build_qdrant_client(
            url=url, api_key=api_key, timeout_seconds=timeout_seconds
        )
        self._ensure_collection()

    def upsert(self, records: Sequence[VectorStoreRecord]) -> None:
        if not records:
            return

        points: list[Any] = []
        for record in records:
            self._config.ensure_embedding_compatible(record.embedding)
            points.append(
                self._qdrant_models.PointStruct(
                    id=_qdrant_point_id_for_document_id(
                        collection_name=self._config.collection_name,
                        document_id=record.document.document_id,
                    ),
                    vector=list(record.embedding.vector),
                    payload={
                        "document_id": record.document.document_id,
                        "content": record.document.content,
                        "metadata": record.document.metadata_as_mapping(),
                        "embedding_model_id": record.embedding.model_id,
                        "embedding_dimensions": record.embedding.dimensions,
                    },
                )
            )

        self._client.upsert(
            collection_name=self._config.collection_name,
            points=points,
            wait=True,
        )

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
        query_filter = self._build_qdrant_filter(metadata_filter)

        scored_points = self._client.search(
            collection_name=self._config.collection_name,
            query_vector=list(query_embedding.vector),
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )
        return tuple(self._build_search_result(point) for point in scored_points)

    def delete(self, document_ids: Sequence[str]) -> None:
        active_ids = [document_id for document_id in document_ids if document_id]
        if not active_ids:
            return
        point_ids = [
            _qdrant_point_id_for_document_id(
                collection_name=self._config.collection_name, document_id=document_id
            )
            for document_id in active_ids
        ]
        self._client.delete(
            collection_name=self._config.collection_name,
            points_selector=self._qdrant_models.PointIdsList(points=point_ids),
            wait=True,
        )

    def _ensure_collection(self) -> None:
        if self._client.collection_exists(self._config.collection_name):
            self._validate_collection_compatibility()
            return

        self._client.create_collection(
            collection_name=self._config.collection_name,
            vectors_config=self._qdrant_models.VectorParams(
                size=self._config.dimensions,
                distance=self._to_qdrant_distance(self._config.distance_metric),
            ),
        )

    def _validate_collection_compatibility(self) -> None:
        collection = self._client.get_collection(self._config.collection_name)
        vectors_config = cast(Any, collection).config.params.vectors
        vector_params = self._extract_vector_params(vectors_config)
        if vector_params is None:
            raise VectorStoreCompatibilityError(
                f"Collection '{self._config.collection_name}' is not a compatible dense vector "
                "collection."
            )

        existing_dimensions = int(vector_params.size)
        if existing_dimensions != self._config.dimensions:
            raise VectorStoreCompatibilityError(
                "Collection dimensionality mismatch: "
                f"expected {self._config.dimensions} but found {existing_dimensions}."
            )

        expected_distance = self._to_qdrant_distance(self._config.distance_metric)
        if vector_params.distance != expected_distance:
            raise VectorStoreCompatibilityError(
                "Collection distance metric mismatch: "
                f"expected {self._config.distance_metric.value} but found {vector_params.distance}."
            )

    def _extract_vector_params(self, vectors_config: Any) -> Any | None:
        if hasattr(vectors_config, "size") and hasattr(vectors_config, "distance"):
            return vectors_config
        if isinstance(vectors_config, Mapping):
            for value in vectors_config.values():
                if hasattr(value, "size") and hasattr(value, "distance"):
                    return value
        return None

    def _build_qdrant_filter(self, metadata_filter: MetadataFilter | None) -> Any:
        must_conditions = [
            self._qdrant_models.FieldCondition(
                key="embedding_model_id",
                match=self._qdrant_models.MatchValue(value=self._config.embedding_model_id),
            )
        ]
        if metadata_filter is not None:
            for metadata_key, metadata_value in metadata_filter.equals:
                must_conditions.append(
                    self._qdrant_models.FieldCondition(
                        key=f"metadata.{metadata_key}",
                        match=self._qdrant_models.MatchValue(value=metadata_value),
                    )
                )
        return self._qdrant_models.Filter(must=must_conditions)

    def _build_search_result(self, point: Any) -> SearchResult:
        payload = cast(dict[str, Any], point.payload or {})
        metadata_payload = payload.get("metadata")
        metadata_mapping: Mapping[str, object]
        if isinstance(metadata_payload, Mapping):
            metadata_mapping = cast(Mapping[str, object], metadata_payload)
        else:
            metadata_mapping = {}

        document_id = payload.get("document_id")
        content = payload.get("content")
        if not isinstance(document_id, str) or not isinstance(content, str):
            raise VectorStoreCompatibilityError("Qdrant payload missing required document fields.")

        document = Document(
            document_id=document_id,
            content=content,
            metadata=normalize_document_metadata(metadata_mapping),
        )
        return SearchResult(document=document, score=float(point.score))

    def _to_qdrant_distance(self, metric: VectorDistanceMetric) -> Any:
        if metric is VectorDistanceMetric.COSINE:
            return self._qdrant_models.Distance.COSINE
        if metric is VectorDistanceMetric.DOT:
            return self._qdrant_models.Distance.DOT
        if metric is VectorDistanceMetric.EUCLIDEAN:
            return self._qdrant_models.Distance.EUCLID
        raise VectorStoreConfigurationError(f"Unsupported distance metric: {metric}")


def _build_qdrant_client(*, url: str, api_key: str | None, timeout_seconds: float) -> Any:
    qdrant_client_cls, _ = _load_qdrant_client_dependencies()
    return qdrant_client_cls(url=url, api_key=api_key, timeout=timeout_seconds)


def _load_qdrant_models() -> Any:
    _, qdrant_models = _load_qdrant_client_dependencies()
    return qdrant_models


def _load_qdrant_client_dependencies() -> tuple[Any, Any]:
    try:
        qdrant_client_module = importlib.import_module("qdrant_client")
        qdrant_http_models_module = importlib.import_module("qdrant_client.http.models")
    except ImportError as exc:
        raise VectorStoreConfigurationError(
            "qdrant-client is required for QdrantVectorStore. Install it with: "
            "pip install qdrant-client"
        ) from exc
    return qdrant_client_module.QdrantClient, qdrant_http_models_module


def _qdrant_point_id_for_document_id(*, collection_name: str, document_id: str) -> str:
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, f"context-engine:qdrant:{collection_name}")
    return str(uuid.uuid5(namespace, document_id))
