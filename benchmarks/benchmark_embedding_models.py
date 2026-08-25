"""Run the model-independent M4 retrieval benchmark against local models.

Install the optional dependencies with ``pip install -e ".[benchmark]"`` and
run this module explicitly. Real model inference is intentionally excluded from
the normal unit-test and CI paths.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import statistics
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from math import sqrt
from pathlib import Path
from time import perf_counter
from typing import Any, cast

from context_engine.retrieval import (
    Document,
    Embedding,
    EmbeddingProvider,
    EmbeddingVectorStoreRetriever,
    Ingestor,
    LocalEmbeddingProvider,
    LocalEmbeddingProviderConfig,
    MetadataFilter,
    RetrievalQualityMetrics,
    RetrievalRequest,
    SearchResult,
    VectorDistanceMetric,
    VectorStore,
    VectorStoreCollectionConfig,
    VectorStoreConfigurationError,
    VectorStoreRecord,
    evaluate_rankings,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_PATH = (
    REPO_ROOT / "benchmarks" / "data" / "retrieval" / "m4-retrieval-dataset-v1.json"
)
DEFAULT_JSON_OUTPUT_PATH = REPO_ROOT / "benchmarks" / "results" / "m4-retrieval-results.json"
DEFAULT_MARKDOWN_OUTPUT_PATH = (
    REPO_ROOT / "docs" / "experiments" / "m4-embedding-model-comparison.md"
)
DEFAULT_K_VALUES = (1, 5, 10)


class BenchmarkConfigurationError(ValueError):
    """Raised when benchmark inputs or configuration are invalid."""


@dataclass(frozen=True, slots=True)
class BenchmarkQuery:
    """One stable query in the retrieval benchmark dataset."""

    query_id: str
    text: str
    intent: str


@dataclass(frozen=True, slots=True)
class BenchmarkDataset:
    """Validated, provider-independent benchmark input."""

    dataset_id: str
    version: str
    description: str
    documents: tuple[Document, ...]
    queries: tuple[BenchmarkQuery, ...]
    relevance_judgments: Mapping[str, frozenset[str]]
    sha256: str


@dataclass(frozen=True, slots=True)
class CandidateModel:
    """Explicit local model configuration used by the shared benchmark flow."""

    model_id: str
    model_reference: str
    batch_size: int = 8
    normalize_embeddings: bool = True
    query_prefix: str = ""
    document_prefix: str = ""
    trust_remote_code: bool = False

    def provider_config(self) -> LocalEmbeddingProviderConfig:
        return LocalEmbeddingProviderConfig(
            model_id=self.model_id,
            model_reference=self.model_reference,
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize_embeddings,
            query_prefix=self.query_prefix,
            document_prefix=self.document_prefix,
            trust_remote_code=self.trust_remote_code,
        )


CANDIDATE_MODELS: tuple[CandidateModel, ...] = (
    CandidateModel(model_id="bge-m3", model_reference="BAAI/bge-m3"),
    CandidateModel(
        model_id="qwen3-embedding-0.6b",
        model_reference="Qwen/Qwen3-Embedding-0.6B",
        query_prefix=(
            "Instruct: Retrieve the most relevant Context Engine document for the query.\nQuery: "
        ),
    ),
    CandidateModel(
        model_id="qwen3-embedding-8b",
        model_reference="Qwen/Qwen3-Embedding-8B",
        batch_size=2,
        query_prefix=(
            "Instruct: Retrieve the most relevant Context Engine document for the query.\nQuery: "
        ),
    ),
    CandidateModel(
        model_id="nomic-embed-text",
        model_reference="nomic-ai/nomic-embed-text-v1.5",
        query_prefix="search_query: ",
        document_prefix="search_document: ",
        trust_remote_code=True,
    ),
    CandidateModel(
        model_id="all-minilm-l6-v2",
        model_reference="sentence-transformers/all-MiniLM-L6-v2",
    ),
)


class InMemoryCosineVectorStore(VectorStore):
    """Small deterministic VectorStore used only by the portable benchmark."""

    def __init__(self, config: VectorStoreCollectionConfig) -> None:
        if config.distance_metric is not VectorDistanceMetric.COSINE:
            raise VectorStoreConfigurationError(
                "The M4 in-memory benchmark store supports cosine similarity only."
            )
        self._config = config
        self._records: dict[str, VectorStoreRecord] = {}

    def upsert(self, records: Sequence[VectorStoreRecord]) -> None:
        for record in records:
            self._config.ensure_embedding_compatible(record.embedding)
            self._records[record.document.document_id] = record

    def search(
        self,
        query_embedding: Embedding,
        *,
        top_k: int = 5,
        metadata_filter: MetadataFilter | None = None,
    ) -> tuple[SearchResult, ...]:
        if top_k <= 0:
            raise VectorStoreConfigurationError("top_k must be greater than zero.")
        self._config.ensure_embedding_compatible(query_embedding)
        matches = (
            record
            for record in self._records.values()
            if metadata_filter is None
            or all(
                record.document.metadata_as_mapping().get(key) == value
                for key, value in metadata_filter.equals
            )
        )
        scored = [
            SearchResult(
                document=record.document,
                score=_cosine_similarity(query_embedding.vector, record.embedding.vector),
            )
            for record in matches
        ]
        scored.sort(key=lambda result: (-result.score, result.document.document_id))
        return tuple(scored[:top_k])

    def delete(self, document_ids: Sequence[str]) -> None:
        for document_id in document_ids:
            self._records.pop(document_id, None)


class MeasuringEmbeddingProvider(EmbeddingProvider):
    """Record inference timings while preserving the provider boundary."""

    def __init__(self, provider: EmbeddingProvider) -> None:
        self._provider = provider
        self.document_embedding_seconds: list[float] = []
        self.query_embedding_seconds: list[float] = []

    def embed_documents(self, documents: Sequence[Document]) -> Sequence[Embedding]:
        started = perf_counter()
        try:
            return self._provider.embed_documents(documents)
        finally:
            self.document_embedding_seconds.append(perf_counter() - started)

    def embed_query(self, query: str) -> Embedding:
        started = perf_counter()
        try:
            return self._provider.embed_query(query)
        finally:
            self.query_embedding_seconds.append(perf_counter() - started)


class MeasuringVectorStore(VectorStore):
    """Record vector-search timings while preserving the store boundary."""

    def __init__(self, vector_store: VectorStore) -> None:
        self._vector_store = vector_store
        self.search_seconds: list[float] = []

    def upsert(self, records: Sequence[VectorStoreRecord]) -> None:
        self._vector_store.upsert(records)

    def search(
        self,
        query_embedding: Embedding,
        *,
        top_k: int = 5,
        metadata_filter: MetadataFilter | None = None,
    ) -> Sequence[SearchResult]:
        started = perf_counter()
        try:
            return self._vector_store.search(
                query_embedding,
                top_k=top_k,
                metadata_filter=metadata_filter,
            )
        finally:
            self.search_seconds.append(perf_counter() - started)

    def delete(self, document_ids: Sequence[str]) -> None:
        self._vector_store.delete(document_ids)


def load_dataset(path: Path = DEFAULT_DATASET_PATH) -> BenchmarkDataset:
    """Load and validate the version-controlled benchmark dataset."""
    raw_bytes = path.read_bytes()
    try:
        payload = json.loads(raw_bytes)
    except json.JSONDecodeError as exc:
        raise BenchmarkConfigurationError(f"Dataset is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise BenchmarkConfigurationError("Dataset root must be a JSON object.")

    dataset_id = _required_string(payload, "dataset_id")
    version = _required_string(payload, "version")
    description = _required_string(payload, "description")
    raw_documents = _required_list(payload, "documents")
    raw_queries = _required_list(payload, "queries")
    raw_judgments = _required_list(payload, "relevance_judgments")

    documents = tuple(_parse_document(item) for item in raw_documents)
    queries = tuple(_parse_query(item) for item in raw_queries)
    judgment_pairs = [_parse_judgment(item) for item in raw_judgments]
    judgments = dict(judgment_pairs)

    document_ids = [document.document_id for document in documents]
    query_ids = [query.query_id for query in queries]
    if len(document_ids) != len(set(document_ids)):
        raise BenchmarkConfigurationError("Dataset document IDs must be unique.")
    if len(query_ids) != len(set(query_ids)):
        raise BenchmarkConfigurationError("Dataset query IDs must be unique.")
    if len(judgments) != len(judgment_pairs) or set(judgments) != set(query_ids):
        raise BenchmarkConfigurationError("Every query must have exactly one relevance judgment.")
    unknown_relevant_ids = set().union(*judgments.values()) - set(document_ids)
    if unknown_relevant_ids:
        raise BenchmarkConfigurationError(
            "Relevance judgments reference unknown document IDs: "
            + ", ".join(sorted(unknown_relevant_ids))
        )

    return BenchmarkDataset(
        dataset_id=dataset_id,
        version=version,
        description=description,
        documents=documents,
        queries=queries,
        relevance_judgments=judgments,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
    )


def run_model_benchmark(
    model: CandidateModel,
    dataset: BenchmarkDataset,
    *,
    k_values: Sequence[int] = DEFAULT_K_VALUES,
) -> dict[str, Any]:
    """Run the shared retrieval procedure for one candidate model."""
    maximum_k = max(k_values)
    memory_before = _current_process_rss_bytes()
    initialization_started = perf_counter()
    provider = LocalEmbeddingProvider(model.provider_config())
    initialization_seconds = perf_counter() - initialization_started
    memory_after_load = _current_process_rss_bytes()

    store_config = VectorStoreCollectionConfig(
        collection_name=f"m4-benchmark-{model.model_id}",
        embedding_model_id=provider.model_id,
        dimensions=provider.dimensions,
        distance_metric=VectorDistanceMetric.COSINE,
    )
    measured_provider = MeasuringEmbeddingProvider(provider)
    measured_store = MeasuringVectorStore(InMemoryCosineVectorStore(store_config))
    Ingestor(measured_provider, measured_store).ingest_documents(dataset.documents)
    retriever = EmbeddingVectorStoreRetriever(
        embedding_provider=measured_provider,
        vector_store=measured_store,
    )

    rankings: dict[str, tuple[str, ...]] = {}
    for query in dataset.queries:
        results = retriever.retrieve(RetrievalRequest(query=query.text, top_k=maximum_k))
        rankings[query.query_id] = tuple(result.document.document_id for result in results)

    quality = evaluate_rankings(
        rankings,
        dataset.relevance_judgments,
        k_values=k_values,
    )
    document_seconds = sum(measured_provider.document_embedding_seconds)
    return {
        "status": "completed",
        "model_id": model.model_id,
        "model_reference": model.model_reference,
        "resolved_model_revision": _resolved_huggingface_revision(model.model_reference),
        "configuration": asdict(model),
        "quality": _quality_as_dict(quality),
        "performance": {
            "initialization_seconds": initialization_seconds,
            "document_embedding_seconds": document_seconds,
            "document_embeddings_per_second": (
                len(dataset.documents) / document_seconds if document_seconds > 0 else None
            ),
            "query_embedding_latency_ms": _latency_summary(
                measured_provider.query_embedding_seconds
            ),
            "vector_search_latency_ms": _latency_summary(measured_store.search_seconds),
        },
        "dimensions": provider.dimensions,
        "model_parameter_bytes": provider.model_parameter_bytes,
        "process_rss_bytes": {
            "before_model_load": memory_before,
            "after_model_load": memory_after_load,
            "increase_after_model_load": _difference(memory_after_load, memory_before),
        },
        "rankings": rankings,
    }


def run_benchmark(
    models: Sequence[CandidateModel],
    *,
    dataset_path: Path = DEFAULT_DATASET_PATH,
    k_values: Sequence[int] = DEFAULT_K_VALUES,
    hardware_excluded_model_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Run all requested models and retain structured failures for reproducibility."""
    if not models:
        raise BenchmarkConfigurationError("At least one candidate model is required.")
    if not k_values or any(k <= 0 for k in k_values):
        raise BenchmarkConfigurationError("K values must be positive integers.")
    all_candidate_ids = [model.model_id for model in CANDIDATE_MODELS]
    requested_ids = [model.model_id for model in models]
    excluded_ids = sorted(set(hardware_excluded_model_ids))
    unknown_excluded_ids = set(excluded_ids) - set(all_candidate_ids)
    if unknown_excluded_ids:
        raise BenchmarkConfigurationError(
            "Unknown hardware-excluded model IDs: " + ", ".join(sorted(unknown_excluded_ids))
        )
    overlapping_ids = set(excluded_ids) & set(requested_ids)
    if overlapping_ids:
        raise BenchmarkConfigurationError(
            "A model cannot be requested and hardware-excluded: "
            + ", ".join(sorted(overlapping_ids))
        )
    dataset = load_dataset(dataset_path)
    model_results: list[dict[str, Any]] = []
    for model in models:
        print(f"Running M4 retrieval benchmark for {model.model_id}...", flush=True)
        try:
            model_results.append(run_model_benchmark(model, dataset, k_values=k_values))
        except Exception as exc:  # benchmark boundary records unavailable models
            model_results.append(
                {
                    "status": "failed",
                    "model_id": model.model_id,
                    "model_reference": model.model_reference,
                    "configuration": asdict(model),
                    "error": _error_details(exc),
                }
            )

    return {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "benchmark": {
            "dataset_id": dataset.dataset_id,
            "dataset_version": dataset.version,
            "dataset_sha256": dataset.sha256,
            "document_count": len(dataset.documents),
            "query_count": len(dataset.queries),
            "k_values": list(k_values),
            "distance_metric": VectorDistanceMetric.COSINE.value,
            "all_candidate_model_ids": all_candidate_ids,
            "requested_model_ids": requested_ids,
            "hardware_exclusions": {
                model_id: "Excluded because the local machine cannot run this model reliably."
                for model_id in excluded_ids
            },
        },
        "environment": _environment_details(),
        "models": model_results,
        "selection": select_default_model(
            model_results,
            maximum_k=max(k_values),
            expected_model_ids=all_candidate_ids,
            hardware_excluded_model_ids=excluded_ids,
        ),
    }


