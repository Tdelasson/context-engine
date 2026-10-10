"""Deterministic processing/chunking/embedding/search composition without live services."""

import json
from collections.abc import Sequence

import pytest

from context_engine.agent import AgentRuntime, AgentRuntimeExecutionOutcome
from context_engine.knowledge.chunking import ChunkingConfig, StructureAwareChunker
from context_engine.knowledge.processing import (
    DiagnosticCode,
    SourceFormat,
    SourceInput,
    process_source,
)
from context_engine.knowledge.token_counting import TokenizerTokenCounter
from context_engine.models import ModelFinishReason, ModelRequest, ModelResponse, ModelToolCall
from context_engine.retrieval import (
    Document,
    Embedding,
    EmbeddingVectorStoreRetriever,
    Ingestor,
    LocalEmbeddingProvider,
    LocalEmbeddingProviderConfig,
    MetadataFilter,
    SearchResult,
    VectorStoreRecord,
)
from context_engine.tools import (
    ToolInvocation,
    ToolNamePolicy,
    ToolPolicyDecision,
    ToolRegistry,
    ToolResultStatus,
    ToolRuntime,
)
from context_engine.tools.retrieval import SearchDocumentsTool, SearchDocumentsToolConfig


class _CharacterTokenizer:
    """Controlled fixture: each Unicode character is one token, plus two specials."""

    def encode(
        self,
        text: str,
        *,
        add_special_tokens: bool,
        truncation: bool,
        padding: bool,
    ) -> Sequence[int]:
        assert not truncation and not padding
        return tuple(ord(character) for character in text) + ((0, 0) if add_special_tokens else ())


class _BoundedEmbeddingBackend:
    model_id = "fixture-embedding"
    dimensions = 2
    model_parameter_bytes = None

    def __init__(self, tokenizer: _CharacterTokenizer, limit: int) -> None:
        self.tokenizer = tokenizer
        self.limit = limit
        self.document_inputs: list[str] = []

    def embed_documents(
        self,
        texts: Sequence[str],
        *,
        batch_size: int,
        normalize_embeddings: bool,
    ) -> Sequence[Sequence[float]]:
        self.document_inputs.extend(texts)
        for text in texts:
            assert (
                len(
                    self.tokenizer.encode(
                        text.strip(),
                        add_special_tokens=True,
                        truncation=False,
                        padding=False,
                    )
                )
                <= self.limit
            )
        return tuple((1.0, 0.0) if "COBALT-742" in text else (0.0, 1.0) for text in texts)

    def embed_query(self, text: str, *, normalize_embeddings: bool) -> Sequence[float]:
        return (1.0, 0.0)


class _MemoryStore:
    def __init__(self) -> None:
        self.records: dict[str, VectorStoreRecord] = {}
        self.search_calls = 0

    def upsert(self, records: Sequence[VectorStoreRecord]) -> None:
        self.records.update((record.document.document_id, record) for record in records)

    def search(
        self,
        query_embedding: Embedding,
        *,
        top_k: int = 5,
        metadata_filter: MetadataFilter | None = None,
    ) -> Sequence[SearchResult]:
        self.search_calls += 1
        results = [
            SearchResult(
                record.document,
                sum(
                    left * right
                    for left, right in zip(query_embedding.vector, record.embedding.vector)
                ),
            )
            for record in self.records.values()
            if metadata_filter is None
            or all(
                record.document.metadata_as_mapping().get(key) == value
                for key, value in metadata_filter.equals
            )
        ]
        return tuple(
            sorted(results, key=lambda result: (-result.score, result.document.document_id))[:top_k]
        )

    def delete(self, document_ids: Sequence[str]) -> None:
        for document_id in document_ids:
            self.records.pop(document_id, None)


class _EvidenceGateway:
    """Propose search, then require the structured tool evidence before answering."""

    def __init__(self) -> None:
        self.requests: list[ModelRequest] = []

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        if len(self.requests) == 1:
            return ModelResponse(
                "fixture-chat",
                "",
                ModelFinishReason.STOP,
                tool_call=ModelToolCall.from_mapping(
                    "search_documents",
                    {"query": "meeting access code"},
                    tool_call_id="search-1",
                ),
            )
        evidence = request.messages[-1].tool_result
        assert evidence is not None
        output = evidence.output_as_mapping()
        matches = output["results"]
        assert isinstance(matches, list) and matches
        assert "COBALT-742" in matches[0]["content"]
        return ModelResponse(
            "fixture-chat", "The access code is COBALT-742.", ModelFinishReason.STOP
        )


def _source(format: SourceFormat) -> SourceInput:
    if format is SourceFormat.PDF:
        pytest.importorskip("pypdf")
        from tests.pdf_fixtures import make_pdf

        content = make_pdf(
            (
                "Background: read the meeting guide.",
                None,
                "Access code is COBALT-742. Meeting starts at noon.",
            )
        )
        return SourceInput("meeting-source", "meeting.pdf", content, format, "uploaded")
    text = (
        "# Meeting ø 🐍\n\n"
        + "Read the meeting guide. " * 6
        + "\n\n## Access\n\nAccess code is COBALT-742. Meeting starts at noon.\n"
    )
    return SourceInput("meeting-source", "meeting.md", text.encode(), format, "uploaded")


