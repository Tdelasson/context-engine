"""Paired evidence-budget comparison on frozen, identical M5 ranked candidates."""

import argparse
import json
import os
import platform
import sys
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Any
from uuid import uuid4

from benchmarks.benchmark_chunked_retrieval import MemoryEvidenceStore, load_evidence_dataset
from context_engine.knowledge.chunking import ChunkingConfig, StructureAwareChunker
from context_engine.knowledge.ingestion import SourceIngestionCoordinator, indexing_configuration_id
from context_engine.models.evidence_counting import QwenEvidenceTokenCounter
from context_engine.retrieval import (
    EmbeddingVectorStoreRetriever,
    LocalEmbeddingProvider,
    LocalEmbeddingProviderConfig,
    RetrievalRequest,
    SearchResult,
    VectorStoreCollectionConfig,
)
from context_engine.retrieval.evidence_evaluation import _union_length, evaluate_evidence_query
from context_engine.retrieval.evidence_selection import (
    EvidenceSelectionConfig,
    EvidenceTokenCounter,
    RankedEvidenceSelector,
    comparable_spans,
)
from context_engine.tools.retrieval import SearchDocumentsTool


def redundancy(results: Sequence[SearchResult]) -> dict[str, int | float]:
    groups: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
    sum_lengths = 0
    uncomparable = 0
    for result in results:
        spans = comparable_spans(result)
        if spans is None:
            uncomparable += 1
            continue
        intervals = [(s.start_offset, s.end_offset) for s in spans]
        sum_lengths += _union_length(intervals)
        groups[(spans[0].source_id, spans[0].content_sha256)].extend(intervals)
    unique = sum(_union_length(intervals) for intervals in groups.values())
    return {
        "repeated_source_characters": sum_lengths - unique,
        "repeated_source_fraction": (sum_lengths - unique) / sum_lengths if sum_lengths else 0,
        "uncomparable_candidates": uncomparable,
    }


def compare_candidates(
    query: str,
    candidates: Sequence[SearchResult],
    counter: EvidenceTokenCounter,
    budget: int,
    threshold: float | None,
) -> dict[str, Any]:
    tool = SearchDocumentsTool(
        type("UnusedRetriever", (), {"retrieve": lambda self, request: ()})()
    )
    selector = RankedEvidenceSelector(
        EvidenceSelectionConfig(
            budget, max_results=5, max_content_chars=2000, overlap_threshold=threshold
        ),
        counter,
        lambda result: tool._serialize_result(result, preserve_content=True),
    )
    started = perf_counter()
    selection = selector.select(query, candidates)
    return {
        "selection": selection,
        "selection_seconds": perf_counter() - started,
        "redundancy": redundancy(selection.selected),
    }