def select_default_model(
    model_results: Sequence[Mapping[str, Any]],
    *,
    maximum_k: int,
    expected_model_ids: Sequence[str] | None = None,
    hardware_excluded_model_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Select quality-first while avoiding disproportionate cost for marginal gains."""
    completed = [result for result in model_results if result.get("status") == "completed"]
    if not completed:
        return {
            "status": "not_selected",
            "model_id": None,
            "reason": "No candidate model completed the benchmark.",
        }

    def quality_values(result: Mapping[str, Any]) -> tuple[float, float, float]:
        quality = cast(Mapping[str, Any], result["quality"])
        ndcg = cast(Mapping[str, float], quality["ndcg_at_k"])
        recall = cast(Mapping[str, float], quality["recall_at_k"])
        return (
            float(ndcg[str(maximum_k)]),
            float(quality["mean_reciprocal_rank"]),
            float(recall[str(maximum_k)]),
        )

    best_ndcg = max(quality_values(result)[0] for result in completed)
    ndcg_shortlist = [
        result for result in completed if quality_values(result)[0] >= best_ndcg - 0.01
    ]
    best_mrr = max(quality_values(result)[1] for result in ndcg_shortlist)
    mrr_shortlist = [
        result for result in ndcg_shortlist if quality_values(result)[1] >= best_mrr - 0.01
    ]
    best_recall = max(quality_values(result)[2] for result in mrr_shortlist)
    quality_shortlist = [
        result for result in mrr_shortlist if quality_values(result)[2] >= best_recall - 0.01
    ]

    def efficiency_key(result: Mapping[str, Any]) -> tuple[float, float, float, float, float]:
        performance = cast(Mapping[str, Any], result["performance"])
        query_latency = cast(Mapping[str, float], performance["query_embedding_latency_ms"])
        parameter_bytes = result.get("model_parameter_bytes")
        footprint = float(parameter_bytes) if isinstance(parameter_bytes, int) else float("inf")
        ndcg, mrr, recall = quality_values(result)
        return (
            -footprint,
            -float(query_latency["mean"]),
            ndcg,
            mrr,
            recall,
        )

    selected = max(quality_shortlist, key=efficiency_key)
    shortlist_ids = [str(result["model_id"]) for result in quality_shortlist]
    evaluated_ids = [str(result["model_id"]) for result in completed]
    failed_ids = [
        str(result["model_id"]) for result in model_results if result.get("status") != "completed"
    ]
    expected = set(expected_model_ids or evaluated_ids)
    excluded = set(hardware_excluded_model_ids)
    not_evaluated_ids = sorted(
        expected - excluded - {str(result["model_id"]) for result in model_results}
    )
    status = "selected"
    if failed_ids or not_evaluated_ids:
        status = "provisional"
    elif excluded:
        status = "selected_with_hardware_exclusions"
    return {
        "status": status,
        "model_id": selected["model_id"],
        "evaluated_model_ids": evaluated_ids,
        "failed_model_ids": failed_ids,
        "not_evaluated_model_ids": not_evaluated_ids,
        "hardware_excluded_model_ids": sorted(excluded),
        "quality_shortlist_model_ids": shortlist_ids,
        "policy": (
            f"Successively shortlist models within 0.01 of the best NDCG@{maximum_k}, MRR, and "
            f"Recall@{maximum_k}; then prefer lower parameter footprint and mean query latency."
        ),
        "reason": (
            f"{selected['model_id']} remained in the quality-equivalent shortlist and had the "
            "best recorded local efficiency trade-off under the selection policy."
        ),
    }


def write_results(results: Mapping[str, Any], *, json_path: Path, markdown_path: Path) -> None:
    """Write machine-readable results and a human-readable comparison."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown_report(results), encoding="utf-8")


def render_markdown_report(results: Mapping[str, Any]) -> str:
    """Render a repository-friendly comparison from the canonical JSON result."""
    benchmark = cast(Mapping[str, Any], results["benchmark"])
    environment = cast(Mapping[str, Any], results["environment"])
    selection = cast(Mapping[str, Any], results["selection"])
    maximum_k = max(cast(Sequence[int], benchmark["k_values"]))
    lines = [
        "# M4 Embedding Model Comparison",
        "",
        f"Generated: `{results['generated_at']}`",
        "",
        "## Configuration",
        "",
        f"- Dataset: `{benchmark['dataset_id']}` version `{benchmark['dataset_version']}`",
        f"- Dataset SHA-256: `{benchmark['dataset_sha256']}`",
        f"- Documents / queries: {benchmark['document_count']} / {benchmark['query_count']}",
        f"- K values: {', '.join(str(value) for value in benchmark['k_values'])}",
        f"- Distance metric: `{benchmark['distance_metric']}`",
        f"- Platform: `{environment['platform']}`",
        f"- Python: `{environment['python_version']}`",
        "",
        "## Results",
        "",
        f"| Model | Status | Recall@{maximum_k} | MRR | NDCG@{maximum_k} | "
        "Dimensions | Query mean ms | Docs/sec | Parameter GiB |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for raw_result in cast(Sequence[Mapping[str, Any]], results["models"]):
        lines.append(_model_markdown_row(raw_result, maximum_k=maximum_k))

    lines.extend(
        [
            "",
            "## Default Model Decision",
            "",
            f"**Status:** `{selection['status']}`",
            "",
            f"**Selected model:** `{selection.get('model_id') or 'none'}`",
            "",
            str(selection["reason"]),
            "",
        ]
    )
    if selection.get("policy"):
        lines.extend([f"Selection policy: {selection['policy']}", ""])
    if selection.get("failed_model_ids"):
        failed = ", ".join(f"`{model_id}`" for model_id in selection["failed_model_ids"])
        lines.extend(
            [
                f"The decision is provisional because these candidates failed: {failed}.",
                "Review their structured errors in the JSON result before adopting the default.",
                "",
            ]
        )
    if selection.get("not_evaluated_model_ids"):
        missing = ", ".join(f"`{model_id}`" for model_id in selection["not_evaluated_model_ids"])
        lines.extend(
            [
                "The decision is provisional because these candidates were not evaluated: "
                f"{missing}.",
                "",
            ]
        )
    if selection.get("hardware_excluded_model_ids"):
        excluded = ", ".join(
            f"`{model_id}`" for model_id in selection["hardware_excluded_model_ids"]
        )
        lines.extend(
            [
                f"Hardware exclusion: {excluded} was not run on this machine.",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
            "Quality metrics are comparable because every completed model used the same dataset, "
            "relevance judgments, cosine search, and K values. Latency and memory figures describe "
            "only the recorded local environment and are not production capacity guarantees.",
            "",
        ]
    )
    return "\n".join(lines)


def _model_markdown_row(result: Mapping[str, Any], *, maximum_k: int) -> str:
    if result.get("status") != "completed":
        error = cast(Mapping[str, Any], result.get("error", {}))
        status = f"failed: {error.get('type', 'unknown')}"
        return f"| {result['model_id']} | {status} | — | — | — | — | — | — | — |"
    quality = cast(Mapping[str, Any], result["quality"])
    performance = cast(Mapping[str, Any], result["performance"])
    recall = cast(Mapping[str, float], quality["recall_at_k"])
    ndcg = cast(Mapping[str, float], quality["ndcg_at_k"])
    query_latency = cast(Mapping[str, float], performance["query_embedding_latency_ms"])
    parameter_bytes = cast(int | None, result["model_parameter_bytes"])
    parameter_gib = parameter_bytes / (1024**3) if parameter_bytes is not None else None
    parameter_display = f"{parameter_gib:.3f}" if parameter_gib is not None else "—"
    return (
        f"| {result['model_id']} | completed | {recall[str(maximum_k)]:.4f} | "
        f"{float(quality['mean_reciprocal_rank']):.4f} | "
        f"{ndcg[str(maximum_k)]:.4f} | {result['dimensions']} | "
        f"{query_latency['mean']:.3f} | "
        f"{float(performance['document_embeddings_per_second']):.3f} | "
        f"{parameter_display} |"
    )


def _quality_as_dict(quality: RetrievalQualityMetrics) -> dict[str, Any]:
    return {
        "recall_at_k": {str(k): value for k, value in quality.recall_at_k.items()},
        "mean_reciprocal_rank": quality.mean_reciprocal_rank,
        "ndcg_at_k": {str(k): value for k, value in quality.ndcg_at_k.items()},
    }


def _latency_summary(seconds: Sequence[float]) -> dict[str, float]:
    if not seconds:
        raise BenchmarkConfigurationError("Cannot summarize an empty timing sequence.")
    milliseconds = [value * 1_000 for value in seconds]
    ordered = sorted(milliseconds)
    p95_index = min(len(ordered) - 1, max(0, round(0.95 * len(ordered) + 0.5) - 1))
    return {
        "mean": statistics.fmean(milliseconds),
        "median": statistics.median(milliseconds),
        "p95": ordered[p95_index],
        "minimum": ordered[0],
        "maximum": ordered[-1],
    }


def _environment_details() -> dict[str, Any]:
    details: dict[str, Any] = {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "cpu_count": os.cpu_count(),
        "packages": {
            package: _package_version(package)
            for package in ("sentence-transformers", "transformers", "torch")
        },
    }
    try:
        import importlib

        torch_module = importlib.import_module("torch")
        cuda = torch_module.cuda
        details["torch_cuda_available"] = cuda.is_available()
        details["torch_cuda_device_count"] = cuda.device_count()
        details["torch_cuda_devices"] = [
            cuda.get_device_name(index) for index in range(cuda.device_count())
        ]
    except ImportError:
        details["torch_cuda_available"] = None
    return details


def _current_process_rss_bytes() -> int | None:
    """Read resident memory on supported platforms without another dependency."""
    if os.name == "nt":
        return _windows_process_rss_bytes()
    statm_path = Path("/proc/self/statm")
    if not statm_path.exists() or not hasattr(os, "sysconf"):
        return None
    try:
        resident_pages = int(statm_path.read_text(encoding="ascii").split()[1])
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
    except (IndexError, OSError, ValueError):
        return None
    return resident_pages * page_size


def _windows_process_rss_bytes() -> int | None:
    try:
        import ctypes
        from ctypes import wintypes

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(ProcessMemoryCounters),
            wintypes.DWORD,
        )
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        process = kernel32.GetCurrentProcess()
        succeeded = psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb)
        return int(counters.WorkingSetSize) if succeeded else None
    except (AttributeError, OSError):
        return None


