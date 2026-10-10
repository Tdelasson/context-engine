"""Verify saved real rankings reproduce the frozen evidence labels."""

import json
from dataclasses import asdict
from pathlib import Path

from benchmarks.benchmark_chunked_retrieval import load_evidence_dataset
from context_engine.retrieval.embeddings import Document
from context_engine.retrieval.evidence_evaluation import evaluate_evidence_query
from context_engine.retrieval.vector_store import SearchResult


def test_saved_hybrid_comparison_replays_all_evidence_metrics() -> None:
    path = Path(__file__).resolve().parents[3] / "benchmarks/results/m5-hybrid-128-16.json"
    artifact = json.loads(path.read_text())
    dataset = load_evidence_dataset()
    assert artifact["dataset_sha256"] == dataset.sha256
    assert artifact["failures"] == []
    queries = {q.query_id: q for q in dataset.queries}
    assert len(artifact["queries"]) == 27
    for row in artifact["queries"]:
        results = tuple(
            SearchResult(
                Document.from_mapping(
                    document_id=r["chunk_id"],
                    content=artifact["chunks"][r["chunk_id"]]["content"],
                    metadata=r["metadata"],
                ),
                r["score"],
            )
            for r in row["results"]
        )
        metrics = asdict(
            evaluate_evidence_query(results, queries[row["query_id"]].evidence, k_values=(1, 5, 10))
        )
        assert json.loads(json.dumps(metrics)) == row["metrics"]

        if row["strategy"] == "hybrid":
            assert row["union_candidate_count"] == len(results)
            union = asdict(
                evaluate_evidence_query(
                    results, queries[row["query_id"]].evidence, k_values=(len(results) or 1,)
                )
            )
            assert json.loads(json.dumps(union)) == row["union_candidate_metrics"]
