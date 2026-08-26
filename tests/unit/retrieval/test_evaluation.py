import pytest

from context_engine.retrieval import (
    RetrievalEvaluationError,
    evaluate_rankings,
    ndcg_at_k,
    recall_at_k,
    reciprocal_rank,
)


def test_individual_metrics_match_manually_calculated_values() -> None:
    ranking = ("doc-a", "doc-x", "doc-b")
    relevant = {"doc-a", "doc-b"}

    assert recall_at_k(ranking, relevant, k=1) == 0.5
    assert recall_at_k(ranking, relevant, k=3) == 1.0
    assert reciprocal_rank(ranking, relevant) == 1.0
    assert ndcg_at_k(ranking, relevant, k=3) == pytest.approx(0.9197207891)


def test_evaluate_rankings_aggregates_over_fixed_query_set() -> None:
    metrics = evaluate_rankings(
        {
            "query-a": ("doc-a", "doc-x", "doc-b"),
            "query-b": ("doc-x", "doc-d", "doc-y"),
        },
        {
            "query-a": {"doc-a", "doc-b"},
            "query-b": {"doc-d"},
        },
        k_values=(1, 3),
    )

    assert metrics.recall_at_k == {1: 0.25, 3: 1.0}
    assert metrics.mean_reciprocal_rank == 0.75
    assert metrics.ndcg_at_k[1] == 0.5
    assert metrics.ndcg_at_k[3] == pytest.approx(0.7753252714)


@pytest.mark.parametrize("k", [0, -1])
def test_metrics_reject_non_positive_k(k: int) -> None:
    with pytest.raises(RetrievalEvaluationError, match="greater than zero"):
        recall_at_k(("doc-a",), {"doc-a"}, k=k)


def test_metrics_reject_empty_relevance_judgments() -> None:
    with pytest.raises(RetrievalEvaluationError, match="must not be empty"):
        ndcg_at_k(("doc-a",), set(), k=1)


def test_evaluate_rankings_rejects_mismatched_query_sets() -> None:
    with pytest.raises(RetrievalEvaluationError, match="same query IDs"):
        evaluate_rankings(
            {"query-a": ("doc-a",)},
            {"query-b": {"doc-a"}},
            k_values=(1,),
        )


def test_evaluate_rankings_rejects_duplicate_ranked_documents() -> None:
    with pytest.raises(RetrievalEvaluationError, match="duplicate document IDs"):
        evaluate_rankings(
            {"query-a": ("doc-a", "doc-a")},
            {"query-a": {"doc-a"}},
            k_values=(1,),
        )
