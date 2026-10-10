"""Paired BM25/dense comparison on identical committed M5 chunks and queries."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from benchmarks.benchmark_chunked_retrieval import load_evidence_dataset
from context_engine.knowledge.chunking import ChunkingConfig, StructureAwareChunker
from context_engine.knowledge.ingestion import SourceIngestionCoordinator, indexing_configuration_id
from context_engine.retrieval import (
    EmbeddingVectorStoreRetriever,
    LocalEmbeddingProvider,
    LocalEmbeddingProviderConfig,
    RetrievalRequest,
    VectorStoreCollectionConfig,
)
from context_engine.retrieval.evidence_evaluation import evaluate_evidence_query
from context_engine.retrieval.lexical import LexicalRetriever
from context_engine.retrieval.qdrant_lexical_index import QdrantBM25ChunkStore, QdrantLexicalIndex


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-reference", required=True)
    parser.add_argument("--qdrant-url", default="http://localhost:6333")
    parser.add_argument("--chunk-tokens", type=int, default=128)
    parser.add_argument("--overlap-tokens", type=int, default=16)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dataset = load_evidence_dataset()
    provider = LocalEmbeddingProvider(
        LocalEmbeddingProviderConfig(
            model_id="sentence-transformers/all-MiniLM-L6-v2",
            model_reference=args.model_reference,
            batch_size=8,
            normalize_embeddings=True,
        )
    )
    counter = provider.build_token_counter()
    chunker = StructureAwareChunker(
        ChunkingConfig(
            model_id=provider.model_id,
            max_input_tokens=args.chunk_tokens,
            overlap_tokens=args.overlap_tokens,
        ),
        counter,
    )
    config = VectorStoreCollectionConfig(
        f"ce-bm25-paired-{uuid4().hex}",
        provider.model_id,
        provider.dimensions,
        index_version="m5-chunks-v1",
        index_configuration_id=indexing_configuration_id(
            chunker, embedding_identity=provider.indexing_identity
        ),
    )
    store = QdrantBM25ChunkStore(config, url=args.qdrant_url)
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
        strategies = {
            "dense": EmbeddingVectorStoreRetriever(embedding_provider=provider, vector_store=store),
            "lexical": LexicalRetriever(lexical_index=QdrantLexicalIndex(chunk_store=store)),
        }
        rows = []
        for query in dataset.queries:
            for strategy, retriever in strategies.items():
                started = perf_counter()
                results = tuple(retriever.retrieve(RetrievalRequest(query.text, 10)))
                elapsed = perf_counter() - started
                rows.append(
                    {
                        "query_id": query.query_id,
                        "query": query.text,
                        "split": query.split,
                        "strategy": strategy,
                        "seconds": elapsed,
                        "metrics": asdict(
                            evaluate_evidence_query(results, query.evidence, k_values=(1, 5, 10))
                        ),
                        "results": [
                            {
                                "chunk_id": result.document.document_id,
                                "score": result.score,
                                "source_id": result.document.metadata_as_mapping()["source_id"],
                                "content_sha256": result.document.metadata_as_mapping()[
                                    "content_sha256"
                                ],
                                "spans": result.document.metadata_as_mapping()["spans"],
                                "diagnostics": [asdict(stage) for stage in result.diagnostics],
                            }
                            for result in results
                        ],
                    }
                )
        output = {
            "dataset_sha256": dataset.sha256,
            "dataset_id": dataset.dataset_id,
            "chunk_configuration": asdict(chunker.config),
            "index_configuration_id": coordinator.configuration_id,
            "lexical_configuration": asdict(store.lexical_config),
            "lexical_configuration_id": store.lexical_config.configuration_id,
            "embedding_identity": provider.indexing_identity,
            "tokenizer_id": counter.tokenizer_id,
            "chunk_count": sum(outcome.chunk_count for outcome in outcomes),
            "combined_ingestion_seconds": ingestion_seconds,
            "indexing_cost_note": "Combined processing/chunking/dense+BM25 writes; "
            "lexical incremental encoding is not separately timed.",
            "qdrant_version": store._client.info().version,
            "queries": rows,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    finally:
        store._client.delete_collection(config.collection_name)


if __name__ == "__main__":
    main()
