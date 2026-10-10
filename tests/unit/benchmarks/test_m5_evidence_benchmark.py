"""Validated corpus and actual M5 boundaries with deterministic embedding fixtures."""

import json
from pathlib import Path

import pytest

from benchmarks.benchmark_chunked_retrieval import load_evidence_dataset, run_dense_configuration
from context_engine.knowledge.chunking import ChunkingConfig
from tests.source_index_fixtures import CharacterCounter, FixtureEmbeddingProvider


def test_corpus_has_separate_splits_multispan_pdf_and_no_support() -> None:
    data = load_evidence_dataset()
    assert {query.split for query in data.queries} == {"development", "held_out"}
    assert len(data.sources) == 4
    assert sum(not query.evidence for query in data.queries) == 2
    pdf = next(
        source for source in data.processed_sources if source.provenance.format.value == "pdf"
    )
    assert {
        block.location.page_number for block in pdf.blocks if block.location.page_number is not None
    } == {1, 2}
    assert any(len(item.spans) > 1 for query in data.queries for item in query.evidence)


def test_same_labels_evaluate_multiple_chunk_configs_and_serialization() -> None:
    dataset = load_evidence_dataset()
    runs = [
        run_dense_configuration(
            dataset,
            provider=FixtureEmbeddingProvider(),
            dimensions=2,
            counter=CharacterCounter(),
            embedding_identity="fixture-v1",
            chunk_config=ChunkingConfig("fixture-embedding", size, 8),
        )
        for size in (96, 160)
    ]
    assert runs[0]["dataset_sha256"] == runs[1]["dataset_sha256"]
    assert runs[0]["configuration_id"] != runs[1]["configuration_id"]
    assert runs[0]["chunk_count"] > runs[1]["chunk_count"]
    assert not runs[0]["cleanup_errors"]
    restored = json.loads(json.dumps(runs[0], sort_keys=True))
    assert restored["backend"] == "in-memory-cosine"
    for query in runs[0]["queries"]:
        assert query["query_embedding_seconds"] >= 0 and query["vector_search_seconds"] >= 0
        assert query["retrieved_tokens_at_k"][1] > 2
        if not query["metrics"]["supported"]:
            assert query["metrics"]["recall_at_k"] is None
    assert runs[0]["persisted_index_bytes"] is None
    assert runs[0]["dense_vector_float32_bytes_estimate"] == runs[0]["chunk_count"] * 8


def test_ingestion_failure_is_explicit_and_preserves_primary_error() -> None:
    provider = FixtureEmbeddingProvider()
    provider.fail = True
    with pytest.raises(RuntimeError, match="Benchmark ingestion failed"):
        run_dense_configuration(
            load_evidence_dataset(),
            provider=provider,
            dimensions=2,
            counter=CharacterCounter(),
            embedding_identity="fixture-v1",
            chunk_config=ChunkingConfig("fixture-embedding", 96, 0),
        )


def test_query_prefix_is_counted_without_truncation() -> None:
    with pytest.raises(ValueError, match="query exceeds"):
        run_dense_configuration(
            load_evidence_dataset(),
            provider=FixtureEmbeddingProvider(),
            dimensions=2,
            counter=CharacterCounter(),
            embedding_identity="fixture-v1",
            chunk_config=ChunkingConfig("fixture-embedding", 96, 0),
            query_prefix="x" * 256,
        )


def test_stale_processed_text_digest_fails(tmp_path: Path) -> None:
    original = Path(__file__).resolve().parents[3] / "benchmarks/data/retrieval/m5"
    import shutil

    shutil.copytree(original, tmp_path / "m5")
    path = tmp_path / "m5/dataset.json"
    raw = json.loads(path.read_text())
    raw["sources"][0]["processed_text_sha256"] = "0" * 64
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="Stale"):
        load_evidence_dataset(path)
