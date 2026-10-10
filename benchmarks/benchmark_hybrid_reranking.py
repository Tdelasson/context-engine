"""Opt-in native Qdrant hybrid candidates followed by controlled local reranking."""

import argparse
import json
import sys
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

from benchmarks.benchmark_chunked_retrieval import load_evidence_dataset
from benchmarks.benchmark_reranking import compare_saved_candidates
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
    VectorStoreCollectionConfig,
)
from context_engine.retrieval.evidence_evaluation import evaluate_evidence_query
from context_engine.retrieval.hybrid import (
    HybridRetriever,
    HybridRetrieverConfig,
    lifecycle_visibility_reader,
)
from context_engine.retrieval.lexical import LexicalRetriever
from context_engine.retrieval.qdrant_lexical_index import QdrantBM25ChunkStore, QdrantLexicalIndex


def run_comparison(
    embedding_reference: str, reranking_reference: str, qdrant_url: str
) -> dict[str, object]:
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
    store = QdrantBM25ChunkStore(
        VectorStoreCollectionConfig(
            "ce-hybrid-reranking-" + uuid4().hex,
            provider.model_id,
            provider.dimensions,
            index_version=INDEX_VERSION,
            index_configuration_id=identity,
        ),
        url=qdrant_url,
    )
    try:
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
        config = HybridRetrieverConfig(
            dense_candidate_count=20,
            lexical_candidate_count=20,
            final_result_count=40,
            smoothing=60,
        )
        hybrid = HybridRetriever(
            dense_retriever=EmbeddingVectorStoreRetriever(
                embedding_provider=provider, vector_store=store
            ),
            lexical_retriever=LexicalRetriever(lexical_index=QdrantLexicalIndex(chunk_store=store)),
            config=config,
            visibility_reader=lifecycle_visibility_reader(store),
        )
        saved = {
            query.query_id: tuple(hybrid.retrieve(RetrievalRequest(query.text, 40)))
            for query in dataset.queries
        }
        report = compare_saved_candidates(
            dataset,
            counter,
            chunker,
            saved,
            reranking_reference,
            backend="native Qdrant dense + BM25 hybrid RRF candidates; identical saved-list replay",
        )
        report["environment"]["packages"]["qdrant-client"] = version("qdrant-client")
        report["upstream_candidate_union_metrics"] = {
            query.query_id: asdict(
                evaluate_evidence_query(
                    saved[query.query_id], query.evidence, k_values=(len(saved[query.query_id]),)
                )
            )
            for query in dataset.queries
        }
        report["upstream_configuration"] = asdict(config)
        report["lexical_configuration"] = asdict(store.lexical_config)
        report["decision"] = (
            "Optional only. Hybrid integration verified; small corpus and single warm passes "
            "do not establish a default quality/resource benefit."
        )
        return report
    finally:
        primary = sys.exception()
        try:
            store._client.delete_collection(store.collection_config.collection_name)
        except Exception as cleanup_error:
            if primary is None:
                raise
            primary.add_note(f"Benchmark collection cleanup failed: {cleanup_error}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embedding-reference", required=True)
    parser.add_argument("--reranking-reference", required=True)
    parser.add_argument("--qdrant-url", default="http://localhost:6333")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_comparison(args.embedding_reference, args.reranking_reference, args.qdrant_url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
