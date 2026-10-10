from collections.abc import Sequence

import pytest

from context_engine.retrieval import (
    Document,
    Embedding,
    EmbeddingVectorStoreRetriever,
    Ingestor,
    MetadataFilter,
    SearchResult,
    VectorStore,
    VectorStoreRecord,
)
from context_engine.tools import ToolInvocation, ToolRegistry, ToolResultStatus, ToolRuntime
from context_engine.tools.retrieval import SearchDocumentsTool
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
    metadata = first.metadata_as_mapping()
    assert metadata["source_kind"] == "uploaded"
    assert metadata["source_name"] == "facts.md"
    assert metadata["source_id"] == first.document_id
    assert len(str(metadata["content_sha256"])) == 64


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


def test_upload_revision_replaces_same_source_without_consuming_count_limit() -> None:
    catalog, store = _catalog(max_files=1)
    first = catalog.ingest_uploads((UploadCandidate("facts.md", b"# First"),))
    revision = catalog.uploaded_documents[0].metadata_as_mapping()["content_sha256"]
    second = catalog.ingest_uploads((UploadCandidate("facts.md", b"# Second"),))
    assert first.document_ids == second.document_ids
    assert len(catalog.uploaded_documents) == len(store.records) == 1
    document = store.records[first.document_ids[0]].document
    assert document.content == "# Second"
    assert document.metadata_as_mapping()["content_sha256"] != revision
    assert catalog.clear_uploads() == first.document_ids
    assert store.records == {}


def test_upload_bom_is_removed_by_core_processing() -> None:
    document = construct_uploaded_document(
        UploadCandidate("facts.TXT", b"\xef\xbb\xbfUnicode: \xc3\xb8"), UploadLimits()
    )
    assert document.content == "Unicode: ø"
    assert document.metadata_as_mapping()["source_format"] == "text"


def test_invalid_upload_batch_does_not_ingest_valid_prefix() -> None:
    catalog, store = _catalog()
    with pytest.raises(WorkbenchDocumentError) as exc:
        catalog.ingest_uploads(
            (UploadCandidate("valid.txt", b"valid"), UploadCandidate("bad.txt", b"\xff"))
        )
    assert isinstance(exc.value.__cause__, ValueError)
    assert store.upsert_batches == []
    assert catalog.uploaded_documents == ()


def test_processed_uploads_remain_searchable_through_tool_runtime() -> None:
    class SearchableStore(_RecordingVectorStore):
        def search(
            self,
            query_embedding: Embedding,
            *,
            top_k: int = 5,
            metadata_filter: MetadataFilter | None = None,
        ) -> Sequence[SearchResult]:
            return tuple(SearchResult(record.document, 1.0) for record in self.records.values())[
                :top_k
            ]

    provider = _EmbeddingProvider()
    store = SearchableStore()
    catalog = DocumentCatalog(
        ingestor=Ingestor(provider, store),
        vector_store=store,
    )
    text = "# Meeting\n\nAccess code: COBALT-742.\n"
    report = catalog.ingest_uploads((UploadCandidate("meeting.md", text.encode()),))
    registry = ToolRegistry()
    registry.register(
        SearchDocumentsTool(
            EmbeddingVectorStoreRetriever(
                embedding_provider=provider,
                vector_store=store,
            )
        )
    )
    runtime = ToolRuntime(registry)
    result = runtime.execute(
        ToolInvocation.from_mapping(
            tool_name="search_documents",
            arguments={"query": "meeting access code"},
        )
    )
    assert result.status is ToolResultStatus.SUCCESS
    output = result.output_as_mapping()
    assert output["result_count"] == 1
    matches = output["results"]
    assert isinstance(matches, list)
    match = matches[0]
    assert isinstance(match, dict)
    assert match["document_id"] == report.document_ids[0]
    assert match["content"] == text
    assert match["metadata"] == catalog.uploaded_documents[0].metadata_as_mapping()