def _package_version(package: str) -> str | None:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def _resolved_huggingface_revision(model_reference: str) -> str | None:
    cache_key = "models--" + model_reference.replace("/", "--")
    reference_path = Path.home() / ".cache" / "huggingface" / "hub" / cache_key / "refs" / "main"
    try:
        revision = reference_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return revision or None


def _error_details(exc: Exception) -> dict[str, Any]:
    causes: list[dict[str, str]] = []
    cause = exc.__cause__
    while cause is not None:
        causes.append({"type": type(cause).__name__, "message": str(cause)})
        cause = cause.__cause__
    return {"type": type(exc).__name__, "message": str(exc), "causes": causes}


def _difference(value: int | None, baseline: int | None) -> int | None:
    if value is None or baseline is None:
        return None
    return value - baseline


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise VectorStoreConfigurationError("Cosine similarity requires equal vector dimensions.")
    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / (left_norm * right_norm)


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise BenchmarkConfigurationError(f"Dataset field '{key}' must be a non-empty string.")
    return value


def _required_list(payload: Mapping[str, Any], key: str) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        raise BenchmarkConfigurationError(f"Dataset field '{key}' must be a non-empty list.")
    return value


def _parse_document(raw: Any) -> Document:
    if not isinstance(raw, dict):
        raise BenchmarkConfigurationError("Every dataset document must be an object.")
    metadata = raw.get("metadata")
    if not isinstance(metadata, dict):
        raise BenchmarkConfigurationError("Document metadata must be an object.")
    return Document.from_mapping(
        document_id=_required_string(raw, "document_id"),
        content=_required_string(raw, "content"),
        metadata=metadata,
    )