def run_benchmark(
    embedding_reference: str,
    tokenizer_directory: str,
    *,
    strategy: str = "dense-memory",
    qdrant_url: str = "http://localhost:6333",
    reranking_reference: str | None = None,
) -> dict[str, Any]:
    dataset = load_evidence_dataset()
    counter = QwenEvidenceTokenCounter(tokenizer_directory)
    provider = LocalEmbeddingProvider(
        LocalEmbeddingProviderConfig(
            "sentence-transformers/all-MiniLM-L6-v2",
            embedding_reference,
            batch_size=8,
            normalize_embeddings=True,
        )
    )
    chunker = StructureAwareChunker(
        ChunkingConfig(provider.model_id, 128, 16), provider.build_token_counter()
    )
    config = VectorStoreCollectionConfig(
        "ce-evidence-budget-" + uuid4().hex,
        provider.model_id,
        provider.dimensions,
        index_version="m5-chunks-v1",
        index_configuration_id=indexing_configuration_id(
            chunker, embedding_identity=provider.indexing_identity
        ),
    )
    store: Any = MemoryEvidenceStore(config)
    if strategy == "hybrid-reranked-qdrant":
        from context_engine.retrieval.qdrant_lexical_index import QdrantBM25ChunkStore

        store = QdrantBM25ChunkStore(config, url=qdrant_url)
    elif strategy != "dense-memory":
        raise ValueError("Unknown benchmark strategy.")
    coordinator = SourceIngestionCoordinator(
        chunker=chunker,
        embedding_provider=provider,
        vector_store=store,
        embedding_identity=provider.indexing_identity,
    )
    try:
        started = perf_counter()
        outcomes = [
            coordinator.ingest(source, dataset.processing_limits) for source in dataset.sources
        ]
        if any(outcome.status == "failed" for outcome in outcomes):
            raise RuntimeError(f"Ingestion failed: {outcomes}")
        ingestion_seconds = perf_counter() - started
        retriever: Any = EmbeddingVectorStoreRetriever(
            embedding_provider=provider, vector_store=store
        )
        if strategy == "hybrid-reranked-qdrant":
            from context_engine.retrieval.hybrid import (
                HybridRetriever,
                HybridRetrieverConfig,
                lifecycle_visibility_reader,
            )
            from context_engine.retrieval.lexical import LexicalRetriever
            from context_engine.retrieval.local_cross_encoder import (
                LocalCrossEncoderConfig,
                LocalCrossEncoderReranker,
            )
            from context_engine.retrieval.qdrant_lexical_index import QdrantLexicalIndex
            from context_engine.retrieval.reranking import (
                RerankingRetriever,
                RerankingRetrieverConfig,
            )

            if not reranking_reference:
                raise ValueError("Hybrid reranking requires a prepared local model.")
            retriever = RerankingRetriever(
                HybridRetriever(
                    dense_retriever=retriever,
                    lexical_retriever=LexicalRetriever(
                        lexical_index=QdrantLexicalIndex(chunk_store=store)
                    ),
                    config=HybridRetrieverConfig(20, 20, 20, 60),
                    visibility_reader=lifecycle_visibility_reader(store),
                ),
                LocalCrossEncoderReranker(
                    LocalCrossEncoderConfig(model_reference=reranking_reference)
                ),
                config=RerankingRetrieverConfig(20, 20),
            )
        # Freeze candidates once per query. Labels are used only after selection.
        saved = {
            q.query_id: tuple(retriever.retrieve(RetrievalRequest(q.text, 20)))
            for q in dataset.queries
        }
        rows = []
        for query in dataset.queries:
            for budget in (2048, 4096, 8192):
                for threshold in (None, 0.5, 0.8, 1.0):
                    measured = compare_candidates(
                        query.text, saved[query.query_id], counter, budget, threshold
                    )
                    selection = measured.pop("selection")
                    rows.append(
                        {
                            "query_id": query.query_id,
                            "split": query.split,
                            "budget": budget,
                            "overlap_threshold": threshold,
                            "status": selection.status,
                            "token_count": selection.token_count,
                            "selected_ids": [r.document.document_id for r in selection.selected],
                            "metrics": asdict(
                                evaluate_evidence_query(selection.selected, query.evidence)
                            ),
                            "diagnostics": [asdict(d) for d in selection.diagnostics],
                            "configuration_id": selection.configuration_id,
                            **measured,
                        }
                    )
        aggregates = []
        for split in ("development", "held_out"):
            for budget in (2048, 4096, 8192):
                for threshold in (None, 0.5, 0.8, 1.0):
                    group = [
                        r
                        for r in rows
                        if r["split"] == split
                        and r["budget"] == budget
                        and r["overlap_threshold"] == threshold
                    ]
                    supported = [r for r in group if r["metrics"]["supported"]]
                    aggregates.append(
                        {
                            "split": split,
                            "budget": budget,
                            "overlap_threshold": threshold,
                            "supported_query_count": len(supported),
                            "unsupported_query_count": len(group) - len(supported),
                            "evidence_recall": mean(
                                r["metrics"]["recall_at_k"][10] for r in supported
                            ),
                            "all_required_rate": mean(
                                r["metrics"]["all_required_at_k"][10] for r in supported
                            ),
                            "character_coverage": mean(
                                mean(r["metrics"]["coverage_at_k"][10].values()) for r in supported
                            ),
                            "mean_tokens": mean(r["token_count"] for r in group),
                            "mean_selection_ms": mean(r["selection_seconds"] * 1000 for r in group),
                            "mean_repeated_source_characters": mean(
                                r["redundancy"]["repeated_source_characters"] for r in group
                            ),
                        }
                    )
        # Selection consults only development summaries. Lower cost breaks quality ties.
        development = [
            a
            for a in aggregates
            if a["split"] == "development" and a["overlap_threshold"] is not None
        ]
        chosen = min(
            development,
            key=lambda a: (
                -a["evidence_recall"],
                -a["all_required_rate"],
                a["mean_tokens"],
                a["budget"],
                a["overlap_threshold"],
            ),
        )
        return {
            "schema_version": "m5-evidence-selection-v1",
            "strategy": strategy,
            "dataset_id": dataset.dataset_id,
            "dataset_sha256": dataset.sha256,
            "counting_method": counter.method,
            "counting_configuration_id": counter.configuration_id,
            "answering_model": counter.model_id,
            "chunk_configuration": asdict(chunker.config),
            "index_configuration_id": coordinator.configuration_id,
            "embedding_identity": provider.indexing_identity,
            "chunk_count": sum(o.chunk_count for o in outcomes),
            "ingestion_seconds": ingestion_seconds,
            "chosen_on_development": chosen,
            "failures": [],
            "queries": rows,
            "aggregate": aggregates,
            "saved_candidates": {
                key: [
                    {
                        "document": {
                            "document_id": r.document.document_id,
                            "content": r.document.content,
                            "metadata": r.document.metadata_as_mapping(),
                        },
                        "score": r.score,
                        "diagnostics": [asdict(d) for d in r.diagnostics],
                    }
                    for r in results
                ]
                for key, results in saved.items()
            },
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "omp_threads": os.getenv("OMP_NUM_THREADS"),
                "mkl_threads": os.getenv("MKL_NUM_THREADS"),
                "packages": {
                    name: version(name)
                    for name in (
                        "tokenizers",
                        "sentence-transformers",
                        "torch",
                        "pypdf",
                        "qdrant-client",
                    )
                },
                "qdrant_server": store._client.info().version
                if strategy == "hybrid-reranked-qdrant"
                else None,
            },
        }
    finally:
        if strategy == "hybrid-reranked-qdrant":
            primary = sys.exception()
            try:
                store._client.delete_collection(config.collection_name)
                store._client.close()
            except Exception as exc:
                if primary is None:
                    raise
                primary.add_note(f"Benchmark cleanup failed: {exc}")


