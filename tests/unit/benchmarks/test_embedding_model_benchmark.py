from __future__ import annotations

from collections.abc import Sequence

import pytest

from benchmarks import benchmark_embedding_models as benchmark
from context_engine.retrieval import Document, Embedding


class _FakeLocalEmbeddingProvider:
    def __init__(self, config: benchmark.LocalEmbeddingProviderConfig) -> None:
        self.model_id = config.model_id
        self.dimensions = 2
        self.model_parameter_bytes = 2_048

    def embed_documents(self, documents: Sequence[Document]) -> tuple[Embedding, ...]:
        return tuple(
            Embedding.from_sequence(
                vector=(1.0, 0.0) if document.document_id == "doc-a" else (0.0, 1.0),
                model_id=self.model_id,
            )
            for document in documents
        )

    def embed_query(self, query: str) -> Embedding:
        vector = (1.0, 0.0) if query == "find alpha" else (0.0, 1.0)
        return Embedding.from_sequence(vector=vector, model_id=self.model_id)


def _dataset() -> benchmark.BenchmarkDataset:
    return benchmark.BenchmarkDataset(
        dataset_id="test-dataset",
        version="1.0.0",
        description="Deterministic fixture",
        documents=(
            Document.from_mapping(document_id="doc-a", content="alpha"),
            Document.from_mapping(document_id="doc-b", content="beta"),
        ),
        queries=(
            benchmark.BenchmarkQuery("query-a", "find alpha", "alpha"),
            benchmark.BenchmarkQuery("query-b", "find beta", "beta"),
        ),
        relevance_judgments={
            "query-a": frozenset({"doc-a"}),
            "query-b": frozenset({"doc-b"}),
        },
        sha256="fixture-sha",
    )


def test_versioned_dataset_loads_into_domain_types() -> None:
    dataset = benchmark.load_dataset()

    assert dataset.dataset_id == "m4-retrieval-benchmark-v1"
    assert dataset.version == "1.0.0"
    assert len(dataset.documents) == 34
    assert len(dataset.queries) == 20
    assert set(dataset.relevance_judgments) == {query.query_id for query in dataset.queries}
    assert len(dataset.sha256) == 64


def test_candidate_models_use_explicit_provider_configuration() -> None:
    assert {model.model_id for model in benchmark.CANDIDATE_MODELS} == {
        "bge-m3",
        "qwen3-embedding-0.6b",
        "qwen3-embedding-8b",
        "nomic-embed-text",
        "all-minilm-l6-v2",
    }
    assert all(model.model_reference for model in benchmark.CANDIDATE_MODELS)
    nomic = next(
        model for model in benchmark.CANDIDATE_MODELS if model.model_id == "nomic-embed-text"
    )
    assert nomic.trust_remote_code is True
    assert nomic.query_prefix == "search_query: "
    assert nomic.document_prefix == "search_document: "


def test_model_benchmark_uses_ingestion_retrieval_and_deterministic_metrics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(benchmark, "LocalEmbeddingProvider", _FakeLocalEmbeddingProvider)

    result = benchmark.run_model_benchmark(
        benchmark.CandidateModel("fake", "local/fake"),
        _dataset(),
        k_values=(1, 2),
    )

    assert result["status"] == "completed"
    assert result["quality"]["recall_at_k"] == {"1": 1.0, "2": 1.0}
    assert result["quality"]["mean_reciprocal_rank"] == 1.0
    assert result["quality"]["ndcg_at_k"] == {"1": 1.0, "2": 1.0}
    assert result["dimensions"] == 2
    assert result["model_parameter_bytes"] == 2_048
    assert set(result["rankings"]) == {"query-a", "query-b"}


def test_default_selection_is_quality_first_and_reports_partial_runs() -> None:
    def result(model_id: str, ndcg: float, latency: float) -> dict[str, object]:
        return {
            "status": "completed",
            "model_id": model_id,
            "quality": {
                "ndcg_at_k": {"10": ndcg},
                "recall_at_k": {"10": 1.0},
                "mean_reciprocal_rank": ndcg,
            },
            "performance": {"query_embedding_latency_ms": {"mean": latency}},
            "model_parameter_bytes": 1_000,
        }

    selection = benchmark.select_default_model(
        (
            result("fast-lower-quality", 0.8, 1.0),
            result("slow-higher-quality", 0.9, 100.0),
            {"status": "failed", "model_id": "unavailable"},
        ),
        maximum_k=10,
    )

    assert selection["status"] == "provisional"
    assert selection["model_id"] == "slow-higher-quality"
    assert selection["failed_model_ids"] == ["unavailable"]


def test_default_selection_prefers_efficiency_when_quality_is_comparable() -> None:
    def result(
        model_id: str, ndcg: float, mrr: float, recall: float, size: int
    ) -> dict[str, object]:
        return {
            "status": "completed",
            "model_id": model_id,
            "quality": {
                "ndcg_at_k": {"10": ndcg},
                "recall_at_k": {"10": recall},
                "mean_reciprocal_rank": mrr,
            },
            "performance": {"query_embedding_latency_ms": {"mean": 10.0}},
            "model_parameter_bytes": size,
        }

    selection = benchmark.select_default_model(
        (
            result("large", 0.925, 0.915, 1.0, 2_000),
            result("small", 0.921, 0.912, 1.0, 100),
        ),
        maximum_k=10,
    )

    assert selection["status"] == "selected"
    assert selection["model_id"] == "small"


def test_markdown_report_contains_decision_and_environment() -> None:
    results = {
        "generated_at": "2026-08-25T00:00:00+00:00",
        "benchmark": {
            "dataset_id": "dataset",
            "dataset_version": "1",
            "dataset_sha256": "abc",
            "document_count": 2,
            "query_count": 2,
            "k_values": [1, 10],
            "distance_metric": "cosine",
        },
        "environment": {"platform": "test-os", "python_version": "3.12"},
        "models": [{"status": "failed", "model_id": "model", "error": {"type": "OOM"}}],
        "selection": {
            "status": "not_selected",
            "model_id": None,
            "reason": "No model completed.",
        },
    }

    report = benchmark.render_markdown_report(results)

    assert "# M4 Embedding Model Comparison" in report
    assert "test-os" in report
    assert "failed: OOM" in report
    assert "No model completed." in report
