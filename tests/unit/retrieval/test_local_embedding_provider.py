from collections.abc import Sequence

import pytest

from context_engine.retrieval import (
    Document,
    EmbeddingProvider,
    LocalEmbeddingProvider,
    LocalEmbeddingProviderConfig,
    LocalEmbeddingProviderConfigurationError,
    LocalEmbeddingProviderInferenceError,
    LocalEmbeddingProviderInitializationError,
)


class _FakeBackend:
    def __init__(self) -> None:
        self.model_id = "fake-local-embedding-model-v1"
        self.dimensions = 3
        self.embedded_documents: tuple[str, ...] = ()
        self.embedded_queries: tuple[str, ...] = ()

    def embed_documents(
        self,
        texts: Sequence[str],
        *,
        batch_size: int,
        normalize_embeddings: bool,
    ) -> tuple[tuple[float, ...], ...]:
        del batch_size, normalize_embeddings
        self.embedded_documents = tuple(texts)
        return tuple(
            (float(index), float(len(text)), 1.0) for index, text in enumerate(texts, start=1)
        )

    def embed_query(self, text: str, *, normalize_embeddings: bool) -> tuple[float, ...]:
        del normalize_embeddings
        self.embedded_queries = (text,)
        return (float(len(text)), 0.0, 1.0)


def _build_provider(
    backend: _FakeBackend | None = None,
    *,
    document_prefix: str = "",
    query_prefix: str = "",
) -> LocalEmbeddingProvider:
    active_backend = _FakeBackend() if backend is None else backend
    config = LocalEmbeddingProviderConfig(
        model_id=active_backend.model_id,
        model_reference="local/fake-model",
        document_prefix=document_prefix,
        query_prefix=query_prefix,
    )
    return LocalEmbeddingProvider(config, backend_factory=lambda _: active_backend)


def test_local_provider_satisfies_embedding_provider_protocol() -> None:
    provider = _build_provider()
    assert isinstance(provider, EmbeddingProvider)


def test_local_provider_embeds_documents_in_batch_with_metadata() -> None:
    backend = _FakeBackend()
    provider = _build_provider(backend, document_prefix="doc: ")
    documents = (
        Document.from_mapping(document_id="doc-1", content="alpha"),
        Document.from_mapping(document_id="doc-2", content="beta"),
    )

    embeddings = provider.embed_documents(documents)

    assert backend.embedded_documents == ("doc: alpha", "doc: beta")
    assert len(embeddings) == 2
    assert embeddings[0].model_id == backend.model_id
    assert embeddings[0].dimensions == backend.dimensions
    assert embeddings[1].model_id == backend.model_id
    assert embeddings[1].dimensions == backend.dimensions


def test_local_provider_embeds_query_with_query_prefix() -> None:
    backend = _FakeBackend()
    provider = _build_provider(backend, query_prefix="query: ")

    embedding = provider.embed_query("find context")

    assert backend.embedded_queries == ("query: find context",)
    assert embedding.model_id == backend.model_id
    assert embedding.dimensions == backend.dimensions
    assert embedding.vector == (19.0, 0.0, 1.0)


def test_local_provider_rejects_empty_query() -> None:
    provider = _build_provider()
    with pytest.raises(
        LocalEmbeddingProviderConfigurationError,
        match="query must be a non-empty string",
    ):
        provider.embed_query("")


def test_local_provider_rejects_dimension_mismatch() -> None:
    class _WrongDimensionBackend(_FakeBackend):
        def embed_query(self, text: str, *, normalize_embeddings: bool) -> tuple[float, ...]:
            del text, normalize_embeddings
            return (1.0, 2.0)

    provider = _build_provider(_WrongDimensionBackend())
    with pytest.raises(LocalEmbeddingProviderInferenceError, match="invalid embedding vector"):
        provider.embed_query("query")


def test_local_provider_rejects_document_vector_count_mismatch() -> None:
    class _TooFewVectorsBackend(_FakeBackend):
        def embed_documents(
            self,
            texts: Sequence[str],
            *,
            batch_size: int,
            normalize_embeddings: bool,
        ) -> tuple[tuple[float, ...], ...]:
            del texts, batch_size, normalize_embeddings
            return ((1.0, 2.0, 3.0),)

    provider = _build_provider(_TooFewVectorsBackend())
    documents = (
        Document.from_mapping(document_id="doc-1", content="alpha"),
        Document.from_mapping(document_id="doc-2", content="beta"),
    )
    with pytest.raises(
        LocalEmbeddingProviderInferenceError,
        match="different number of vectors than documents",
    ):
        provider.embed_documents(documents)


def test_local_provider_surfaces_backend_initialization_errors() -> None:
    config = LocalEmbeddingProviderConfig(model_id="model", model_reference="model/path")

    def _failing_factory(_: LocalEmbeddingProviderConfig) -> _FakeBackend:
        raise RuntimeError("backend unavailable")

    with pytest.raises(LocalEmbeddingProviderInitializationError, match="Failed to initialize"):
        LocalEmbeddingProvider(config, backend_factory=_failing_factory)
