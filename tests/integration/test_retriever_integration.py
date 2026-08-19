from __future__ import annotations

import os
import uuid

import pytest

from context_engine.retrieval import (
    Document,
    EmbeddingVectorStoreRetriever,
    LocalEmbeddingProvider,
    LocalEmbeddingProviderConfig,
    LocalEmbeddingProviderInitializationError,
    MetadataFilter,
    RetrievalRequest,
    VectorDistanceMetric,
    VectorStoreCollectionConfig,
    VectorStoreConfigurationError,
    VectorStoreRecord,
)
from context_engine.retrieval.qdrant_vector_store import QdrantVectorStore


def _skip_unless_retriever_integration_enabled() -> None:
    if os.getenv("CONTEXT_ENGINE_RUN_RETRIEVER_INTEGRATION") != "1":
        pytest.skip("Set CONTEXT_ENGINE_RUN_RETRIEVER_INTEGRATION=1 to run retriever integration tests.")


def _build_local_provider() -> LocalEmbeddingProvider:
    model_reference = os.getenv("CONTEXT_ENGINE_EMBEDDING_MODEL")
    if not model_reference:
        pytest.skip("Set CONTEXT_ENGINE_EMBEDDING_MODEL to a locally available embedding model.")
    assert model_reference is not None

    model_id = os.getenv("CONTEXT_ENGINE_EMBEDDING_MODEL_ID", model_reference)
    batch_size = int(os.getenv("CONTEXT_ENGINE_EMBEDDING_BATCH_SIZE", "8"))
    normalize_embeddings = os.getenv("CONTEXT_ENGINE_EMBEDDING_NORMALIZE", "0") == "1"
    query_prefix = os.getenv("CONTEXT_ENGINE_EMBEDDING_QUERY_PREFIX", "")
    document_prefix = os.getenv("CONTEXT_ENGINE_EMBEDDING_DOCUMENT_PREFIX", "")

    try:
        return LocalEmbeddingProvider(
            LocalEmbeddingProviderConfig(
                model_id=model_id,
                model_reference=model_reference,
                batch_size=batch_size,
                normalize_embeddings=normalize_embeddings,
                query_prefix=query_prefix,
                document_prefix=document_prefix,
            )
        )
    except LocalEmbeddingProviderInitializationError as exc:
        pytest.skip(f"Local embedding model/runtime not available for integration test: {exc}")
    raise AssertionError("pytest.skip should have exited the test before reaching this point.")


def test_retriever_with_local_embedding_provider_and_qdrant() -> None:
    _skip_unless_retriever_integration_enabled()
    provider = _build_local_provider()

    documents = (
        Document.from_mapping(
            document_id="doc-1",
            content="Context Engine supports a context-aware DJ focused on music.",
            metadata={"topic": "music", "lang": "en"},
        ),
        Document.from_mapping(
            document_id="doc-2",
            content="The architecture separates embedding generation from vector search.",
            metadata={"topic": "architecture", "lang": "en"},
        ),
        Document.from_mapping(
            document_id="doc-3",
            content="Music retrieval pipelines can use metadata filters with vector search.",
            metadata={"topic": "music", "lang": "en"},
        ),
    )

    embeddings = provider.embed_documents(documents)
    assert embeddings, "Local provider should produce document embeddings."

    collection_name = f"context-engine-retriever-it-{uuid.uuid4().hex}"
    try:
        vector_store = QdrantVectorStore(
            VectorStoreCollectionConfig(
                collection_name=collection_name,
                embedding_model_id=embeddings[0].model_id,
                dimensions=embeddings[0].dimensions,
                distance_metric=VectorDistanceMetric.COSINE,
            ),
            url=os.getenv("CONTEXT_ENGINE_QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("CONTEXT_ENGINE_QDRANT_API_KEY"),
            timeout_seconds=float(os.getenv("CONTEXT_ENGINE_QDRANT_TIMEOUT_SECONDS", "5")),
        )
    except VectorStoreConfigurationError as exc:
        pytest.skip(f"Qdrant integration dependencies/runtime unavailable: {exc}")

    vector_store.upsert(
        tuple(
            VectorStoreRecord(document=document, embedding=embedding)
            for document, embedding in zip(documents, embeddings, strict=True)
        )
    )

    retriever = EmbeddingVectorStoreRetriever(
        embedding_provider=provider,
        vector_store=vector_store,
    )
    results = retriever.retrieve(
        RetrievalRequest(
            query="What does the project say about music retrieval?",
            top_k=2,
            metadata_filter=MetadataFilter.from_mapping({"topic": "music"}),
        )
    )

    assert results
    assert len(results) <= 2
    assert all(result.document.metadata_as_mapping().get("topic") == "music" for result in results)
