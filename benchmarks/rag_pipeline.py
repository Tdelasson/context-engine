"""Shared opt-in ingestion/retrieval setup; no labels reach runtime candidates."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from typing import Any
from uuid import uuid4

from benchmarks.benchmark_chunked_retrieval import EvidenceDataset, MemoryEvidenceStore
from context_engine.knowledge.chunking import ChunkingConfig, StructureAwareChunker
from context_engine.knowledge.ingestion import SourceIngestionCoordinator, indexing_configuration_id
from context_engine.retrieval import (
    EmbeddingVectorStoreRetriever,
    LocalEmbeddingProvider,
    LocalEmbeddingProviderConfig,
    VectorStoreCollectionConfig,
)


@contextmanager
def indexed_pipeline(
    dataset: EvidenceDataset,
    embedding_reference: str,
    *,
    model_id: str,
    chunk_tokens: int = 128,
    overlap: int = 16,
    qdrant_url: str | None = None,
    reranking_reference: str | None = None,
) -> Iterator[tuple[dict[str, Any], dict[str, Any]]]:
    provider = LocalEmbeddingProvider(
        LocalEmbeddingProviderConfig(
            model_id,
            embedding_reference,
            batch_size=16,
            normalize_embeddings=True,
        )
    )
    chunker = StructureAwareChunker(
        ChunkingConfig(provider.model_id, chunk_tokens, overlap),
        provider.build_token_counter(),
    )
    config = VectorStoreCollectionConfig(
        "ce-rag-eval-" + uuid4().hex,
        provider.model_id,
        provider.dimensions,
        index_version="m5-chunks-v1",
        index_configuration_id=indexing_configuration_id(
            chunker,
            embedding_identity=provider.indexing_identity,
        ),
    )
    store: Any = MemoryEvidenceStore(config)
    if qdrant_url:
        from context_engine.retrieval.qdrant_lexical_index import QdrantBM25ChunkStore

        store = QdrantBM25ChunkStore(config, url=qdrant_url)
    coordinator = SourceIngestionCoordinator(
        chunker=chunker,
        embedding_provider=provider,
        vector_store=store,
        embedding_identity=provider.indexing_identity,
    )
    try:
        outcomes = [
            coordinator.ingest(source, dataset.processing_limits) for source in dataset.sources
        ]
        failed = [o for o in outcomes if o.status == "failed"]
        if failed:
            raise RuntimeError(f"Corpus ingestion failed: {failed}")
        dense = EmbeddingVectorStoreRetriever(embedding_provider=provider, vector_store=store)
        paths: dict[str, Any] = {"dense": dense}
        if qdrant_url:
            from context_engine.retrieval.hybrid import (
                HybridRetriever,
                HybridRetrieverConfig,
                lifecycle_visibility_reader,
            )
            from context_engine.retrieval.lexical import LexicalRetriever
            from context_engine.retrieval.qdrant_lexical_index import QdrantLexicalIndex

            lexical = LexicalRetriever(lexical_index=QdrantLexicalIndex(chunk_store=store))
            hybrid = HybridRetriever(
                dense_retriever=dense,
                lexical_retriever=lexical,
                config=HybridRetrieverConfig(20, 20, 20, 60),
                visibility_reader=lifecycle_visibility_reader(store),
            )
            paths.update(lexical=lexical, hybrid=hybrid)
            if reranking_reference:
                from context_engine.retrieval.local_cross_encoder import (
                    LocalCrossEncoderConfig,
                    LocalCrossEncoderReranker,
                )
                from context_engine.retrieval.reranking import (
                    RerankingRetriever,
                    RerankingRetrieverConfig,
                )

                paths["reranked"] = RerankingRetriever(
                    hybrid,
                    LocalCrossEncoderReranker(
                        LocalCrossEncoderConfig(
                            model_reference=reranking_reference,
                        )
                    ),
                    config=RerankingRetrieverConfig(20, 20),
                )
        elif reranking_reference:
            raise ValueError(
                "The integrated reranked comparison requires Qdrant hybrid candidates."
            )
        yield (
            paths,
            {
                "embedding_identity": provider.indexing_identity,
                "chunking": asdict(chunker.config),
                "index_configuration_id": coordinator.configuration_id,
                "chunk_count": sum(o.chunk_count for o in outcomes),
                "backend": "qdrant-bm25-dense" if qdrant_url else "in-memory-cosine",
                "qdrant_server": store._client.info().version if qdrant_url else None,
                "reranking_reference": reranking_reference,
            },
        )
    finally:
        if qdrant_url:
            import sys

            primary = sys.exception()
            try:
                store._client.delete_collection(config.collection_name)
            except Exception as exc:
                if primary is None:
                    raise
                primary.add_note(f"Collection cleanup failed: {exc}")
            finally:
                store._client.close()