def _pipeline(format: SourceFormat) -> tuple[_MemoryStore, ToolRegistry, tuple[Document, ...]]:
    processed = process_source(_source(format))
    tokenizer = _CharacterTokenizer()
    prefix = "passage: "
    config = ChunkingConfig(
        model_id="fixture-embedding",
        max_input_tokens=96,
        overlap_tokens=8,
        document_prefix=prefix,
    )
    counter = TokenizerTokenCounter(
        tokenizer,
        model_id=config.model_id,
        tokenizer_id="unicode-fixture-v1",
        max_input_tokens=96,
    )
    chunker = StructureAwareChunker(config, counter)
    chunks = chunker.chunk(processed)
    assert chunks == chunker.chunk(processed)
    assert len(chunks) > 1
    end = 0
    recovered = []
    for chunk in chunks:
        assert chunk.start_offset <= end < chunk.end_offset
        assert chunk.source_text == processed.text[chunk.start_offset : chunk.end_offset]
        recovered.append(processed.text[end : chunk.end_offset])
        assert chunk.token_count == counter.count_tokens(prefix + chunk.content)
        assert chunk.token_count <= 96
        assert all(
            processed.text[span.location.start_offset : span.location.end_offset]
            == processed.blocks[span.block_index].text[
                span.location.start_offset
                - processed.blocks[
                    span.block_index
                ].location.start_offset : span.location.end_offset
                - processed.blocks[span.block_index].location.start_offset
            ]
            for span in chunk.spans
        )
        end = chunk.end_offset
    assert "".join(recovered) == processed.text
    if format is SourceFormat.PDF:
        assert {page for chunk in chunks for page in chunk.page_numbers} == {1, 3}
        assert any(item.code is DiagnosticCode.PARTIAL_EXTRACTION for item in processed.diagnostics)
    documents = tuple(chunk.to_document() for chunk in chunks)
    backend = _BoundedEmbeddingBackend(tokenizer, 96)
    provider = LocalEmbeddingProvider(
        LocalEmbeddingProviderConfig(
            model_id=config.model_id,
            model_reference="controlled-fixture",
            document_prefix=prefix,
        ),
        backend_factory=lambda _: backend,
    )
    store = _MemoryStore()
    Ingestor(provider, store).ingest_documents(documents)
    assert backend.document_inputs == [prefix + document.content for document in documents]
    assert set(store.records) == {chunk.chunk_id for chunk in chunks}
    registry = ToolRegistry()
    registry.register(
        SearchDocumentsTool(
            EmbeddingVectorStoreRetriever(embedding_provider=provider, vector_store=store),
            config=SearchDocumentsToolConfig(top_k=1, max_content_chars=500),
        )
    )
    return store, registry, documents


@pytest.mark.parametrize("format", [SourceFormat.MARKDOWN, SourceFormat.PDF])
def test_processing_to_chunk_embedding_and_agent_search_preserves_evidence(
    format: SourceFormat,
) -> None:
    store, registry, documents = _pipeline(format)
    gateway = _EvidenceGateway()
    runtime = AgentRuntime(model_gateway=gateway, tool_runtime=ToolRuntime(registry))
    result = runtime.run(model_id="fixture-chat", user_prompt="What is the meeting access code?")
    assert result.outcome is AgentRuntimeExecutionOutcome.RESPONDED
    assert result.proposed_response == "The access code is COBALT-742."
    assert store.search_calls == 1
    assert runtime.tool_results[0].status is ToolResultStatus.SUCCESS
    assert runtime.tool_execution_traces[0].policy_decision is ToolPolicyDecision.ALLOW
    output = runtime.tool_results[0].output_as_mapping()
    json.dumps(output, allow_nan=False)
    matches = output["results"]
    assert isinstance(matches, list)
    match = matches[0]
    document = next(
        document for document in documents if document.document_id == match["document_id"]
    )
    assert match["metadata"] == document.metadata_as_mapping()
    assert match["metadata"]["source_id"] == "meeting-source"
    if format is SourceFormat.PDF:
        assert 3 in match["metadata"]["page_numbers"]
        assert any(
            diagnostic["code"] == DiagnosticCode.PARTIAL_EXTRACTION.value
            for diagnostic in match["metadata"]["processing_diagnostics"]
        )


def test_chunk_search_still_respects_tool_policy() -> None:
    store, registry, _ = _pipeline(SourceFormat.MARKDOWN)
    runtime = ToolRuntime(
        registry,
        policy=ToolNamePolicy.from_mapping(
            {
                "search_documents": ToolPolicyDecision.DENY,
            }
        ),
    )
    result = runtime.execute(
        ToolInvocation.from_mapping(
            "search_documents",
            {"query": "meeting access code"},
        )
    )
    assert result.status is not ToolResultStatus.SUCCESS
    assert store.search_calls == 0
