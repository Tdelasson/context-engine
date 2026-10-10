"""Deterministic rank fusion and fail-closed orchestration contracts."""

from collections.abc import Sequence
from dataclasses import replace
from math import inf, nan
from typing import cast

import pytest

from context_engine.retrieval.embeddings import Document
from context_engine.retrieval.hybrid import (
    HybridConfigurationError,
    HybridConsistencyError,
    HybridRetrievalError,
    HybridRetriever,
    HybridRetrieverConfig,
    HybridVisibilitySnapshot,
    reciprocal_rank_fusion,
)
from context_engine.retrieval.retriever import RetrievalRequest
from context_engine.retrieval.source_store import SourceIndexPhase, SourceIndexState
from context_engine.retrieval.vector_store import MetadataFilter, SearchResult


def result(identity: str, score: float = 0.5, **metadata: object) -> SearchResult:
    return SearchResult(
        Document.from_mapping(document_id=identity, content="identical text", metadata=metadata),
        score,
    )


class Branch:
    def __init__(self, output: Sequence[SearchResult] = (), error: Exception | None = None):
        self.output = output
        self.error = error
        self.requests: list[RetrievalRequest] = []

    def retrieve(self, request: RetrievalRequest) -> Sequence[SearchResult]:
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.output


def test_one_based_arithmetic_deduplication_and_ties() -> None:
    cfg = HybridRetrieverConfig(smoothing=0)
    a, b, c = result("a"), result("b"), result("c")
    fused = reciprocal_rank_fusion((a, a, b), (c, b), config=cfg)
    assert [r.document.document_id for r in fused] == ["a", "b", "c"]
    assert [r.score for r in fused] == [1, 1, 1]
    assert [s.rank for s in fused[1].diagnostics if s.score_kind == "rrf_contribution"] == [2, 2]
    assert reciprocal_rank_fusion((a, a, b), (c, b), config=cfg) == fused


@pytest.mark.parametrize("dense,lexical", [((), ()), ((result("a"),), ()), ((), (result("b"),))])
def test_empty_and_missing_candidates(
    dense: Sequence[SearchResult], lexical: Sequence[SearchResult]
) -> None:
    fused = reciprocal_rank_fusion(dense, lexical, config=HybridRetrieverConfig())
    assert len(fused) == len(dense) + len(lexical)
    assert all(r.score == 1 / 61 for r in fused)


def test_budgets_filters_final_limit_and_native_scores() -> None:
    dense = Branch((result("a", 0.2, group="ok"),))
    lexical = Branch((result("a", 7.2, group="ok"), result("b", 4.8, group="ok")))
    cfg = HybridRetrieverConfig(2, 3, 2, 60)
    retriever = HybridRetriever(dense_retriever=dense, lexical_retriever=lexical, config=cfg)
    filter_ = MetadataFilter.from_mapping({"group": "ok"})
    output = retriever.retrieve(RetrievalRequest("query", 1, filter_))
    assert dense.requests == [RetrievalRequest("query", 2, filter_)]
    assert lexical.requests == [RetrievalRequest("query", 3, filter_)]
    assert len(output) == 1 and output[0].score == 2 / 61
    assert [
        s.score for s in output[0].diagnostics if s.strategy in {"hybrid_dense", "hybrid_lexical"}
    ] == [0.2, 7.2]
    assert all(
        s.duration_seconds is not None
        for s in output[0].diagnostics
        if s.strategy.startswith("hybrid")
    )


@pytest.mark.parametrize("value", [0, -1, True, 1.2, 1001])
def test_invalid_budgets(value: object) -> None:
    with pytest.raises(HybridConfigurationError):
        HybridRetrieverConfig(dense_candidate_count=cast(int, value))


@pytest.mark.parametrize("value", [-1, True, 1.2, 10001])
def test_invalid_smoothing(value: object) -> None:
    with pytest.raises(HybridConfigurationError):
        HybridRetrieverConfig(smoothing=cast(int, value))


