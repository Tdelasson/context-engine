import os

import pytest

from context_engine.retrieval import (
    Document,
    LocalEmbeddingProvider,
    LocalEmbeddingProviderConfig,
    LocalEmbeddingProviderInitializationError,
)


def _skip_unless_local_embedding_enabled() -> None:
    if os.getenv("CONTEXT_ENGINE_RUN_LOCAL_EMBEDDING_INTEGRATION") != "1":
        pytest.skip(
            "Set CONTEXT_ENGINE_RUN_LOCAL_EMBEDDING_INTEGRATION=1 to run local embedding "
            "integration tests."
        )


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


def test_local_embedding_provider_with_real_model() -> None:
    _skip_unless_local_embedding_enabled()
    provider = _build_local_provider()
    documents = (
        Document.from_mapping(
            document_id="doc-1", content="Context Engine supports local inference."
        ),
        Document.from_mapping(document_id="doc-2", content="Embeddings power semantic retrieval."),
    )

    document_embeddings = provider.embed_documents(documents)
    query_embedding = provider.embed_query("How does Context Engine run embeddings locally?")

    assert len(document_embeddings) == 2
    assert document_embeddings[0].model_id == query_embedding.model_id
    assert document_embeddings[0].dimensions > 0
    assert document_embeddings[0].dimensions == document_embeddings[1].dimensions
    assert document_embeddings[0].dimensions == query_embedding.dimensions
