"""Explicit processing, chunking, embedding, and recoverable source lifecycle."""

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from hashlib import sha256
from threading import Lock, RLock
from uuid import uuid4

from context_engine.knowledge.chunking import StructureAwareChunker
from context_engine.knowledge.processing import (
    BlockLocation,
    DiagnosticCode,
    ProcessedSource,
    ProcessingDiagnostic,
    ProcessingLimits,
    SourceInput,
    process_source,
)
from context_engine.retrieval.embeddings import Document, EmbeddingProvider
from context_engine.retrieval.source_store import (
    SourceIndexPhase,
    SourceIndexRevision,
    SourceIndexState,
    SourceIndexUnavailableError,
    SourceLifecycleStore,
)
from context_engine.retrieval.vector_store import VectorStoreCompatibilityError, VectorStoreRecord

INDEX_VERSION = "m5-chunks-v1"


def indexing_configuration_id(chunker: StructureAwareChunker, *, embedding_identity: str) -> str:
    """Bind effective preprocessing/model identity to exact-token chunk settings."""
    if not embedding_identity.strip():
        raise ValueError("An explicit embedding configuration identity is required.")
    return sha256(
        json.dumps(
            {
                "index_version": INDEX_VERSION,
                "processing_version": "processing-v1",
                "chunk_configuration_id": chunker.configuration_id,
                "embedding_identity": embedding_identity,
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()


def source_diagnostics(source: SourceIndexRevision) -> tuple[ProcessingDiagnostic, ...]:
    """Reconstruct exact persisted diagnostic locations for reports after restart."""
    diagnostics = []
    raw = dict(source.metadata).get("source_processing_diagnostics", [])
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                location = item.get("location")
                diagnostics.append(
                    ProcessingDiagnostic(
                        DiagnosticCode(item["code"]),
                        item["message"],
                        BlockLocation(**location) if isinstance(location, dict) else None,
                    )
                )
    return tuple(diagnostics)


class IngestionStatus(StrEnum):
    UNCHANGED = "unchanged"
    CREATED = "created"
    REPLACED = "replaced"
    DELETED = "deleted"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class IngestionOutcome:
    source_id: str
    status: IngestionStatus
    chunk_count: int = 0
    previous_chunk_count: int = 0
    chunk_ids: tuple[str, ...] = ()
    diagnostics: tuple[ProcessingDiagnostic, ...] = ()
    error_phase: str | None = None
    error_message: str | None = None
    requires_recovery: bool = False
    recovered: bool = False


class SourceIngestionCoordinator:
    """Single-writer coordinator; the store owns durability and search visibility."""

    _locks: dict[str, RLock] = {}
    _locks_guard = Lock()

    def __init__(
        self,
        *,
        chunker: StructureAwareChunker,
        embedding_provider: EmbeddingProvider,
        vector_store: SourceLifecycleStore,
        embedding_identity: str,
    ) -> None:
        self.chunker = chunker
        self._provider = embedding_provider
        self._store = vector_store
        # Serialize workbench sessions within this process. Separate processes
        # still require a single writer per collection.
        with self._locks_guard:
            self._lock = self._locks.setdefault(
                vector_store.collection_config.collection_name, RLock()
            )
        self.configuration_id = indexing_configuration_id(
            chunker, embedding_identity=embedding_identity
        )
        config = vector_store.collection_config
        if (
            config.index_version != INDEX_VERSION
            or config.index_configuration_id != self.configuration_id
            or config.embedding_model_id != chunker.config.model_id
        ):
            raise VectorStoreCompatibilityError(
                "Incompatible source index; select a new collection and rebuild."
            )

    def list_sources(self) -> tuple[SourceIndexRevision, ...]:
        with self._lock:
            return tuple(state.active for state in self._states() if state.active is not None)

    def _states(self) -> Sequence[SourceIndexState]:
        states = self._store.list_source_states()
        if any(state.phase is not SourceIndexPhase.ACTIVE for state in states):
            raise SourceIndexUnavailableError("Pending source operations require recovery.")
        return states

    def ingest(
        self, source: SourceInput, limits: ProcessingLimits | None = None
    ) -> IngestionOutcome:
        try:
            processed = (
                process_source(source, limits) if limits is not None else process_source(source)
            )
        except Exception as exc:
            return _failure(source.source_id, "processing", exc)
        return self.ingest_processed(processed)

    def ingest_processed(self, source: ProcessedSource) -> IngestionOutcome:
        """Accept already-processed application sources without repeating extraction."""
        with self._lock:
            source_id = source.provenance.source_id
            stage = "state_read"
            mutating = False
            previous: SourceIndexRevision | None = None
            try:
                state = next((item for item in self._states() if item.source_id == source_id), None)
                previous = state.active if state is not None else None
                if previous is not None and (
                    previous.source_name != source.provenance.source_name
                    or previous.source_kind != source.provenance.source_kind
                ):
                    raise VectorStoreCompatibilityError(
                        "A source identity cannot change its name or namespace."
                    )
                stage = "chunking"
                chunks = self.chunker.chunk(source)
                documents = tuple(
                    Document.from_mapping(
                        document_id=chunk.chunk_id,
                        content=chunk.content,
                        metadata={
                            **chunk.to_document().metadata_as_mapping(),
                            "index_version": INDEX_VERSION,
                            "index_configuration_id": self.configuration_id,
                            "source_processing_diagnostics": [
                                asdict(item) for item in source.diagnostics
                            ],
                        },
                    )
                    for chunk in chunks
                )
                target = SourceIndexRevision(
                    source_id=source_id,
                    source_name=source.provenance.source_name,
                    source_kind=source.provenance.source_kind,
                    content_sha256=source.provenance.content_sha256,
                    configuration_id=self.configuration_id,
                    chunk_ids=tuple(doc.document_id for doc in documents),
                    metadata=documents[0].metadata,
                )
                if previous == target:
                    return _success(target, previous, IngestionStatus.UNCHANGED, source.diagnostics)
                if previous is not None and set(previous.chunk_ids) & set(target.chunk_ids):
                    raise VectorStoreCompatibilityError(
                        "Changed source metadata requires a new indexing configuration."
                    )
                stage = "embedding"
                embeddings = self._provider.embed_documents(documents)
                if len(embeddings) != len(documents):
                    raise ValueError("Embedding count must match chunk count.")
                for embedding in embeddings:
                    self._store.collection_config.ensure_embedding_compatible(embedding)
                records = tuple(
                    VectorStoreRecord(doc, vector)
                    for doc, vector in zip(documents, embeddings, strict=True)
                )
                stage = "storage"
                pending = SourceIndexState(
                    source_id, uuid4().hex, SourceIndexPhase.STAGING, previous, target
                )
                mutating = True
                self._store.save_source_state(pending)
                self._store.upsert(records)
                ready = replace(pending, phase=SourceIndexPhase.READY)
                self._store.save_source_state(ready)
                self._finish(ready)
                return _success(
                    target,
                    previous,
                    IngestionStatus.CREATED if previous is None else IngestionStatus.REPLACED,
                    source.diagnostics,
                )
            except Exception as exc:
                return _failure(
                    source_id,
                    stage,
                    exc,
                    requires_recovery=mutating or isinstance(exc, SourceIndexUnavailableError),
                    previous=previous,
                    diagnostics=source.diagnostics,
                )

    def delete_source(self, source_id: str) -> IngestionOutcome:
        with self._lock:
            previous = None
            mutating = False
            try:
                if not source_id.strip():
                    raise ValueError("Source identity must not be empty.")
                state = next((item for item in self._states() if item.source_id == source_id), None)
                previous = state.active if state is not None else None
                if previous is None:
                    return IngestionOutcome(source_id, IngestionStatus.UNCHANGED)
                ready = SourceIndexState(source_id, uuid4().hex, SourceIndexPhase.READY, previous)
                mutating = True
                self._store.save_source_state(ready)
                self._finish(ready)
                return IngestionOutcome(
                    source_id, IngestionStatus.DELETED, previous_chunk_count=len(previous.chunk_ids)
                )
            except Exception as exc:
                return _failure(
                    source_id,
                    "storage",
                    exc,
                    requires_recovery=mutating or isinstance(exc, SourceIndexUnavailableError),
                    previous=previous,
                )

    def _finish(self, state: SourceIndexState) -> None:
        target_ids = set(state.target.chunk_ids) if state.target is not None else set()
        if state.active is not None:
            self._store.delete(
                tuple(chunk_id for chunk_id in state.active.chunk_ids if chunk_id not in target_ids)
            )
        self._store.save_source_state(
            replace(state, phase=SourceIndexPhase.ACTIVE, active=state.target, target=None)
        )

    def recover(self) -> tuple[IngestionOutcome, ...]:
        """Rollback incomplete staging or finish ready replacements/deletes, without inference."""
        with self._lock:
            outcomes: list[IngestionOutcome] = []
            try:
                states = self._store.list_source_states()
            except Exception as exc:
                return (_failure("*", "recovery", exc, requires_recovery=True),)
            for state in states:
                if state.phase is SourceIndexPhase.ACTIVE:
                    continue
                try:
                    if state.phase is SourceIndexPhase.STAGING:
                        assert state.target is not None
                        self._store.delete(state.target.chunk_ids)
                        self._store.save_source_state(
                            replace(state, phase=SourceIndexPhase.ACTIVE, target=None)
                        )
                        outcome = IngestionOutcome(
                            state.source_id,
                            IngestionStatus.FAILED,
                            chunk_count=len(state.active.chunk_ids) if state.active else 0,
                            chunk_ids=state.active.chunk_ids if state.active else (),
                            diagnostics=source_diagnostics(state.active) if state.active else (),
                            error_phase="recovery",
                            error_message=(
                                "Incomplete staged revision discarded; previous revision restored."
                            ),
                            recovered=True,
                        )
                    else:
                        self._finish(state)
                        outcome = (
                            IngestionOutcome(
                                state.source_id,
                                IngestionStatus.DELETED,
                                previous_chunk_count=len(state.active.chunk_ids)
                                if state.active
                                else 0,
                                recovered=True,
                            )
                            if state.target is None
                            else replace(
                                _success(
                                    state.target,
                                    state.active,
                                    IngestionStatus.CREATED
                                    if state.active is None
                                    else IngestionStatus.REPLACED,
                                    source_diagnostics(state.target),
                                ),
                                recovered=True,
                            )
                        )
                    outcomes.append(outcome)
                except Exception as exc:
                    outcomes.append(
                        _failure(
                            state.source_id,
                            "recovery",
                            exc,
                            requires_recovery=True,
                            previous=state.active,
                        )
                    )
            return tuple(outcomes)


def _success(
    target: SourceIndexRevision,
    previous: SourceIndexRevision | None,
    status: IngestionStatus,
    diagnostics: tuple[ProcessingDiagnostic, ...],
) -> IngestionOutcome:
    return IngestionOutcome(
        target.source_id,
        status,
        len(target.chunk_ids),
        len(previous.chunk_ids) if previous is not None else 0,
        target.chunk_ids,
        diagnostics,
    )


def _failure(
    source_id: str,
    phase: str,
    error: Exception,
    *,
    requires_recovery: bool = False,
    previous: SourceIndexRevision | None = None,
    diagnostics: tuple[ProcessingDiagnostic, ...] = (),
) -> IngestionOutcome:
    return IngestionOutcome(
        source_id,
        IngestionStatus.FAILED,
        previous_chunk_count=len(previous.chunk_ids) if previous is not None else 0,
        diagnostics=diagnostics,
        error_phase=phase,
        error_message=f"{type(error).__name__}: {error}",
        requires_recovery=requires_recovery,
    )