@pytest.mark.parametrize("query,top_k", [(" ", 1), ("query", 21)])
def test_invalid_requests_do_not_call_branches(query: str, top_k: int) -> None:
    branch = Branch()
    retriever = HybridRetriever(dense_retriever=branch, lexical_retriever=branch)
    with pytest.raises(HybridConfigurationError):
        retriever.retrieve(RetrievalRequest(query, top_k))
    assert not branch.requests


@pytest.mark.parametrize("score", [nan, inf, -inf, True])
def test_invalid_scores(score: float) -> None:
    with pytest.raises(HybridRetrievalError):
        reciprocal_rank_fusion((result("a", score),), (), config=HybridRetrieverConfig())


def test_canonical_conflicts_and_distinct_sources() -> None:
    cfg = HybridRetrieverConfig()
    a = result("a", source_id="one", content_sha256="rev")
    b = result("b", source_id="two", content_sha256="rev")
    assert len(reciprocal_rank_fusion((a,), (b,), config=cfg)) == 2
    for other in (
        replace(a, document=replace(a.document, content="changed")),
        result("a", source_id="one", content_sha256="changed"),
        result("a", source_id="two", content_sha256="rev"),
    ):
        with pytest.raises(HybridConsistencyError):
            reciprocal_rank_fusion((a,), (other,), config=cfg)
    with pytest.raises(HybridConsistencyError):
        reciprocal_rank_fusion((a, replace(a, score=1)), (), config=cfg)
    with pytest.raises(HybridConsistencyError):
        reciprocal_rank_fusion(
            (a,), (result("different", source_id="one", content_sha256="changed"),), config=cfg
        )
    with pytest.raises(HybridConsistencyError):
        reciprocal_rank_fusion(
            (result("a", index_configuration_id="old"),),
            (result("b", index_configuration_id="new"),),
            config=cfg,
        )


@pytest.mark.parametrize("branch", ["dense", "lexical"])
def test_branch_failure_returns_no_partial_result(branch: str) -> None:
    dense, lexical = Branch((result("a"),)), Branch((result("b"),))
    if branch == "dense":
        dense.error = RuntimeError("unavailable")
    else:
        lexical.error = RuntimeError("unavailable")
    with pytest.raises(HybridRetrievalError) as failure:
        HybridRetriever(dense_retriever=dense, lexical_retriever=lexical).retrieve(
            RetrievalRequest("query")
        )
    assert failure.value.branch == branch
    if branch == "dense":
        assert not lexical.requests


def test_changed_visibility_fails_before_second_branch() -> None:
    snapshots = iter((HybridVisibilitySnapshot("old", ()), HybridVisibilitySnapshot("new", ())))
    dense, lexical = Branch(), Branch()
    retriever = HybridRetriever(
        dense_retriever=dense, lexical_retriever=lexical, visibility_reader=lambda: next(snapshots)
    )
    with pytest.raises(HybridConsistencyError):
        retriever.retrieve(RetrievalRequest("query"))
    assert dense.requests and not lexical.requests
    with pytest.raises(HybridConsistencyError):
        HybridVisibilitySnapshot("id", (SourceIndexState("s", "op", SourceIndexPhase.READY),))


def test_dependency_budget_filter_and_malformed_records_fail() -> None:
    for output in (
        (result("a"), result("b")),
        (result("a", group="wrong"),),
        (cast(SearchResult, object()),),
    ):
        dense = Branch(output)
        retriever = HybridRetriever(
            dense_retriever=dense, lexical_retriever=Branch(), config=HybridRetrieverConfig(1, 1, 1)
        )
        with pytest.raises(HybridRetrievalError):
            retriever.retrieve(
                RetrievalRequest("query", 1, MetadataFilter.from_mapping({"group": "ok"}))
            )


def test_duplicate_metadata_keys_and_blank_source_fail_typed() -> None:
    bad_metadata = SearchResult(Document("a", "text", (("key", 1), ("key", 2))), 1)
    for candidate in (bad_metadata, result("a", source_id=" ", content_sha256="rev")):
        with pytest.raises(HybridRetrievalError):
            reciprocal_rank_fusion((candidate,), (), config=HybridRetrieverConfig())
