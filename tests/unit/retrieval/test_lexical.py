"""Deterministic lexical capability contracts, independent of storage and models."""

from dataclasses import replace
from typing import Any, cast

import pytest

from context_engine.retrieval.embeddings import Document
from context_engine.retrieval.lexical import (
    LexicalConfigurationError,
    LexicalIndexConfig,
    LexicalIndexError,
    LexicalRetriever,
)
from context_engine.retrieval.retriever import RetrievalRequest
from context_engine.retrieval.vector_store import MetadataFilter, SearchResult
from context_engine.tools import ToolInvocation
from context_engine.tools.retrieval.tool import SearchDocumentsTool


class FakeIndex:
    config = LexicalIndexConfig()

    def __init__(self, results: tuple[SearchResult, ...] = ()) -> None:
        self.results = results
        self.requests: list[RetrievalRequest] = []

    def search(self, request: RetrievalRequest) -> tuple[SearchResult, ...]:
        self.requests.append(request)
        return self.results

    def upsert(self, documents: Any) -> None:
        pass

    def delete(self, document_ids: Any) -> None:
        pass


def result(identity: str = "a", score: float = 1.0) -> SearchResult:
    return SearchResult(
        Document.from_mapping(
            document_id=identity,
            content="search_documents",
            metadata={"source_id": "s", "topic": "tools"},
        ),
        score,
    )


def test_fake_substitution_filters_provenance_diagnostics_and_ties() -> None:
    index = FakeIndex((result("z"), result("a")))
    request = RetrievalRequest(
        "SEARCH_documents", 2, MetadataFilter.from_mapping({"topic": "tools"})
    )
    results = LexicalRetriever(lexical_index=index).retrieve(request)
    assert index.requests == [request]
    assert [r.document.document_id for r in results] == ["a", "z"]
    assert results[0].document == result().document
    assert results[0].diagnostics[0].score_kind == "bm25"
    assert results[1].diagnostics[0].rank == 2


@pytest.mark.parametrize("score", [float("nan"), float("inf"), -1, True, "wrong"])
def test_invalid_scores_rejected(score: Any) -> None:
    with pytest.raises(LexicalIndexError):
        LexicalRetriever(lexical_index=FakeIndex((result(score=score),))).retrieve(
            RetrievalRequest("q")
        )


@pytest.mark.parametrize(
    "results", [(result(), result()), (None,), (SearchResult(Document("a", ""), 1),)]
)
def test_invalid_duplicate_records_rejected(results: Any) -> None:
    with pytest.raises(LexicalIndexError):
        LexicalRetriever(lexical_index=FakeIndex(results)).retrieve(RetrievalRequest("q"))


@pytest.mark.parametrize("query", [" ", "\n\t"])
def test_blank_queries_rejected(query: str) -> None:
    with pytest.raises(LexicalConfigurationError):
        LexicalRetriever(lexical_index=FakeIndex()).retrieve(RetrievalRequest(query))


@pytest.mark.parametrize(
    "metadata_filter",
    [
        MetadataFilter((("topic", float("nan")),)),
        MetadataFilter((("", "v"),)),
        MetadataFilter((("x", "a"), ("x", "b"))),
        "invalid",
    ],
)
def test_invalid_filters_rejected(metadata_filter: Any) -> None:
    with pytest.raises(LexicalConfigurationError):
        LexicalRetriever(lexical_index=FakeIndex()).retrieve(
            RetrievalRequest("q", metadata_filter=metadata_filter)
        )


def test_backend_filter_violation_rejected() -> None:
    with pytest.raises(LexicalIndexError):
        LexicalRetriever(lexical_index=FakeIndex((result(),))).retrieve(
            RetrievalRequest("q", metadata_filter=MetadataFilter.from_mapping({"topic": "other"}))
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"k": 0},
        {"k": True},
        {"b": 2},
        {"language": "danish"},
        {"average_document_length": float("inf")},
    ],
)
def test_invalid_configuration(changes: dict[str, Any]) -> None:
    with pytest.raises(LexicalConfigurationError):
        replace(LexicalIndexConfig(), **changes)


def test_effective_configuration_changes_identity() -> None:
    assert (
        replace(LexicalIndexConfig(), k=2).configuration_id != LexicalIndexConfig().configuration_id
    )


def test_lexical_search_tool_boundary() -> None:
    tool = SearchDocumentsTool(LexicalRetriever(lexical_index=FakeIndex((result(),))))
    output = tool.execute(
        ToolInvocation.from_mapping(
            tool_name="search_documents", arguments={"query": "search_documents"}
        )
    )
    rows = cast(list[dict[str, Any]], output["results"])
    assert rows[0]["document_id"] == "a"
    assert rows[0]["diagnostics"][0]["score_kind"] == "bm25"


def test_lexical_tool_registry_schema_and_policy_are_enforced() -> None:
    from context_engine.tools import (
        ToolPolicyDecision,
        ToolPolicyEvaluation,
        ToolRegistry,
        ToolResultStatus,
        ToolRuntime,
    )

    class DenySearch:
        def evaluate(self, invocation: ToolInvocation) -> ToolPolicyEvaluation:
            return ToolPolicyEvaluation(decision=ToolPolicyDecision.DENY)

    index = FakeIndex((result(),))
    registry = ToolRegistry()
    registry.register(SearchDocumentsTool(LexicalRetriever(lexical_index=index)))
    runtime = ToolRuntime(registry, policy=DenySearch())
    response = runtime.execute(
        ToolInvocation.from_mapping(tool_name="search_documents", arguments={"query": "q"})
    )
    assert response.status is ToolResultStatus.ERROR
    assert not index.requests