def _parse_query(raw: Any) -> BenchmarkQuery:
    if not isinstance(raw, dict):
        raise BenchmarkConfigurationError("Every dataset query must be an object.")
    return BenchmarkQuery(
        query_id=_required_string(raw, "query_id"),
        text=_required_string(raw, "text"),
        intent=_required_string(raw, "intent"),
    )


def _parse_judgment(raw: Any) -> tuple[str, frozenset[str]]:
    if not isinstance(raw, dict):
        raise BenchmarkConfigurationError("Every relevance judgment must be an object.")
    query_id = _required_string(raw, "query_id")
    relevant_ids = _required_list(raw, "relevant_document_ids")
    if not all(isinstance(document_id, str) and document_id for document_id in relevant_ids):
        raise BenchmarkConfigurationError("Relevant document IDs must be non-empty strings.")
    normalized = frozenset(cast(list[str], relevant_ids))
    if len(normalized) != len(relevant_ids):
        raise BenchmarkConfigurationError("Relevant document IDs must not contain duplicates.")
    return query_id, normalized


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--models",
        nargs="+",
        choices=[model.model_id for model in CANDIDATE_MODELS],
        required=True,
        help="Candidate model IDs to run. Explicit selection prevents accidental 8B model loads.",
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument(
        "--hardware-excluded-models",
        nargs="*",
        choices=[model.model_id for model in CANDIDATE_MODELS],
        default=[],
        help="Candidates intentionally skipped because this machine cannot run them reliably.",
    )
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    selected_ids = set(cast(list[str], args.models))
    selected_models = tuple(model for model in CANDIDATE_MODELS if model.model_id in selected_ids)
    results = run_benchmark(
        selected_models,
        dataset_path=cast(Path, args.dataset),
        k_values=DEFAULT_K_VALUES,
        hardware_excluded_model_ids=cast(list[str], args.hardware_excluded_models),
    )
    write_results(
        results,
        json_path=cast(Path, args.json_output),
        markdown_path=cast(Path, args.markdown_output),
    )
    failed_count = sum(
        result.get("status") != "completed"
        for result in cast(Sequence[Mapping[str, Any]], results["models"])
    )
    print(f"Wrote {args.json_output} and {args.markdown_output}.")
    return 1 if failed_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
