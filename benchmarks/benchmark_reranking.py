"""Controlled optional reranking comparison using #64's frozen evidence corpus."""

from __future__ import annotations

import argparse
import json
import os
import platform
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Any

from benchmarks.benchmark_chunked_retrieval import MemoryEvidenceStore, load_evidence_dataset
from context_engine.knowledge.chunking import ChunkingConfig, StructureAwareChunker
from context_engine.knowledge.ingestion import (
    INDEX_VERSION,
    IngestionStatus,
    SourceIngestionCoordinator,
    indexing_configuration_id,
)
from context_engine.retrieval import (
    EmbeddingVectorStoreRetriever,
    LocalEmbeddingProvider,
    LocalEmbeddingProviderConfig,
    RetrievalRequest,
    SearchResult,
    VectorStoreCollectionConfig,
)
from context_engine.retrieval.evidence_evaluation import evaluate_evidence_query
from context_engine.retrieval.local_cross_encoder import (
    LocalCrossEncoderConfig,
    LocalCrossEncoderReranker,
)
from context_engine.retrieval.reranking import (
    RerankerError,
    RerankingCandidate,
    RerankingRequest,
    RerankingRetriever,
    RerankingRetrieverConfig,
)


class SavedCandidates:
    """Replay the identical saved list so query embedding/search variation cannot affect ranking."""

    def __init__(self, candidates: tuple[SearchResult, ...]) -> None:
        self.candidates = candidates

    def retrieve(self, request: RetrievalRequest) -> tuple[SearchResult, ...]:
        return self.candidates[: request.top_k]


