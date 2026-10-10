"""Opt-in native hybrid retrieval through local reranking and the policy/runtime boundary."""

import os
from uuid import uuid4

import pytest

from context_engine.knowledge.chunking import ChunkingConfig, StructureAwareChunker
from context_engine.knowledge.ingestion import SourceIngestionCoordinator, indexing_configuration_id
from context_engine.knowledge.processing import SourceFormat, SourceInput
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
from context_engine.retrieval.qdrant_lexical_index import QdrantBM25ChunkStore, QdrantLexicalIndex
from context_engine.retrieval.reranking import RerankingRetriever, RerankingRetrieverConfig
from context_engine.retrieval.retriever import EmbeddingVectorStoreRetriever
from context_engine.retrieval.vector_store import VectorStoreCollectionConfig
from context_engine.tools.policy import ToolNamePolicy, ToolPolicyDecision
from context_engine.tools.retrieval.tool import SearchDocumentsTool
from context_engine.tools.runtime import ToolInvocation, ToolRegistry, ToolResultStatus, ToolRuntime
from tests.source_index_fixtures import CharacterCounter, FixtureEmbeddingProvider


def test_native_hybrid_local_reranking_runtime() -> None:
    reference = os.getenv("CONTEXT_ENGINE_RERANKING_INTEGRATION_MODEL")
    if not reference or os.getenv("CONTEXT_ENGINE_RUN_QDRANT_LEXICAL_INTEGRATION") != "1":
        pytest.skip("Opt in to native Qdrant tests and supply a prepared offline reranking model.")
    chunker = StructureAwareChunker(ChunkingConfig("fixture-embedding", 240, 0), CharacterCounter())
    store = QdrantBM25ChunkStore(
        VectorStoreCollectionConfig(
            "ce-hybrid-rerank-it-" + uuid4().hex,
            "fixture-embedding",
            2,
            index_version="m5-chunks-v1",
            index_configuration_id=indexing_configuration_id(
                chunker, embedding_identity="fixture-v1"
            ),
        ),
        url=os.getenv("CONTEXT_ENGINE_QDRANT_URL", "http://localhost:6333"),
    )
    try:
        coordinator = SourceIngestionCoordinator(
            chunker=chunker,
            embedding_provider=FixtureEmbeddingProvider(),
            vector_store=store,
            embedding_identity="fixture-v1",
        )
        ingested_ids: dict[str, tuple[str, ...]] = {}
        for identity, text in (
            ("mars", "Mars is known as the Red Planet."),
            ("venus", "Venus is Earth's twin and has a dense atmosphere."),
        ):
            outcome = coordinator.ingest(
                SourceInput(identity, identity + ".txt", text.encode(), SourceFormat.TEXT)
            )
            assert outcome.status == "created"
            ingested_ids[identity] = outcome.chunk_ids
        hybrid = HybridRetriever(
            dense_retriever=EmbeddingVectorStoreRetriever(
                embedding_provider=FixtureEmbeddingProvider(), vector_store=store
            ),
            lexical_retriever=LexicalRetriever(lexical_index=QdrantLexicalIndex(chunk_store=store)),
            config=HybridRetrieverConfig(final_result_count=20),
            visibility_reader=lifecycle_visibility_reader(store),
        )
        reranker = LocalCrossEncoderReranker(LocalCrossEncoderConfig(model_reference=reference))
        registry = ToolRegistry()
        registry.register(
            SearchDocumentsTool(
                RerankingRetriever(hybrid, reranker, config=RerankingRetrieverConfig(20, 5))
            )
        )
        invocation = ToolInvocation.from_mapping(
            tool_name="search_documents",
            arguments={"query": "Which planet is known as the Red Planet?"},
        )
        denied = ToolRuntime(
            registry, policy=ToolNamePolicy((), default_decision=ToolPolicyDecision.DENY)
        ).execute(invocation)
        assert denied.status is ToolResultStatus.ERROR
        response = ToolRuntime(registry).execute(invocation)
        assert response.status is ToolResultStatus.SUCCESS
        results = response.output_as_mapping()["results"]
        assert isinstance(results, list) and len(results) == 2
        first = results[0]
        assert isinstance(first, dict)
        assert first["metadata"]["source_id"] == "mars"
        assert first["metadata"]["content_sha256"]
        assert first["document_id"] in ingested_ids["mars"]
        stages = {stage["strategy"] for stage in first["diagnostics"]}
        assert {"hybrid", "upstream", "reranking"} <= stages
    finally:
        store._client.delete_collection(store.collection_config.collection_name)
