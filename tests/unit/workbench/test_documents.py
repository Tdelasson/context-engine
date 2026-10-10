import pytest

from context_engine.knowledge.processing import SourceFormat, SourceInput
from context_engine.retrieval import (
    EmbeddingVectorStoreRetriever,
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
from tests.source_index_fixtures import (
    FixtureEmbeddingProvider,
    MemorySourceStore,
    coordinator,
    fixture_chunker,
)


def _catalog(*, max_files: int = 5) -> tuple[DocumentCatalog, MemorySourceStore]:
    store = MemorySourceStore(fixture_chunker())
    catalog = DocumentCatalog(
        ingestion=coordinator(store),
        upload_limits=UploadLimits(max_files=max_files, max_bytes_per_file=64),
        preloaded_sources=(
            SourceInput("preloaded-demo", "demo.md", b"demo", SourceFormat.MARKDOWN, "preloaded"),
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
        (UploadCandidate(name="facts.docx", content=b"text"), "Only UTF-8"),
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
    first = catalog.prepare()
    catalog.prepare()
    assert len(store.upsert_batches) == 1
    assert set(store.records) == set(first.outcomes[0].chunk_ids)
    assert catalog.last_report.outcomes[0].status.value == "unchanged"


def test_clear_uploads_deletes_only_uploaded_sources_after_restart() -> None:
    catalog, store = _catalog()
    preloaded = catalog.prepare().outcomes[0].chunk_ids
    report = catalog.ingest_uploads((UploadCandidate(name="facts.txt", content=b"meeting fact"),))
    restarted = DocumentCatalog(ingestion=coordinator(store), preloaded_sources=())
    assert restarted.uploaded_sources[0].source_id == report.source_ids[0]
    assert restarted.clear_uploads() == report.source_ids
    assert set(store.records) == set(preloaded)
    assert catalog.uploaded_sources == ()


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
    revision = catalog.uploaded_sources[0].content_sha256
    second = catalog.ingest_uploads((UploadCandidate("facts.md", b"# Second"),))
    assert first.source_ids == second.source_ids
    assert len(catalog.uploaded_sources) == len(store.records) == 1
    document = store.records[second.outcomes[0].chunk_ids[0]].document
    assert document.content == "# Second"
    assert document.metadata_as_mapping()["content_sha256"] != revision
    assert catalog.clear_uploads() == first.source_ids
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
    assert catalog.uploaded_sources == ()


def test_processed_uploads_remain_searchable_through_tool_runtime() -> None:
    provider = FixtureEmbeddingProvider()
    store = MemorySourceStore(fixture_chunker())
    catalog = DocumentCatalog(ingestion=coordinator(store, provider), preloaded_sources=())
    text = "# Meeting\n\nAccess code: COBALT-742.\n"
    report = catalog.ingest_uploads((UploadCandidate("meeting.md", text.encode()),))
    registry = ToolRegistry()
    registry.register(
        SearchDocumentsTool(
            EmbeddingVectorStoreRetriever(embedding_provider=provider, vector_store=store)
        )
    )
    result = ToolRuntime(registry).execute(
        ToolInvocation.from_mapping(
            tool_name="search_documents", arguments={"query": "meeting access code"}
        )
    )
    assert result.status is ToolResultStatus.SUCCESS
    output = result.output_as_mapping()
    assert output["result_count"] == 1
    matches = output["results"]
    assert isinstance(matches, list)
    match = matches[0]
    assert isinstance(match, dict)
    assert match["document_id"] == report.outcomes[0].chunk_ids[0]
    assert match["content"] == text
    assert match["metadata"]["source_id"] == report.source_ids[0]
    assert match["metadata"]["spans"]


def test_pdf_uploads_keep_page_metadata_and_diagnostics_in_catalog() -> None:
    from tests.pdf_fixtures import make_pdf

    catalog, store = _catalog()
    report = catalog.ingest_uploads((UploadCandidate("facts.pdf", make_pdf(("Fact", None))),))
    document = store.records[report.outcomes[0].chunk_ids[0]].document
    assert document.metadata_as_mapping()["page_numbers"] == [1]
    assert len(catalog.upload_diagnostics) == 2
    assert catalog.upload_diagnostics[0][0] == "facts.pdf"
    catalog.ingest_uploads((UploadCandidate("facts.pdf", make_pdf(("Updated fact",))),))
    assert not catalog.upload_diagnostics
    catalog.clear_uploads()
    assert catalog.uploaded_sources == ()


def test_pdf_uploads_use_explicit_separate_limits() -> None:
    from tests.pdf_fixtures import make_pdf

    candidate = UploadCandidate("facts.pdf", make_pdf(("Fact", "Page two")))
    document = construct_uploaded_document(candidate, UploadLimits(max_bytes_per_file=1))
    assert "Page two" in document.content
    for limits, message in [
        (UploadLimits(max_pdf_bytes_per_file=1), "exceeds 1 bytes"),
        (UploadLimits(max_pdf_pages=1), "exceeds 1 pages"),
        (UploadLimits(max_pdf_text_characters=1), "exceeds 1 extracted"),
    ]:
        with pytest.raises(WorkbenchDocumentError, match=message):
            construct_uploaded_document(candidate, limits)


def test_source_batch_storage_failure_reports_committed_prefix_and_restart_rollback() -> None:
    from context_engine.retrieval.source_store import SourceIndexUnavailableError

    catalog, store = _catalog()
    store.fail_on["upsert"] = 2
    with pytest.raises(WorkbenchDocumentError, match="recover"):
        catalog.ingest_uploads(
            (UploadCandidate("one.txt", b"one"), UploadCandidate("two.txt", b"two"))
        )
    assert [outcome.status.value for outcome in catalog.last_report.outcomes] == [
        "created",
        "failed",
    ]
    with pytest.raises(SourceIndexUnavailableError):
        catalog.uploaded_sources
    catalog.prepare()
    assert [source.source_name for source in catalog.uploaded_sources] == ["one.txt"]
    assert catalog.recovery_outcomes[0].recovered


def test_individual_upload_deletion_preserves_other_source() -> None:
    catalog, store = _catalog()
    report = catalog.ingest_uploads(
        (UploadCandidate("one.txt", b"one"), UploadCandidate("two.txt", b"two"))
    )
    catalog.delete_upload(report.source_ids[0])
    assert [source.source_name for source in catalog.uploaded_sources] == ["two.txt"]
    assert catalog.last_report.outcomes[0].status.value == "deleted"
