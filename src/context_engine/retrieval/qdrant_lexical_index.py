"""Native local Qdrant BM25 with one owner for complete chunk points."""

from collections.abc import Mapping, Sequence
from dataclasses import replace
from math import isfinite
from typing import Any
from urllib.parse import urlparse

from context_engine.retrieval.embeddings import Document
from context_engine.retrieval.lexical import (
    LexicalCompatibilityError,
    LexicalConfigurationError,
    LexicalIndexConfig,
    LexicalIndexError,
    validate_lexical_request,
)
from context_engine.retrieval.qdrant_vector_store import (
    QdrantVectorStore,
    _extract_collection_metadata,
    _load_qdrant_client_dependencies,
    _qdrant_point_id_for_document_id,
)
from context_engine.retrieval.retriever import RetrievalRequest
from context_engine.retrieval.source_store import SourceIndexUnavailableError
from context_engine.retrieval.vector_store import (
    SearchResult,
    VectorStoreCollectionConfig,
    VectorStoreCompatibilityError,
)

_LEXICAL_METADATA_KEY = "_context_engine_lexical_config"


class QdrantBM25ChunkStore(QdrantVectorStore):
    """Combined dense/sparse point writer used by SourceIngestionCoordinator.

    Both vectors and canonical text/payload are written together. Source manifest
    operations and removal remain inherited, so there is one recovery journal.
    """

    _supports_lexical_vectors = True

    def __init__(
        self,
        config: VectorStoreCollectionConfig,
        *,
        lexical_config: LexicalIndexConfig | None = None,
        url: str = "http://localhost:6333",
        timeout_seconds: float = 10.0,
        allow_remote_server: bool = False,
    ) -> None:
        if type(allow_remote_server) is not bool:
            raise LexicalConfigurationError("allow_remote_server must be a bool.")
        parsed = urlparse(url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            raise LexicalConfigurationError("Provide an HTTP Qdrant URL without credentials.")
        if not allow_remote_server and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise LexicalConfigurationError(
                "Native BM25 runs on the configured server. Remote servers require explicit opt-in."
            )
        if config.index_version != "m5-chunks-v1":
            raise LexicalCompatibilityError("BM25 requires a fresh M5 chunk collection.")
        self.lexical_config = lexical_config or LexicalIndexConfig()
        if (
            type(timeout_seconds) not in (int, float)
            or not isfinite(timeout_seconds)
            or timeout_seconds <= 0
        ):
            raise LexicalConfigurationError("timeout_seconds must be positive.")
        self._config = config
        try:
            client_class, self._qdrant_models = _load_qdrant_client_dependencies()
            # This SDK flag forwards Document inputs to *url*, without selecting
            # any cloud endpoint. Only the native qdrant/bm25 model is submitted.
            self._client = client_class(url=url, timeout=timeout_seconds, cloud_inference=True)
            server_version = self._client.info().version
            version = tuple(int(part) for part in server_version.split("."))
            if version < (1, 16, 3):
                raise LexicalCompatibilityError(
                    "Native BM25 requires Qdrant >=1.16.3; upgrade and rebuild."
                )
            self.lexical_config = replace(self.lexical_config, encoding_version=server_version)
            self._ensure_collection()
        except (LexicalCompatibilityError, VectorStoreCompatibilityError):
            raise
        except Exception as exc:
            raise LexicalIndexError(
                "Cannot initialize native BM25; check local Qdrant >=1.16.3 and client >=1.16."
            ) from exc

    def _bm25_document(self, text: str) -> Any:
        config = self.lexical_config
        return self._qdrant_models.Document(
            text=text,
            model="qdrant/bm25",
            options={
                "language": config.language,
                "k": config.k,
                "b": config.b,
                "avg_len": config.average_document_length,
                "tokenizer": "word",
                "lowercase": True,
                "stopwords": {},
            },
        )

    def _point_vectors(self, dense: list[float], document: Document | None = None) -> Any:
        vectors: dict[str, Any] = {"dense": dense}
        if document is not None:
            vectors["lexical"] = self._bm25_document(document.content)
        return vectors

    def _dense_query_options(self) -> dict[str, object]:
        return {"using": "dense"}

    def _extract_vector_params(self, vectors_config: Any) -> Any:
        if not isinstance(vectors_config, Mapping) or set(vectors_config) != {"dense"}:
            raise LexicalCompatibilityError(
                "Expected named dense vector; select a new BM25 collection and rebuild."
            )
        return vectors_config["dense"]

    def _collection_config_payload(self) -> dict[str, object]:
        return {
            **super()._collection_config_payload(),
            _LEXICAL_METADATA_KEY: self.lexical_config.configuration_id,
        }

    def _ensure_collection(self) -> None:
        if self._client.collection_exists(self._config.collection_name):
            self._validate_collection_compatibility()
            collection = self._client.get_collection(self._config.collection_name)
            sparse = collection.config.params.sparse_vectors
            if (
                _extract_collection_metadata(collection).get(_LEXICAL_METADATA_KEY)
                != self.lexical_config.configuration_id
                or not sparse
                or set(sparse) != {"lexical"}
                or sparse["lexical"].modifier != self._qdrant_models.Modifier.IDF
            ):
                raise LexicalCompatibilityError(
                    "Incompatible BM25 configuration; choose a new collection and reingest."
                )
            return
        self._client.create_collection(
            collection_name=self._config.collection_name,
            vectors_config={
                "dense": self._qdrant_models.VectorParams(
                    size=self._config.dimensions,
                    distance=self._to_qdrant_distance(self._config.distance_metric),
                )
            },
            sparse_vectors_config={
                "lexical": self._qdrant_models.SparseVectorParams(
                    modifier=self._qdrant_models.Modifier.IDF
                )
            },
            metadata=self._collection_config_payload(),
        )

    def lexical_search(self, request: RetrievalRequest) -> tuple[SearchResult, ...]:
        validate_lexical_request(request)
        try:
            snapshot = self._search_snapshot()
            response = self._client.query_points(
                collection_name=self._config.collection_name,
                query=self._bm25_document(request.query),
                using="lexical",
                query_filter=self._build_qdrant_filter(request.metadata_filter),
                limit=request.top_k,
                with_payload=True,
                with_vectors=False,
            )
            if snapshot != self._search_snapshot():
                raise SourceIndexUnavailableError(
                    "Source index changed during lexical search; retry."
                )
            results = tuple(self._build_search_result(point) for point in response.points)
            revisions = {state.active.source_id: state.active for state in snapshot if state.active}
            for result in results:
                if (
                    not isfinite(result.score)
                    or result.score < 0
                    or not result.document.content.strip()
                ):
                    raise LexicalCompatibilityError("Malformed BM25 result content or score.")
                metadata = result.document.metadata_as_mapping()
                revision = revisions.get(str(metadata.get("source_id")))
                if (
                    revision is None
                    or result.document.document_id not in revision.chunk_ids
                    or metadata.get("content_sha256") != revision.content_sha256
                ):
                    raise LexicalCompatibilityError(
                        "Lexical result does not belong to a committed source revision."
                    )
            return results
        except (LexicalIndexError, SourceIndexUnavailableError):
            raise
        except Exception as exc:
            raise LexicalIndexError(
                "Native BM25 search failed; check Qdrant compatibility and service availability."
            ) from exc


class QdrantLexicalIndex:
    """Lexical capability view; canonical point ownership stays in chunk_store.

    Direct mutations require the same coordinator's pending manifest; they cannot
    create independent sparse-only points or bypass source visibility/recovery.
    """

    def __init__(self, *, chunk_store: QdrantBM25ChunkStore) -> None:
        self._store = chunk_store

    @property
    def config(self) -> LexicalIndexConfig:
        return self._store.lexical_config

    def search(self, request: RetrievalRequest) -> tuple[SearchResult, ...]:
        return self._store.lexical_search(request)

    def upsert(self, documents: Sequence[Document]) -> None:
        try:
            self._upsert(documents)
        except LexicalIndexError:
            raise
        except Exception as exc:
            raise LexicalIndexError(
                "Lexical update failed; coordinator recovery is required."
            ) from exc

    def _upsert(self, documents: Sequence[Document]) -> None:
        if not documents:
            return
        if any(not isinstance(doc, Document) for doc in documents):
            raise LexicalConfigurationError("Lexical records must be Documents.")
        states = self._store.list_source_states()
        staged_ids = {
            identity
            for state in states
            if state.target is not None
            for identity in state.target.chunk_ids
        }
        if any(doc.document_id not in staged_ids for doc in documents):
            raise LexicalCompatibilityError(
                "Lexical writes require coordinator-owned staged chunks."
            )
        if len({doc.document_id for doc in documents}) != len(documents):
            raise LexicalConfigurationError("Duplicate chunk IDs are invalid.")
        identifiers = [
            _qdrant_point_id_for_document_id(
                collection_name=self._store.collection_config.collection_name,
                document_id=doc.document_id,
            )
            for doc in documents
        ]
        points = self._store._client.retrieve(
            collection_name=self._store.collection_config.collection_name,
            ids=identifiers,
            with_payload=True,
            with_vectors=False,
        )
        existing = {point.payload["document_id"]: point.payload for point in points}
        if any(
            existing.get(doc.document_id, {}).get("content") != doc.content
            or existing.get(doc.document_id, {}).get("metadata") != doc.metadata_as_mapping()
            for doc in documents
        ):
            raise LexicalCompatibilityError(
                "Canonical payload must already exist unchanged; use the combined writer."
            )
        self._store._client.update_vectors(
            collection_name=self._store.collection_config.collection_name,
            points=[
                self._store._qdrant_models.PointVectors(
                    id=identity, vector={"lexical": self._store._bm25_document(doc.content)}
                )
                for identity, doc in zip(identifiers, documents, strict=True)
            ],
            wait=True,
        )

    def delete(self, document_ids: Sequence[str]) -> None:
        try:
            self._delete(document_ids)
        except LexicalIndexError:
            raise
        except Exception as exc:
            raise LexicalIndexError(
                "Chunk removal failed; coordinator recovery is required."
            ) from exc

    def _delete(self, document_ids: Sequence[str]) -> None:
        if any(not isinstance(identity, str) or not identity.strip() for identity in document_ids):
            raise LexicalConfigurationError("Chunk IDs must be nonblank strings.")
        states = self._store.list_source_states()
        pending_ids = {
            identity
            for state in states
            if state.phase.value != "active"
            for revision in (state.active, state.target)
            if revision is not None
            for identity in revision.chunk_ids
        }
        if any(identity not in pending_ids for identity in document_ids):
            raise LexicalCompatibilityError(
                "Chunk deletion requires coordinator-owned pending operation."
            )
        self._store.delete(document_ids)
