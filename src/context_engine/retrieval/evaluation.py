"""Deterministic information-retrieval quality metrics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass
from math import log2


class RetrievalEvaluationError(ValueError):
    """Raised when retrieval evaluation input is invalid."""


@dataclass(frozen=True, slots=True)
class RetrievalQualityMetrics:
    """Aggregate retrieval-quality metrics for a fixed set of rankings."""

    recall_at_k: Mapping[int, float]
    mean_reciprocal_rank: float
    ndcg_at_k: Mapping[int, float]


def recall_at_k(
    ranked_document_ids: Sequence[str], relevant_document_ids: Set[str], *, k: int
) -> float:
    """Return the fraction of relevant documents present in the first ``k`` results."""
    _validate_metric_input(relevant_document_ids, k=k)
    retrieved = set(ranked_document_ids[:k])
    return len(retrieved & relevant_document_ids) / len(relevant_document_ids)


def reciprocal_rank(ranked_document_ids: Sequence[str], relevant_document_ids: Set[str]) -> float:
    """Return the reciprocal rank of the first relevant result, or zero."""
    if not relevant_document_ids:
        raise RetrievalEvaluationError("relevant_document_ids must not be empty.")
    for rank, document_id in enumerate(ranked_document_ids, start=1):
        if document_id in relevant_document_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(
    ranked_document_ids: Sequence[str], relevant_document_ids: Set[str], *, k: int
) -> float:
    """Return binary normalized discounted cumulative gain at ``k``."""
    _validate_metric_input(relevant_document_ids, k=k)
    dcg = sum(
        1.0 / log2(rank + 1)
        for rank, document_id in enumerate(ranked_document_ids[:k], start=1)
        if document_id in relevant_document_ids
    )
    ideal_relevant_count = min(len(relevant_document_ids), k)
    ideal_dcg = sum(1.0 / log2(rank + 1) for rank in range(1, ideal_relevant_count + 1))
    return dcg / ideal_dcg


def evaluate_rankings(
    rankings: Mapping[str, Sequence[str]],
    relevance_judgments: Mapping[str, Set[str]],
    *,
    k_values: Sequence[int],
) -> RetrievalQualityMetrics:
    """Aggregate deterministic quality metrics over the same fixed query set."""
    normalized_k_values = tuple(dict.fromkeys(k_values))
    if not normalized_k_values or any(k <= 0 for k in normalized_k_values):
        raise RetrievalEvaluationError("k_values must contain positive integers.")
    if set(rankings) != set(relevance_judgments):
        raise RetrievalEvaluationError(
            "rankings and relevance_judgments must contain the same query IDs."
        )

    query_ids = tuple(sorted(rankings))
    if not query_ids:
        raise RetrievalEvaluationError("rankings must not be empty.")
    duplicate_ranking_ids = [
        query_id
        for query_id in query_ids
        if len(rankings[query_id]) != len(set(rankings[query_id]))
    ]
    if duplicate_ranking_ids:
        raise RetrievalEvaluationError(
            "rankings must not contain duplicate document IDs; affected queries: "
            + ", ".join(duplicate_ranking_ids)
        )

    recall = {
        k: sum(
            recall_at_k(rankings[query_id], relevance_judgments[query_id], k=k)
            for query_id in query_ids
        )
        / len(query_ids)
        for k in normalized_k_values
    }
    ndcg = {
        k: sum(
            ndcg_at_k(rankings[query_id], relevance_judgments[query_id], k=k)
            for query_id in query_ids
        )
        / len(query_ids)
        for k in normalized_k_values
    }
    mrr = sum(
        reciprocal_rank(rankings[query_id], relevance_judgments[query_id]) for query_id in query_ids
    ) / len(query_ids)
    return RetrievalQualityMetrics(
        recall_at_k=recall,
        mean_reciprocal_rank=mrr,
        ndcg_at_k=ndcg,
    )


def _validate_metric_input(relevant_document_ids: Set[str], *, k: int) -> None:
    if k <= 0:
        raise RetrievalEvaluationError("k must be greater than zero.")
    if not relevant_document_ids:
        raise RetrievalEvaluationError("relevant_document_ids must not be empty.")