def run_comparison(embedding_reference: str, reranking_reference: str) -> dict[str, Any]:
    dataset = load_evidence_dataset()
    provider = LocalEmbeddingProvider(
        LocalEmbeddingProviderConfig(
            model_id="sentence-transformers/all-MiniLM-L6-v2",
            model_reference=embedding_reference,
            batch_size=8,
            normalize_embeddings=True,
        )
    )
    counter = provider.build_token_counter()
    chunker = StructureAwareChunker(ChunkingConfig(provider.model_id, 128, 16), counter)
    identity = indexing_configuration_id(chunker, embedding_identity=provider.indexing_identity)
    store = MemoryEvidenceStore(
        VectorStoreCollectionConfig(
            "reranking-benchmark",
            provider.model_id,
            provider.dimensions,
            index_version=INDEX_VERSION,
            index_configuration_id=identity,
        )
    )
    coordinator = SourceIngestionCoordinator(
        chunker=chunker,
        embedding_provider=provider,
        vector_store=store,
        embedding_identity=provider.indexing_identity,
    )
    for source in dataset.sources:
        outcome = coordinator.ingest(source, dataset.processing_limits)
        if outcome.status is IngestionStatus.FAILED:
            raise RuntimeError(f"Benchmark ingestion failed: {outcome}")
    dense = EmbeddingVectorStoreRetriever(embedding_provider=provider, vector_store=store)
    saved = {
        q.query_id: tuple(dense.retrieve(RetrievalRequest(q.text, 20))) for q in dataset.queries
    }
    configurations = []
    compatibility_probes = []
    for batch in (4, 8):
        reranker = LocalCrossEncoderReranker(
            LocalCrossEncoderConfig(model_reference=reranking_reference, batch_size=batch)
        )
        from context_engine.retrieval.embeddings import Document

        oversize = RerankingRequest(
            "query",
            (
                RerankingCandidate(
                    Document.from_mapping(document_id="oversize-probe", content="planet " * 600)
                ),
            ),
        )
        try:
            reranker.score(oversize)
            compatibility_probes.append({"batch_size": batch, "status": "unexpected-success"})
        except RerankerError as exc:
            compatibility_probes.append(
                {
                    "batch_size": batch,
                    "status": "rejected",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
        # Explicit unmeasured warm-up before recording warm request latency.
        first = dataset.queries[0]
        RerankingRetriever(SavedCandidates(saved[first.query_id]), reranker).retrieve(
            RetrievalRequest(first.text, 5)
        )
        for budget in (10, 20):
            rows = []
            for query in dataset.queries:
                candidates = saved[query.query_id][:budget]
                before = evaluate_evidence_query(candidates[:5], query.evidence, k_values=(1, 3, 5))
                row: dict[str, Any] = {
                    "query_id": query.query_id,
                    "split": query.split,
                    "candidate_count": len(candidates),
                    "candidate_metrics": asdict(
                        evaluate_evidence_query(candidates, query.evidence, k_values=(budget,))
                    ),
                    "before": asdict(before),
                    "candidate_ids": [r.document.document_id for r in candidates],
                    "before_tokens_at_5": sum(
                        counter.count_tokens(r.document.content) for r in candidates[:5]
                    ),
                }
                started = perf_counter()
                try:
                    ranked = RerankingRetriever(
                        SavedCandidates(candidates),
                        reranker,
                        config=RerankingRetrieverConfig(budget, 5),
                    ).retrieve(RetrievalRequest(query.text, 5))
                    elapsed = perf_counter() - started
                    after = evaluate_evidence_query(ranked, query.evidence, k_values=(1, 3, 5))
                    row.update(
                        status="success",
                        after=asdict(after),
                        warm_seconds=elapsed,
                        reranked_ids=[r.document.document_id for r in ranked],
                        after_tokens_at_5=sum(
                            counter.count_tokens(r.document.content) for r in ranked
                        ),
                        reranker_scores=[r.score for r in ranked],
                    )
                except RerankerError as exc:
                    row.update(
                        status="failed",
                        error_type=type(exc).__name__,
                        error=str(exc),
                        warm_seconds=perf_counter() - started,
                    )
                rows.append(row)
            summary = {}
            for split in ("development", "held_out"):
                group = [row for row in rows if row["split"] == split]
                successes = [row for row in group if row["status"] == "success"]
                supported = [row for row in successes if row["before"]["supported"]]
                summary[split] = {
                    "query_count": len(group),
                    "failures": len(group) - len(successes),
                    "mean_warm_seconds_successes": mean(r["warm_seconds"] for r in successes)
                    if successes
                    else None,
                    "pairs_per_second_successes": (
                        sum(r["candidate_count"] for r in successes)
                        / sum(r["warm_seconds"] for r in successes)
                        if successes
                        else None
                    ),
                    "before_recall_at_1": mean(r["before"]["recall_at_k"][1] for r in supported)
                    if supported
                    else None,
                    "after_recall_at_1": mean(r["after"]["recall_at_k"][1] for r in supported)
                    if supported
                    else None,
                    "before_recall_at_5": mean(r["before"]["recall_at_k"][5] for r in supported)
                    if supported
                    else None,
                    "after_recall_at_5": mean(r["after"]["recall_at_k"][5] for r in supported)
                    if supported
                    else None,
                    "wins_at_5": [
                        r["query_id"]
                        for r in supported
                        if r["after"]["recall_at_k"][5] > r["before"]["recall_at_k"][5]
                    ],
                    "regressions_at_5": [
                        r["query_id"]
                        for r in supported
                        if r["after"]["recall_at_k"][5] < r["before"]["recall_at_k"][5]
                    ],
                    "unchanged_at_5": [
                        r["query_id"]
                        for r in supported
                        if r["after"]["recall_at_k"][5] == r["before"]["recall_at_k"][5]
                    ],
                }
            configurations.append(
                {
                    "candidate_limit": budget,
                    "batch_size": batch,
                    "final_limit": 5,
                    "model_id": reranker.model_id,
                    "configuration_id": reranker.configuration_id,
                    "initialization_seconds": reranker.initialization_seconds,
                    "model_parameter_bytes": reranker.model_parameter_bytes,
                    "rows": rows,
                    "summary": summary,
                }
            )
    return {
        "dataset_id": dataset.dataset_id,
        "dataset_sha256": dataset.sha256,
        "backend": "controlled dense candidates from in-memory cosine; no Qdrant/hybrid",
        "chunking": asdict(chunker.config)
        if hasattr(chunker, "config")
        else {"tokens": 128, "overlap": 16},
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "packages": {
                name: version(name) for name in ("torch", "sentence-transformers", "transformers")
            },
            "threads": {
                key: os.getenv(key)
                for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "TOKENIZERS_PARALLELISM")
            },
        },
        "memory_note": (
            "Parameter bytes only. Peak process memory unavailable; "
            "contains embedding and reranker."
        ),
        "candidate_snapshot": {
            qid: [{"document_id": r.document.document_id, "score": r.score} for r in values]
            for qid, values in saved.items()
        },
        "saved_documents": {
            r.document.document_id: asdict(r.document) for values in saved.values() for r in values
        },
        "configurations": configurations,
        "compatibility_probes": compatibility_probes,
        "decision": (
            "Optional only. No default adoption. Small corpus and "
            "missing hybrid integration limit conclusions."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embedding-reference", required=True)
    parser.add_argument("--reranking-reference", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_comparison(args.embedding_reference, args.reranking_reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
