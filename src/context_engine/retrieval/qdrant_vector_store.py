"""Qdrant-backed vector-store implementation."""

from __future__ import annotations

import importlib
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from typing import Any, cast

from context_engine.retrieval.embeddings import Document, Embedding, normalize_document_metadata
from context_engine.retrieval.source_store import (
    SourceIndexPhase,
    SourceIndexRevision,
    SourceIndexState,
    SourceIndexUnavailableError,
)
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

_COLLECTION_METADATA_KEY = "_context_engine_collection_config"


class QdrantVectorStore(VectorStore):
    """Qdrant implementation of the provider-independent VectorStore contract."""

    _supports_lexical_vectors = False

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

    @property
    def collection_config(self) -> VectorStoreCollectionConfig:
        return self._config

    def list_source_states(self) -> tuple[SourceIndexState, ...]:
        if self._config.index_version != "m5-chunks-v1":
            raise VectorStoreCompatibilityError("Source lifecycle requires an M5 collection.")
        states: list[SourceIndexState] = []
        offset = None
        while True:
            points, offset = self._client.scroll(
                collection_name=self._config.collection_name,
                scroll_filter=self._qdrant_models.Filter(
                    must=[
                        self._qdrant_models.FieldCondition(
                            key="_ce_record_kind",
                            match=self._qdrant_models.MatchValue(value="source_state"),
                        )
                    ]
                ),
                offset=offset,
                limit=128,
                with_payload=True,
                with_vectors=False,
            )
            for point in points:
                state = _decode_source_state(point.payload)
                for revision in (state.active, state.target):
                    if (
                        revision is not None
                        and revision.configuration_id != self._config.index_configuration_id
                    ):
                        raise VectorStoreCompatibilityError(
                            "Persisted source configuration mismatch; explicit repair required."
                        )
                states.append(state)
            if offset is None:
                return tuple(sorted(states, key=lambda state: state.source_id))

    def save_source_state(self, state: SourceIndexState) -> None:
        if self._config.index_version != "m5-chunks-v1":
            raise VectorStoreCompatibilityError("Source lifecycle requires an M5 collection.")
        for revision in (state.active, state.target):
            if (
                revision is not None
                and revision.configuration_id != self._config.index_configuration_id
            ):
                raise VectorStoreCompatibilityError(
                    "Source indexing identity mismatch; rebuild required."
                )
        self._client.upsert(
            collection_name=self._config.collection_name,
            points=[
                self._qdrant_models.PointStruct(
                    id=str(
                        uuid.uuid5(
                            uuid.NAMESPACE_URL,
                            f"context-engine:source-state:{self._config.collection_name}:{state.source_id}",
                        )
                    ),
                    vector=self._point_vectors([0.0] * self._config.dimensions),
                    payload={"_ce_record_kind": "source_state", "state": asdict(state)},
                )
            ],
            wait=True,
        )

    def _search_snapshot(self) -> tuple[SourceIndexState, ...]:
        if self._config.index_version != "m5-chunks-v1":
            return ()
        states = self.list_source_states()
        if any(state.phase is not SourceIndexPhase.ACTIVE for state in states):
            raise SourceIndexUnavailableError("Source index has pending operations; run recovery.")
        return states

    def upsert(self, records: Sequence[VectorStoreRecord]) -> None:
        if not records:
            return

        points: list[Any] = []
        for record in records:
            self._config.ensure_embedding_compatible(record.embedding)
            metadata = record.document.metadata_as_mapping()
            if self._config.index_version == "m5-chunks-v1" and (
                metadata.get("index_configuration_id") != self._config.index_configuration_id
                or not metadata.get("source_id")
                or not metadata.get("chunk_configuration_id")
            ):
                raise VectorStoreCompatibilityError(
                    "M5 requires compatible chunk records; rebuild required."
                )
            points.append(
                self._qdrant_models.PointStruct(
                    id=_qdrant_point_id_for_document_id(
                        collection_name=self._config.collection_name,
                        document_id=record.document.document_id,
                    ),
                    vector=self._point_vectors(list(record.embedding.vector), record.document),
                    payload={
                        "_ce_record_kind": "chunk"
                        if self._config.index_version == "m5-chunks-v1"
                        else "document",
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
        snapshot = self._search_snapshot()
        query_filter = self._build_qdrant_filter(metadata_filter)

        response = self._client.query_points(
            collection_name=self._config.collection_name,
            query=list(query_embedding.vector),
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
            **self._dense_query_options(),
        )
        if snapshot != self._search_snapshot():
            raise SourceIndexUnavailableError("Source index changed during search; retry.")
        return tuple(self._build_search_result(point) for point in response.points)

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

    def _point_vectors(self, dense: list[float], document: Document | None = None) -> Any:
        return dense

    def _dense_query_options(self) -> dict[str, object]:
        return {}

    def _ensure_collection(self) -> None:
        if self._client.collection_exists(self._config.collection_name):
            self._validate_collection_compatibility()
            return

        create_collection_kwargs: dict[str, Any] = {
            "collection_name": self._config.collection_name,
            "vectors_config": self._qdrant_models.VectorParams(
                size=self._config.dimensions,
                distance=self._to_qdrant_distance(self._config.distance_metric),
            ),
            "metadata": self._collection_config_payload(),
        }
        self._client.create_collection(**create_collection_kwargs)

    def _validate_collection_compatibility(self) -> None:
        collection = self._client.get_collection(self._config.collection_name)
        if (
            not self._supports_lexical_vectors
            and _extract_collection_metadata(collection).get("_context_engine_lexical_config")
            is not None
        ):
            raise VectorStoreCompatibilityError(
                "Lexical collection requires its combined writer; dense-only writes are unsafe."
            )
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

        config_embedding_model_id = self._read_collection_embedding_model_id()
        if config_embedding_model_id is None:
            raise VectorStoreCompatibilityError(
                "Collection compatibility metadata missing embedding model identity."
            )
        if config_embedding_model_id != self._config.embedding_model_id:
            raise VectorStoreCompatibilityError(
                "Collection embedding model mismatch: "
                f"expected '{self._config.embedding_model_id}' but found "
                f"'{config_embedding_model_id}'."
            )
        payload = _extract_collection_metadata(collection).get(_COLLECTION_METADATA_KEY)
        assert isinstance(payload, Mapping)
        if (
            payload.get("index_version", "m4-documents-v1") != self._config.index_version
            or payload.get("index_configuration_id") != self._config.index_configuration_id
        ):
            raise VectorStoreCompatibilityError(
                "Collection indexing configuration mismatch; select a new collection and rebuild."
            )

    def _extract_vector_params(self, vectors_config: Any) -> Any | None:
        if hasattr(vectors_config, "size") and hasattr(vectors_config, "distance"):
            return vectors_config
        if isinstance(vectors_config, Mapping):
            raise VectorStoreCompatibilityError(
                "Named-vector or multi-vector Qdrant collections are not supported. "
                "Configure a single dense vector collection."
            )
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
        if self._config.index_version == "m5-chunks-v1":
            must_conditions.append(
                self._qdrant_models.FieldCondition(
                    key="_ce_record_kind", match=self._qdrant_models.MatchValue(value="chunk")
                )
            )
        return self._qdrant_models.Filter(must=must_conditions)

    def _read_collection_embedding_model_id(self) -> str | None:
        collection = self._client.get_collection(self._config.collection_name)
        collection_metadata = _extract_collection_metadata(cast(Any, collection))
        config_payload = collection_metadata.get(_COLLECTION_METADATA_KEY)
        if isinstance(config_payload, Mapping):
            embedding_model_id = config_payload.get("embedding_model_id")
            if isinstance(embedding_model_id, str) and embedding_model_id:
                return embedding_model_id
        return None

    def _collection_config_payload(self) -> dict[str, object]:
        return {
            _COLLECTION_METADATA_KEY: {
                "embedding_model_id": self._config.embedding_model_id,
                "embedding_dimensions": self._config.dimensions,
                "index_version": self._config.index_version,
                "index_configuration_id": self._config.index_configuration_id,
            }
        }

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


def _extract_collection_metadata(collection: Any) -> Mapping[str, object]:
    config = getattr(collection, "config", None)
    if config is None:
        return {}
    metadata = getattr(config, "metadata", None)
    if isinstance(metadata, Mapping):
        return cast(Mapping[str, object], metadata)
    return {}


def _decode_source_state(payload: Any) -> SourceIndexState:
    try:
        raw = payload["state"]

        def revision(value: Any) -> SourceIndexRevision | None:
            if value is None:
                return None
            return SourceIndexRevision(
                source_id=value["source_id"],
                source_name=value["source_name"],
                source_kind=value["source_kind"],
                content_sha256=value["content_sha256"],
                configuration_id=value["configuration_id"],
                chunk_ids=tuple(value["chunk_ids"]),
                metadata=tuple((key, item) for key, item in value["metadata"]),
            )

        return SourceIndexState(
            source_id=raw["source_id"],
            operation_id=raw["operation_id"],
            phase=SourceIndexPhase(raw["phase"]),
            active=revision(raw["active"]),
            target=revision(raw["target"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise VectorStoreCompatibilityError(
            "Malformed source lifecycle state; explicit repair required."
        ) from exc
