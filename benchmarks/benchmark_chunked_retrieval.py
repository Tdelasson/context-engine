"""M5 evidence benchmark; real inference is explicit and never part of default CI."""

from __future__ import annotations

import argparse
import json
import platform
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Any, Literal
from uuid import uuid4

from benchmarks.benchmark_embedding_models import (
    InMemoryCosineVectorStore,
    MeasuringEmbeddingProvider,
    MeasuringVectorStore,
)
from context_engine.knowledge.chunking import ChunkingConfig, StructureAwareChunker, TokenCounter
from context_engine.knowledge.ingestion import (
    INDEX_VERSION,
    IngestionStatus,
    SourceIngestionCoordinator,
    indexing_configuration_id,
)
from context_engine.knowledge.processing import (
    ProcessedSource,
    ProcessingLimits,
    SourceFormat,
    SourceInput,
    process_source,
)
from context_engine.retrieval import (
    EmbeddingProvider,
    EmbeddingVectorStoreRetriever,
    LocalEmbeddingProvider,
    LocalEmbeddingProviderConfig,
    QdrantVectorStore,
    RetrievalRequest,
    VectorStoreCollectionConfig,
)
from context_engine.retrieval.evidence_evaluation import (
    EvidenceItem,
    EvidenceSpan,
    evaluate_evidence_query,
    validate_evidence,
)
from context_engine.retrieval.source_store import SourceIndexState, SourceLifecycleStore

DEFAULT_DATASET = Path(__file__).parent / "data/retrieval/m5/dataset.json"


@dataclass(frozen=True, slots=True)
class EvidenceQuery:
    query_id: str
    text: str
    split: Literal["development", "held_out"]
    evidence: tuple[EvidenceItem, ...]

    def __post_init__(self) -> None:
        if (
            not self.query_id.strip()
            or not self.text.strip()
            or self.split not in {"development", "held_out"}
        ):
            raise ValueError("Queries require identity, text, and explicit evaluation split.")


@dataclass(frozen=True, slots=True)
class EvidenceDataset:
    dataset_id: str
    sha256: str
    sources: tuple[SourceInput, ...]
    processed_sources: tuple[ProcessedSource, ...]
    queries: tuple[EvidenceQuery, ...]
    processing_limits: ProcessingLimits


def load_evidence_dataset(path: Path = DEFAULT_DATASET) -> EvidenceDataset:
    raw_bytes = path.read_bytes()
    raw = json.loads(raw_bytes)
    if raw.get("processing_version") != "processing-v1":
        raise ValueError("Unknown processing representation version.")
    limits = ProcessingLimits(**raw["processing_limits"])
    inputs = []
    processed = []
    for row in raw["sources"]:
        source_path = (path.parent / row["path"]).resolve()
        if not source_path.is_relative_to(path.parent.resolve()):
            raise ValueError("Corpus paths must remain inside the dataset directory.")
        source = SourceInput(
            row["source_id"],
            row["path"],
            source_path.read_bytes(),
            SourceFormat(row["format"]),
            "benchmark",
        )
        result = process_source(source, limits)
        if (
            result.provenance.content_sha256 != row["content_sha256"]
            or sha256(result.text.encode()).hexdigest() != row["processed_text_sha256"]
        ):
            raise ValueError("Stale corpus bytes or processed-text representation.")
        inputs.append(source)
        processed.append(result)
    source_map = {source.provenance.source_id: source for source in processed}
    if len(source_map) != len(processed) or not processed:
        raise ValueError("Corpus sources must be nonempty and unique.")
    queries = []
    for row in raw["queries"]:
        items = tuple(
            EvidenceItem(item["evidence_id"], tuple(EvidenceSpan(**span) for span in item["spans"]))
            for item in row["evidence"]
        )
        validate_evidence(items, source_map)
        queries.append(EvidenceQuery(row["query_id"], row["text"], row["split"], items))
    if not queries or len({q.query_id for q in queries}) != len(queries):
        raise ValueError("Queries must be nonempty and unique.")
    if {q.split for q in queries} != {"development", "held_out"}:
        raise ValueError("Both development and held-out query sets are required.")
    return EvidenceDataset(
        raw["dataset_id"],
        sha256(raw_bytes).hexdigest(),
        tuple(inputs),
        tuple(processed),
        tuple(queries),
        limits,
    )


