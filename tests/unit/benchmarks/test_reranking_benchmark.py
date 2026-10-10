"""Replay the recorded comparison without inference to verify evidence attribution."""

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from benchmarks.benchmark_chunked_retrieval import load_evidence_dataset
from benchmarks.benchmark_reranking import SavedCandidates
from context_engine.retrieval.embeddings import Document
from context_engine.retrieval.evidence_evaluation import evaluate_evidence_query
from context_engine.retrieval.retriever import RetrievalRequest
from context_engine.retrieval.vector_store import SearchResult

REPORTS = (
    Path(__file__).parents[3] / "benchmarks/results/m5-reranking-local.json",
    Path(__file__).parents[3] / "benchmarks/results/m5-reranking-hybrid.json",
)


@pytest.mark.parametrize("report_path", REPORTS, ids=("dense", "hybrid"))
def test_recorded_rankings_use_identical_saved_evidence(report_path: Path) -> None:
    dataset = load_evidence_dataset()
    report = json.loads(report_path.read_text())
    assert report["dataset_sha256"] == dataset.sha256
    documents = {
        identity: Document.from_mapping(
            document_id=identity, content=value["content"], metadata=dict(value["metadata"])
        )
        for identity, value in report["saved_documents"].items()
    }
    queries = {query.query_id: query for query in dataset.queries}
    if "upstream_candidate_union_metrics" in report:
        for query_id, saved in report["candidate_snapshot"].items():
            candidates = tuple(SearchResult(documents[r["document_id"]], r["score"]) for r in saved)
            union = asdict(
                evaluate_evidence_query(
                    candidates, queries[query_id].evidence, k_values=(len(candidates),)
                )
            )
            assert (
                json.loads(json.dumps(union))
                == report["upstream_candidate_union_metrics"][query_id]
            )
            assert all(any(d["strategy"] == "hybrid" for d in r["diagnostics"]) for r in saved)
    for configuration in report["configurations"]:
        for row in configuration["rows"]:
            query = queries[row["query_id"]]
            saved = report["candidate_snapshot"][query.query_id][: configuration["candidate_limit"]]
            candidates = tuple(SearchResult(documents[r["document_id"]], r["score"]) for r in saved)
            assert row["candidate_ids"] == [r.document.document_id for r in candidates]
            assert row["candidate_count"] == len(candidates)
            candidate_metrics = asdict(
                evaluate_evidence_query(
                    candidates, query.evidence, k_values=(configuration["candidate_limit"],)
                )
            )
            assert json.loads(json.dumps(candidate_metrics)) == row["candidate_metrics"]
            before = asdict(
                evaluate_evidence_query(candidates[:5], query.evidence, k_values=(1, 3, 5))
            )
            # JSON converts integer metric keys to strings.
            assert json.loads(json.dumps(before)) == row["before"]
            if row["status"] == "success":
                assert set(row["reranked_ids"]) <= set(row["candidate_ids"])
                assert len(row["reranked_ids"]) == len(set(row["reranked_ids"]))
                after = tuple(
                    SearchResult(documents[identity], score)
                    for identity, score in zip(
                        row["reranked_ids"], row["reranker_scores"], strict=True
                    )
                )
                metrics = asdict(evaluate_evidence_query(after, query.evidence, k_values=(1, 3, 5)))
                assert json.loads(json.dumps(metrics)) == row["after"]


def test_saved_replay_obeys_requested_candidate_count() -> None:
    document = Document.from_mapping(document_id="a", content="original evidence")
    candidates = (SearchResult(document, 0.5),)
    replay = SavedCandidates(candidates)
    assert replay.retrieve(RetrievalRequest("query", 1))[0].document is document
    assert replay.retrieve(RetrievalRequest("query", 5)) == candidates