def serialize_artifact(output: dict[str, Any]) -> str:
    """One generated measurement/candidate per line keeps raw data diffs manageable."""

    def compact(value: object) -> str:
        return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False)

    fields = []
    for key, value in sorted(output.items()):
        if key == "saved_candidates":
            groups = []
            for query_id, candidates in sorted(value.items()):
                groups.append(
                    "    "
                    + compact(query_id)
                    + ": [\n"
                    + ",\n".join("      " + compact(item) for item in candidates)
                    + "\n    ]"
                )
            rendered = "{\n" + ",\n".join(groups) + "\n  }"
        elif isinstance(value, list):
            rendered = "[\n" + ",\n".join("    " + compact(item) for item in value) + "\n  ]"
        else:
            rendered = compact(value)
        fields.append("  " + compact(key) + ": " + rendered)
    return "{\n" + ",\n".join(fields) + "\n}\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embedding-reference", required=True)
    parser.add_argument("--tokenizer-directory", required=True)
    parser.add_argument(
        "--strategy", choices=("dense-memory", "hybrid-reranked-qdrant"), default="dense-memory"
    )
    parser.add_argument("--qdrant-url", default="http://localhost:6333")
    parser.add_argument("--reranking-reference")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        output = run_benchmark(
            args.embedding_reference,
            args.tokenizer_directory,
            strategy=args.strategy,
            qdrant_url=args.qdrant_url,
            reranking_reference=args.reranking_reference,
        )
    except Exception as exc:
        output = {"failures": [{"error_type": type(exc).__name__, "message": str(exc)}]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(serialize_artifact(output))
    if output["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