class MemoryEvidenceStore(InMemoryCosineVectorStore):
    """Single-process benchmark backend with the actual source lifecycle contract."""

    def __init__(self, config: VectorStoreCollectionConfig) -> None:
        super().__init__(config)
        self.states: dict[str, SourceIndexState] = {}

    @property
    def collection_config(self) -> VectorStoreCollectionConfig:
        return self._config

    def list_source_states(self) -> Sequence[SourceIndexState]:
        return tuple(self.states[key] for key in sorted(self.states))

    def save_source_state(self, state: SourceIndexState) -> None:
        self.states[state.source_id] = state


def run_dense_configuration(
    dataset: EvidenceDataset,
    *,
    provider: EmbeddingProvider,
    dimensions: int,
    counter: TokenCounter,
    embedding_identity: str,
    chunk_config: ChunkingConfig,
    query_prefix: str = "",
    backend: str = "in-memory-cosine",
    qdrant_url: str = "http://localhost:6333",
    k_values: Sequence[int] = (1, 5, 10),
) -> dict[str, Any]:
    """Exercise processing -> lifecycle chunk ingestion -> Retriever -> evidence metrics."""
    if backend not in {"in-memory-cosine", "qdrant-server"}:
        raise ValueError("Unsupported benchmark backend.")
    if not k_values or any(type(k) is not int or k <= 0 for k in k_values):
        raise ValueError("K values must be positive integers.")
    chunker = StructureAwareChunker(chunk_config, counter)
    identity = indexing_configuration_id(chunker, embedding_identity=embedding_identity)
    config = VectorStoreCollectionConfig(
        f"m5-benchmark-{uuid4().hex}",
        chunk_config.model_id,
        dimensions,
        index_version=INDEX_VERSION,
        index_configuration_id=identity,
    )
    store: SourceLifecycleStore = (
        MemoryEvidenceStore(config)
        if backend == "in-memory-cosine"
        else QdrantVectorStore(config, url=qdrant_url)
    )
    measured_provider = MeasuringEmbeddingProvider(provider)
    coordinator = SourceIngestionCoordinator(
        chunker=chunker,
        embedding_provider=measured_provider,
        vector_store=store,
        embedding_identity=embedding_identity,
    )
    started = perf_counter()
    cleanup_errors: list[str] = []
    try:
        outcomes = [
            coordinator.ingest(source, dataset.processing_limits) for source in dataset.sources
        ]
        if any(outcome.status is IngestionStatus.FAILED for outcome in outcomes):
            raise RuntimeError("Benchmark ingestion failed: " + repr(outcomes))
        ingestion_seconds = perf_counter() - started
        measured_store = MeasuringVectorStore(store)
        retriever = EmbeddingVectorStoreRetriever(
            embedding_provider=measured_provider, vector_store=measured_store
        )
        rows: list[dict[str, Any]] = []
        for query in dataset.queries:
            # Query truncation would silently invalidate the experiment.
            if counter.count_tokens(query_prefix + query.text) > counter.max_input_tokens:
                raise ValueError("Benchmark query exceeds embedding runtime input limit.")
            results = tuple(retriever.retrieve(RetrievalRequest(query.text, max(k_values))))
            metrics = evaluate_evidence_query(results, query.evidence, k_values=k_values)
            rows.append(
                {
                    "query_id": query.query_id,
                    "split": query.split,
                    "metrics": asdict(metrics),
                    "retrieved_tokens_at_k": {
                        k: sum(
                            counter.count_tokens(result.document.content) for result in results[:k]
                        )
                        for k in k_values
                    },
                    "query_embedding_seconds": measured_provider.query_embedding_seconds[-1],
                    "vector_search_seconds": measured_store.search_seconds[-1],
                    "results": [
                        {
                            "chunk_id": r.document.document_id,
                            "score": r.score,
                            "source_id": r.document.metadata_as_mapping()["source_id"],
                            "content_sha256": r.document.metadata_as_mapping()["content_sha256"],
                            "spans": r.document.metadata_as_mapping()["spans"],
                        }
                        for r in results
                    ],
                }
            )
        aggregates = {}
        for split in ("development", "held_out"):
            supported = [
                row for row in rows if row["split"] == split and row["metrics"]["supported"]
            ]
            aggregates[split] = {
                "supported_query_count": len(supported),
                "unsupported_query_count": sum(
                    row["split"] == split and not row["metrics"]["supported"] for row in rows
                ),
                "macro_evidence_recall_at_k": {
                    k: mean(row["metrics"]["recall_at_k"][k] for row in supported) for k in k_values
                },
                "all_required_rate_at_k": {
                    k: mean(row["metrics"]["all_required_at_k"][k] for row in supported)
                    for k in k_values
                },
            }
        chunk_count = sum(outcome.chunk_count for outcome in outcomes)
        return {
            "cleanup_errors": cleanup_errors,
            "query_prefix": query_prefix,
            "retrieved_token_measurement": (
                "sum of independently tokenized passage content "
                "including per-passage special tokens"
            ),
            "dataset_id": dataset.dataset_id,
            "dataset_sha256": dataset.sha256,
            "configuration_id": identity,
            "chunk_configuration": asdict(chunk_config),
            "embedding_identity": embedding_identity,
            "tokenizer_id": counter.tokenizer_id,
            "backend": backend,
            "ingestion_seconds": ingestion_seconds,
            "document_embedding_seconds": sum(measured_provider.document_embedding_seconds),
            "chunk_count": chunk_count,
            "dense_vector_float32_bytes_estimate": chunk_count * dimensions * 4,
            "persisted_index_bytes": None,
            "aggregate": aggregates,
            "queries": rows,
        }
    finally:
        # Best-effort cleanup never replaces a primary ingestion/inference error.
        for source in dataset.sources:
            try:
                outcome = coordinator.delete_source(source.source_id)
                if outcome.status is IngestionStatus.FAILED:
                    cleanup_errors.append(f"{source.source_id}: {outcome.error_message}")
            except Exception as exc:
                cleanup_errors.append(f"{source.source_id}: {type(exc).__name__}: {exc}")
        if cleanup_errors:
            import sys

            primary = sys.exception()
            if primary is not None:
                primary.add_note("Benchmark cleanup failures: " + repr(cleanup_errors))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model-reference", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--model-id", default="all-minilm-l6-v2")
    parser.add_argument("--chunk-settings", default="96:0,160:0,160:24")
    parser.add_argument(
        "--backend", choices=("in-memory-cosine", "qdrant-server"), default="in-memory-cosine"
    )
    parser.add_argument("--qdrant-url", default="http://localhost:6333")
    parser.add_argument(
        "--output", type=Path, default=Path("benchmarks/results/m5-dense-results.json")
    )
    args = parser.parse_args()
    dataset = load_evidence_dataset(args.dataset)
    output: dict[str, Any] = {
        "schema_version": "m5-evidence-results-v1",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor(),
        },
        "runs": [],
        "failures": [],
    }
    try:
        provider = LocalEmbeddingProvider(
            LocalEmbeddingProviderConfig(
                args.model_id, args.model_reference, normalize_embeddings=True
            )
        )
        counter = provider.build_token_counter()
        for setting in args.chunk_settings.split(","):
            size, overlap = (int(value) for value in setting.split(":"))
            try:
                output["runs"].append(
                    run_dense_configuration(
                        dataset,
                        provider=provider,
                        dimensions=provider.dimensions,
                        counter=counter,
                        embedding_identity=provider.indexing_identity,
                        chunk_config=ChunkingConfig(args.model_id, size, overlap),
                        backend=args.backend,
                        qdrant_url=args.qdrant_url,
                    )
                )
            except Exception as exc:
                output["failures"].append(
                    {
                        "model_id": args.model_id,
                        "chunk_setting": setting,
                        "error_type": type(exc).__name__,
                        "message": str(exc),
                    }
                )
    except Exception as exc:
        output["failures"].append(
            {"model_id": args.model_id, "error_type": type(exc).__name__, "message": str(exc)}
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    if output["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
