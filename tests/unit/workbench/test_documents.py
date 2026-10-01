from collections.abc import Sequence

import pytest

from context_engine.retrieval import (
    Document,
    Embedding,
    Ingestor,
    MetadataFilter,
    SearchResult,
    VectorStore,
    VectorStoreRecord,
)
from context_engine.workbench.documents import (
    DocumentCatalog,
    UploadCandidate,
    UploadLimits,
    WorkbenchDocumentError,
    construct_uploaded_document,
    load_preloaded_documents,
)


class _EmbeddingProvider:
    model_id = "fake-embedding"
    dimensions = 2

    def embed_documents(self, documents: Sequence[Document]) -> Sequence[Embedding]:
        return tuple(
            Embedding.from_sequence(
                vector=(float(index), float(len(document.content))),
                model_id=self.model_id,
            )
            for index, document in enumerate(documents, start=1)
        )

    def embed_query(self, query: str) -> Embedding:
        return Embedding.from_sequence(vector=(float(len(query)), 1.0), model_id=self.model_id)


class _RecordingVectorStore(VectorStore):
    def __init__(self) -> None:
        self.records: dict[str, VectorStoreRecord] = {}
        self.upsert_batches: list[tuple[str, ...]] = []
        self.delete_calls: list[tuple[str, ...]] = []

    def upsert(self, records: Sequence[VectorStoreRecord]) -> None:
        self.upsert_batches.append(tuple(record.document.document_id for record in records))
        self.records.update({record.document.document_id: record for record in records})

    def search(
        self,
        query_embedding: Embedding,
        *,
        top_k: int = 5,
        metadata_filter: MetadataFilter | None = None,
    ) -> Sequence[SearchResult]:
        del query_embedding, top_k, metadata_filter
        return ()

    def delete(self, document_ids: Sequence[str]) -> None:
        normalized_ids = tuple(document_ids)
        self.delete_calls.append(normalized_ids)
        for document_id in normalized_ids:
            self.records.pop(document_id, None)


def _catalog(*, max_files: int = 5) -> tuple[DocumentCatalog, _RecordingVectorStore]:
    store = _RecordingVectorStore()
    catalog = DocumentCatalog(
        ingestor=Ingestor(embedding_provider=_EmbeddingProvider(), vector_store=store),
        vector_store=store,
        upload_limits=UploadLimits(max_files=max_files, max_bytes_per_file=64),
        preloaded_documents=(
            Document.from_mapping(
                document_id="preloaded-demo",
                content="demo",
                metadata={"source_kind": "preloaded", "source_name": "demo.md"},
            ),
        ),
    )
    return catalog, store


def test_preloaded_documents_have_clear_source_labels() -> None:
    documents = load_preloaded_documents()

    assert {document.metadata_as_mapping()["source_kind"] for document in documents} == {
        "preloaded"
    }
    assert {document.metadata_as_mapping()["source_name"] for document in documents} == {
        "architecture.md",
        "demo-guide.txt",
        "roadmap.md",
    }


def test_uploaded_document_is_deterministic_and_labeled() -> None:
    candidate = UploadCandidate(name="facts.md", content=b"A unique UTF-8 fact: \xc3\xb8resund")
    limits = UploadLimits(max_files=2, max_bytes_per_file=100)

    first = construct_uploaded_document(candidate, limits)
    second = construct_uploaded_document(candidate, limits)

    assert first == second
    assert first.document_id.startswith("uploaded-")
    assert first.content == "A unique UTF-8 fact: øresund"
    assert first.metadata_as_mapping() == {
        "source_kind": "uploaded",
        "source_name": "facts.md",
    }


@pytest.mark.parametrize(
    ("candidate", "message"),
    [
        (UploadCandidate(name="facts.pdf", content=b"text"), "Only UTF-8"),
        (UploadCandidate(name="../facts.md", content=b"text"), "must not contain a path"),
        (UploadCandidate(name="facts.md", content=b"\xff"), "valid UTF-8"),
        (UploadCandidate(name="facts.md", content=b"   "), "only whitespace"),
        (UploadCandidate(name="facts.md", content=b"x" * 65), "exceeds 64 bytes"),
    ],
)
def test_uploaded_document_validation_rejects_invalid_input(
    candidate: UploadCandidate, message: str
) -> None:
    with pytest.raises(WorkbenchDocumentError, match=message):
        construct_uploaded_document(
            candidate,
            UploadLimits(max_files=2, max_bytes_per_file=64),
        )


def test_prepare_is_idempotent() -> None:
    catalog, store = _catalog()

    catalog.prepare()
    catalog.prepare()

    assert store.upsert_batches == [("preloaded-demo",)]


def test_clear_uploads_deletes_only_uploaded_documents() -> None:
    catalog, store = _catalog()
    catalog.prepare()
    uploaded_ids = catalog.ingest_uploads(
        (UploadCandidate(name="facts.txt", content=b"meeting fact"),)
    ).document_ids

    cleared_ids = catalog.clear_uploads()

    assert cleared_ids == uploaded_ids
    assert store.delete_calls == [uploaded_ids]
    assert "preloaded-demo" in store.records
    assert catalog.uploaded_documents == ()


def test_upload_limit_is_checked_before_ingestion() -> None:
    catalog, store = _catalog(max_files=1)

    with pytest.raises(WorkbenchDocumentError, match="At most 1"):
        catalog.ingest_uploads(
            (
                UploadCandidate(name="one.txt", content=b"one"),
                UploadCandidate(name="two.txt", content=b"two"),
            )
        )

    assert store.upsert_batches == []
