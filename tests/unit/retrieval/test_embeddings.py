import pytest

from context_engine.retrieval import Document, Embedding, EmbeddingProvider


class _FakeEmbeddingProvider:
    def __init__(self) -> None:
        self.model_id = "fake-embedding-model-v1"
        self.dimensions = 3

    def embed_documents(self, documents: tuple[Document, ...]) -> tuple[Embedding, ...]:
        return tuple(
            Embedding.from_sequence(
                vector=(float(index), float(len(document.content)), 1.0),
                model_id=self.model_id,
                dimensions=self.dimensions,
            )
            for index, document in enumerate(documents, start=1)
        )

    def embed_query(self, query: str) -> Embedding:
        return Embedding.from_sequence(
            vector=(float(len(query)), 0.0, 1.0),
            model_id=self.model_id,
            dimensions=self.dimensions,
        )


def test_document_creation_preserves_stable_id_content_and_metadata() -> None:
    document = Document.from_mapping(
        document_id="doc-123",
        content="Context Engine",
        metadata={"source": "notes", "priority": 2},
    )

    assert document.document_id == "doc-123"
    assert document.content == "Context Engine"
    assert document.metadata_as_mapping() == {"source": "notes", "priority": 2}
    assert isinstance(document.metadata, tuple)


def test_document_rejects_empty_document_id() -> None:
    with pytest.raises(ValueError, match="document_id must be a non-empty string."):
        Document.from_mapping(document_id="", content="content")


def test_embedding_creation_preserves_model_identity_and_dimensions() -> None:
    embedding = Embedding.from_sequence(
        vector=(0.1, 0.2, 0.3),
        model_id="mock-model",
        dimensions=3,
    )

    assert embedding.vector == (0.1, 0.2, 0.3)
    assert embedding.model_id == "mock-model"
    assert embedding.dimensions == 3


def test_embedding_rejects_dimensionality_mismatch_deterministically() -> None:
    with pytest.raises(ValueError, match="Embedding dimensionality mismatch"):
        Embedding.from_sequence(vector=(0.1, 0.2), model_id="mock-model", dimensions=3)


def test_embedding_rejects_non_finite_values() -> None:
    with pytest.raises(ValueError, match="Embedding vector values must be finite numbers."):
        Embedding.from_sequence(vector=(0.1, float("inf"), 0.3), model_id="mock-model", dimensions=3)


def test_fake_provider_satisfies_embedding_provider_contract_for_batch_documents() -> None:
    provider = _FakeEmbeddingProvider()
    documents = (
        Document.from_mapping(document_id="doc-a", content="alpha"),
        Document.from_mapping(document_id="doc-b", content="beta"),
    )

    assert isinstance(provider, EmbeddingProvider)
    embeddings = provider.embed_documents(documents)

    assert len(embeddings) == 2
    assert embeddings[0].model_id == "fake-embedding-model-v1"
    assert embeddings[1].model_id == "fake-embedding-model-v1"
    assert embeddings[0].dimensions == 3
    assert embeddings[1].dimensions == 3


def test_fake_provider_satisfies_embedding_provider_contract_for_single_query() -> None:
    provider = _FakeEmbeddingProvider()

    embedding = provider.embed_query("find context")

    assert embedding.model_id == "fake-embedding-model-v1"
    assert embedding.dimensions == 3
    assert embedding.vector == (12.0, 0.0, 1.0)
