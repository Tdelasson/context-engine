"""Sequential, provider-independent equal-weight reciprocal rank fusion."""

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from hashlib import sha256
from itertools import islice
from math import isfinite
from time import perf_counter

from context_engine.retrieval.diagnostics import RetrievalStageDiagnostic
from context_engine.retrieval.embeddings import Document
from context_engine.retrieval.lexical import validate_lexical_request
from context_engine.retrieval.retriever import RetrievalRequest, Retriever, RetrieverError
from context_engine.retrieval.source_store import (
    SourceIndexPhase,
    SourceIndexState,
    SourceLifecycleStore,
)
from context_engine.retrieval.vector_store import SearchResult


class HybridRetrievalError(RetrieverError):
    """Hybrid execution failed; branch identifies the failed boundary."""

    def __init__(self, message: str, *, branch: str = "fusion") -> None:
        self.branch = branch
        super().__init__(f"Hybrid {branch}: {message}")


class HybridConfigurationError(HybridRetrievalError, ValueError):
    """Invalid application-owned fusion configuration or request."""


class HybridConsistencyError(HybridRetrievalError):
    """Canonical records or observed source visibility are incompatible."""


@dataclass(frozen=True, slots=True)
class HybridRetrieverConfig:
    dense_candidate_count: int = 20
    lexical_candidate_count: int = 20
    final_result_count: int = 20
    smoothing: int = 60

    def __post_init__(self) -> None:
        for name in ("dense_candidate_count", "lexical_candidate_count", "final_result_count"):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= 1000:
                raise HybridConfigurationError(f"{name} must be an integer in [1, 1000].")
        if type(self.smoothing) is not int or not 0 <= self.smoothing <= 10000:
            raise HybridConfigurationError("smoothing must be an integer in [0, 10000].")
        if self.final_result_count > self.dense_candidate_count + self.lexical_candidate_count:
            raise HybridConfigurationError(
                "Final ceiling cannot exceed the total candidate budget."
            )

    @property
    def configuration_id(self) -> str:
        return sha256(
            json.dumps(
                {
                    "version": "equal-rrf-v1",
                    "dense": self.dense_candidate_count,
                    "lexical": self.lexical_candidate_count,
                    "final": self.final_result_count,
                    "smoothing": self.smoothing,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class HybridVisibilitySnapshot:
    """Observed collection generation and lifecycle manifests, not an atomic snapshot."""

    index_configuration_id: str
    source_states: tuple[SourceIndexState, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.index_configuration_id, str)
            or not self.index_configuration_id.strip()
        ):
            raise HybridConsistencyError("Missing index configuration identity.")
        if not isinstance(self.source_states, tuple) or any(
            not isinstance(state, SourceIndexState) or state.phase is not SourceIndexPhase.ACTIVE
            for state in self.source_states
        ):
            raise HybridConsistencyError("Source visibility is pending or invalid.")
        if any(
            s.active is not None and s.active.configuration_id != self.index_configuration_id
            for s in self.source_states
        ):
            raise HybridConsistencyError(
                "Manifest indexing identity differs from snapshot generation."
            )
        if len({s.source_id for s in self.source_states}) != len(self.source_states):
            raise HybridConsistencyError("Duplicate source manifests.")
        object.__setattr__(
            self, "source_states", tuple(sorted(self.source_states, key=lambda s: s.source_id))
        )


def lifecycle_visibility_reader(
    store: SourceLifecycleStore,
) -> Callable[[], HybridVisibilitySnapshot]:
    """Bind both retrievers' shared lifecycle owner; reject pending manifests on each read."""

    def read() -> HybridVisibilitySnapshot:
        identity = store.collection_config.index_configuration_id
        if identity is None:
            raise HybridConsistencyError("Hybrid lifecycle requires an M5 indexing identity.")
        return HybridVisibilitySnapshot(identity, tuple(store.list_source_states()))

    return read


def _validate_branch(
    results: Sequence[SearchResult], budget: int, branch: str
) -> tuple[SearchResult, ...]:
    try:
        bounded = tuple(islice(iter(results), budget + 1))
    except Exception as exc:
        raise HybridRetrievalError("Invalid result sequence.", branch=branch) from exc
    if len(bounded) > budget:
        raise HybridRetrievalError("Candidate budget exceeded.", branch=branch)
    unique: dict[str, SearchResult] = {}
    for result in bounded:
        if (
            not isinstance(result, SearchResult)
            or not isinstance(result.document, Document)
            or not isinstance(result.document.document_id, str)
            or not result.document.document_id.strip()
            or not isinstance(result.document.content, str)
            or not result.document.content.strip()
            or type(result.score) not in (int, float)
            or not isfinite(result.score)
            or not isinstance(result.diagnostics, tuple)
            or any(not isinstance(stage, RetrievalStageDiagnostic) for stage in result.diagnostics)
        ):
            raise HybridRetrievalError("Invalid candidate or score.", branch=branch)
        try:
            if not isinstance(result.document.metadata, tuple):
                raise TypeError("Canonical metadata must be a tuple.")
            metadata = result.document.metadata_as_mapping()
        except (TypeError, ValueError) as exc:
            raise HybridRetrievalError("Invalid canonical metadata.", branch=branch) from exc
        if len(metadata) != len(result.document.metadata) or any(
            not isinstance(k, str) for k in metadata
        ):
            raise HybridRetrievalError("Invalid canonical metadata keys.", branch=branch)
        previous = unique.get(result.document.document_id)
        if previous is not None:
            if previous != result:
                raise HybridConsistencyError("Inconsistent duplicate candidate.", branch=branch)
            continue
        unique[result.document.document_id] = result
    return tuple(unique.values())


def reciprocal_rank_fusion(
    dense: Sequence[SearchResult], lexical: Sequence[SearchResult], *, config: HybridRetrieverConfig
) -> tuple[SearchResult, ...]:
    """One vote per identity per branch; identical duplicates collapse before one-based ranks.

    Missing candidates contribute zero. Equal fused scores sort by canonical document ID.
    Canonical content and ALL metadata must match; runtime diagnostics are separate.
    """
    if not isinstance(config, HybridRetrieverConfig):
        raise HybridConfigurationError("Invalid fusion configuration.")
    branches = (
        ("dense", _validate_branch(dense, config.dense_candidate_count, "dense")),
        ("lexical", _validate_branch(lexical, config.lexical_candidate_count, "lexical")),
    )
    documents: dict[str, SearchResult] = {}
    scores: dict[str, float] = {}
    stages: dict[str, list[RetrievalStageDiagnostic]] = {}
    generations: set[object] = set()
    revisions: dict[str, object] = {}
    for branch, candidates in branches:
        for rank, result in enumerate(candidates, 1):
            identity = result.document.document_id
            metadata = result.document.metadata_as_mapping()
            generation = metadata.get("index_configuration_id")
            if generation is not None:
                if not isinstance(generation, str) or not generation.strip():
                    raise HybridConsistencyError("Invalid generation identity.", branch=branch)
                generations.add(generation)
            source = metadata.get("source_id")
            revision = metadata.get("content_sha256")
            if source is not None:
                if (
                    not isinstance(source, str)
                    or not source.strip()
                    or not isinstance(revision, str)
                    or not revision
                ):
                    raise HybridConsistencyError("Invalid source revision identity.", branch=branch)
                if source in revisions and revisions[source] != revision:
                    raise HybridConsistencyError("Conflicting source revisions.", branch=branch)
                revisions[source] = revision
            previous = documents.get(identity)
            if previous is not None and (
                previous.document.content != result.document.content
                or previous.document.metadata_as_mapping() != metadata
            ):
                raise HybridConsistencyError("Conflicting canonical chunk payload.", branch=branch)
            documents.setdefault(identity, result)
            contribution = 1 / (config.smoothing + rank)
            scores[identity] = scores.get(identity, 0.0) + contribution
            stages.setdefault(identity, []).extend(result.diagnostics)
            stages[identity].extend(
                (
                    RetrievalStageDiagnostic(
                        f"hybrid_{branch}",
                        result.diagnostics[-1].score_kind
                        if result.diagnostics
                        else "native_unspecified",
                        result.score,
                        rank,
                        config.configuration_id,
                        candidate_count=len(candidates),
                    ),
                    RetrievalStageDiagnostic(
                        f"{branch}_rrf",
                        "rrf_contribution",
                        contribution,
                        rank,
                        config.configuration_id,
                        candidate_count=len(candidates),
                    ),
                )
            )
    if len(generations) > 1:
        raise HybridConsistencyError("Incompatible index generations.")
    ordered = sorted(documents, key=lambda identity: (-scores[identity], identity))
    return tuple(
        replace(
            documents[identity],
            score=scores[identity],
            diagnostics=tuple(stages[identity])
            + (
                RetrievalStageDiagnostic(
                    "hybrid",
                    "rrf",
                    scores[identity],
                    rank,
                    config.configuration_id,
                    candidate_count=len(ordered),
                ),
            ),
        )
        for rank, identity in enumerate(ordered, 1)
    )


class HybridRetriever(Retriever):
    """Sequential branches fail closed; an optional reader observes shared lifecycle changes."""

    def __init__(
        self,
        *,
        dense_retriever: Retriever,
        lexical_retriever: Retriever,
        config: HybridRetrieverConfig = HybridRetrieverConfig(),
        visibility_reader: Callable[[], HybridVisibilitySnapshot] | None = None,
    ) -> None:
        if not isinstance(config, HybridRetrieverConfig):
            raise HybridConfigurationError("Invalid hybrid configuration.")
        self.config = config
        self._dense = dense_retriever
        self._lexical = lexical_retriever
        self._visibility_reader = visibility_reader

    def _snapshot(self) -> HybridVisibilitySnapshot | None:
        if self._visibility_reader is None:
            return None
        try:
            snapshot = self._visibility_reader()
            if not isinstance(snapshot, HybridVisibilitySnapshot):
                raise HybridConsistencyError("Invalid visibility snapshot.")
            return snapshot
        except HybridRetrievalError:
            raise
        except Exception as exc:
            raise HybridConsistencyError("Visibility read failed.") from exc

    def retrieve(self, request: RetrievalRequest) -> tuple[SearchResult, ...]:
        try:
            validate_lexical_request(request)
        except RetrieverError as exc:
            raise HybridConfigurationError(str(exc)) from exc
        if request.top_k > self.config.final_result_count:
            raise HybridConfigurationError("Requested top_k exceeds the configured final ceiling.")
        initial = self._snapshot()
        outputs: list[tuple[SearchResult, ...]] = []
        durations: list[float] = []
        for branch, retriever, budget in (
            ("dense", self._dense, self.config.dense_candidate_count),
            ("lexical", self._lexical, self.config.lexical_candidate_count),
        ):
            started = perf_counter()
            try:
                results = _validate_branch(
                    retriever.retrieve(
                        RetrievalRequest(request.query, budget, request.metadata_filter)
                    ),
                    budget,
                    branch,
                )
                if request.metadata_filter is not None and any(
                    r.document.metadata_as_mapping().get(key) != value
                    for r in results
                    for key, value in request.metadata_filter.equals
                ):
                    raise HybridRetrievalError("Candidate violates filters.", branch=branch)
            except HybridRetrievalError:
                raise
            except Exception as exc:
                raise HybridRetrievalError(
                    f"{type(exc).__name__}: branch execution failed.", branch=branch
                ) from exc
            durations.append(perf_counter() - started)
            outputs.append(results)
            if initial != self._snapshot():
                raise HybridConsistencyError("Source visibility changed between searches.")
        started = perf_counter()
        fused = reciprocal_rank_fusion(outputs[0], outputs[1], config=self.config)
        fusion_seconds = perf_counter() - started
        if initial is not None:
            active = {s.source_id: s.active for s in initial.source_states}
            for result in fused:
                metadata = result.document.metadata_as_mapping()
                revision = active.get(str(metadata.get("source_id")))
                if (
                    revision is None
                    or result.document.document_id not in revision.chunk_ids
                    or metadata.get("content_sha256") != revision.content_sha256
                    or metadata.get("index_configuration_id") != initial.index_configuration_id
                ):
                    raise HybridConsistencyError(
                        "Candidate is outside the observed committed index."
                    )
        return tuple(
            replace(
                result,
                diagnostics=tuple(
                    replace(
                        stage,
                        duration_seconds=durations[0]
                        if stage.strategy == "hybrid_dense"
                        else durations[1]
                        if stage.strategy == "hybrid_lexical"
                        else fusion_seconds
                        if stage.strategy == "hybrid"
                        else stage.duration_seconds,
                    )
                    for stage in result.diagnostics
                ),
            )
            for result in fused[: request.top_k]
        )
