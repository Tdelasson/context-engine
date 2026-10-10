"""Provider-independent persisted source manifests and lifecycle storage contract."""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from context_engine.retrieval.vector_store import (
    VectorStore,
    VectorStoreCollectionConfig,
    VectorStoreError,
)


class SourceIndexUnavailableError(VectorStoreError):
    """Search cannot safely serve a pending or concurrently changing source index."""


class SourceIndexPhase(StrEnum):
    ACTIVE = "active"
    STAGING = "staging"
    READY = "ready"


@dataclass(frozen=True, slots=True)
class SourceIndexRevision:
    source_id: str
    source_name: str
    source_kind: str
    content_sha256: str
    configuration_id: str
    chunk_ids: tuple[str, ...]
    metadata: tuple[tuple[str, object], ...] = ()

    def __post_init__(self) -> None:
        if (
            any(
                not isinstance(value, str) or not value.strip()
                for value in (
                    self.source_id,
                    self.source_name,
                    self.source_kind,
                    self.content_sha256,
                    self.configuration_id,
                )
            )
            or not self.chunk_ids
            or any(not isinstance(value, str) or not value for value in self.chunk_ids)
        ):
            raise ValueError("Invalid source revision fields.")
        if len(set(self.chunk_ids)) != len(self.chunk_ids):
            raise ValueError("Duplicate chunk IDs in source revision.")
        if any(
            re.fullmatch(r"[0-9a-f]{64}", value) is None
            for value in (
                self.content_sha256,
                self.configuration_id,
                *self.chunk_ids,
            )
        ):
            raise ValueError(
                "Revision, configuration, and chunk identities must be SHA-256 values."
            )
        keys = [key for key, _ in self.metadata]
        if any(not isinstance(key, str) for key in keys) or len(set(keys)) != len(keys):
            raise ValueError("Source metadata requires unique string keys.")


@dataclass(frozen=True, slots=True)
class SourceIndexState:
    source_id: str
    operation_id: str
    phase: SourceIndexPhase
    active: SourceIndexRevision | None = None
    target: SourceIndexRevision | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.source_id, str)
            or not self.source_id.strip()
            or not isinstance(self.operation_id, str)
            or not self.operation_id.strip()
            or not isinstance(self.phase, SourceIndexPhase)
        ):
            raise ValueError("Source state needs source and operation identities.")
        if self.phase is SourceIndexPhase.ACTIVE and self.target is not None:
            raise ValueError("An active state must not have a pending target.")
        if self.phase is SourceIndexPhase.STAGING and self.target is None:
            raise ValueError("Staging requires a target revision.")
        for revision in (self.active, self.target):
            if revision is not None and (
                not isinstance(revision, SourceIndexRevision)
                or revision.source_id != self.source_id
                or not revision.content_sha256
                or not revision.configuration_id
                or not revision.chunk_ids
                or len(set(revision.chunk_ids)) != len(revision.chunk_ids)
            ):
                raise ValueError("Invalid source revision in persisted state.")
        if (
            self.active is not None
            and self.target is not None
            and set(self.active.chunk_ids) & set(self.target.chunk_ids)
        ):
            raise ValueError("Replacement revisions must have disjoint chunk IDs.")


class SourceLifecycleStore(VectorStore, Protocol):
    @property
    def collection_config(self) -> VectorStoreCollectionConfig: ...

    def list_source_states(self) -> Sequence[SourceIndexState]:
        """Read all persisted source manifests, including pending writes/tombstones."""

    def save_source_state(self, state: SourceIndexState) -> None:
        """Replace one complete manifest with an acknowledged write."""
