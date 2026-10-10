"""Explicit real local inference and deployed Qdrant evidence-path checks."""

import os

import pytest

from benchmarks.benchmark_chunked_retrieval import load_evidence_dataset, run_dense_configuration
from context_engine.knowledge.chunking import ChunkingConfig
from context_engine.retrieval import LocalEmbeddingProvider, LocalEmbeddingProviderConfig


@pytest.mark.parametrize("backend", ["in-memory-cosine", "qdrant-server"])
def test_real_dense_evidence_path(backend: str) -> None:
    if os.getenv("CONTEXT_ENGINE_RUN_LOCAL_EMBEDDING_INTEGRATION") != "1":
        pytest.skip("Real local embedding inference is opt-in.")
    if backend == "qdrant-server" and os.getenv("CONTEXT_ENGINE_RUN_QDRANT_INTEGRATION") != "1":
        pytest.skip("Deployed Qdrant evidence retrieval is opt-in.")
    provider = LocalEmbeddingProvider(
        LocalEmbeddingProviderConfig(
            "all-minilm-l6-v2",
            os.getenv(
                "CONTEXT_ENGINE_EMBEDDING_MODEL_REFERENCE", "sentence-transformers/all-MiniLM-L6-v2"
            ),
            normalize_embeddings=True,
        )
    )
    data = load_evidence_dataset()
    run = run_dense_configuration(
        data,
        provider=provider,
        dimensions=provider.dimensions,
        counter=provider.build_token_counter(),
        embedding_identity=provider.indexing_identity,
        chunk_config=ChunkingConfig(provider.model_id, 160, 24),
        backend=backend,
        qdrant_url=os.getenv("CONTEXT_ENGINE_QDRANT_URL", "http://localhost:6333"),
    )
    approval = next(row for row in run["queries"] if row["query_id"] == "dev-approval")
    assert approval["metrics"]["recall_at_k"][10] == 1
    assert any(result["source_id"] == "m5:operations.md" for result in approval["results"])
    assert run["chunk_count"] > len(data.sources)
    assert run["backend"] == backend
    assert not run["cleanup_errors"]
