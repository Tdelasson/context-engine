from __future__ import annotations

import json
from collections.abc import Sequence

import pytest

from context_engine.retrieval import Document, RetrievalRequest, RetrieverError, SearchResult
from context_engine.tools import (
    Tool,
    ToolInputValidationError,
    ToolInvocation,
    ToolNamePolicy,
    ToolPolicyDecision,
    ToolRegistry,
    ToolResultStatus,
    ToolRuntime,
)
from context_engine.tools.retrieval import (
    SearchDocumentsTool,
    SearchDocumentsToolConfig,
    SearchDocumentsToolConfigurationError,
    SearchDocumentsToolInputError,
    SearchDocumentsToolOutputError,
)


class _RecordingRetriever:
    def __init__(
        self,
        results: Sequence[SearchResult] = (),
        *,
        error: Exception | None = None,
    ) -> None:
        self._results = tuple(results)
        self._error = error
        self.requests: list[RetrievalRequest] = []

    def retrieve(self, request: RetrievalRequest) -> Sequence[SearchResult]:
        self.requests.append(request)
        if self._error is not None:
            raise self._error
        return self._results


def _result(
    document_id: str,
    content: str,
    score: float,
    *,
    metadata: dict[str, object] | None = None,
) -> SearchResult:
    return SearchResult(
        document=Document.from_mapping(
            document_id=document_id,
            content=content,
            metadata=metadata,
        ),
        score=score,
    )


def _runtime_for(tool: SearchDocumentsTool, *, deny: bool = False) -> ToolRuntime:
    registry = ToolRegistry()
    registry.register(tool)
    policy = None
    if deny:
        policy = ToolNamePolicy.from_mapping({"search_documents": ToolPolicyDecision.DENY})
    return ToolRuntime(registry, policy=policy)


def test_search_documents_tool_satisfies_tool_protocol_and_declares_query_only() -> None:
    tool = SearchDocumentsTool(_RecordingRetriever())

    assert isinstance(tool, Tool)
    assert tool.name == "search_documents"
    assert tuple(field.name for field in tool.input_schema.fields) == ("query",)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("top_k", 0),
        ("top_k", -1),
        ("top_k", True),
        ("max_content_chars", 0),
        ("max_content_chars", -1),
        ("max_content_chars", False),
    ],
)
def test_search_documents_tool_config_rejects_invalid_limits(
    field_name: str, value: object
) -> None:
    arguments: dict[str, object] = {field_name: value}

    with pytest.raises(SearchDocumentsToolConfigurationError):
        SearchDocumentsToolConfig(**arguments)  # type: ignore[arg-type]


def test_search_documents_tool_retrieves_bounded_json_safe_results_in_order() -> None:
    retriever = _RecordingRetriever(
        (
            _result(
                "doc-b",
                "abcdefgh",
                0.91,
                metadata={
                    "title": "Second alphabet document",
                    "tags": ("demo", "retrieval"),
                    "properties": {"active": True, "revision": 2},
                },
            ),
            _result("doc-a", "short", 0.72, metadata={"title": "First ID"}),
            _result("doc-c", "excluded by runtime limit", 0.50),
        )
    )
    tool = SearchDocumentsTool(
        retriever,
        config=SearchDocumentsToolConfig(top_k=2, max_content_chars=5),
    )

    output = tool.execute(
        ToolInvocation.from_mapping(
            tool_name="search_documents",
            arguments={"query": "  runtime policy  "},
        )
    )

    assert retriever.requests == [RetrievalRequest(query="runtime policy", top_k=2)]
    assert output == {
        "query": "runtime policy",
        "result_count": 2,
        "results": [
            {
                "document_id": "doc-b",
                "score": 0.91,
                "content": "abcde",
                "content_truncated": True,
                "metadata": {
                    "properties": {"active": True, "revision": 2},
                    "tags": ["demo", "retrieval"],
                    "title": "Second alphabet document",
                },
            },
            {
                "document_id": "doc-a",
                "score": 0.72,
                "content": "short",
                "content_truncated": False,
                "metadata": {"title": "First ID"},
            },
        ],
    }
    json.dumps(output, allow_nan=False, sort_keys=True)


def test_search_documents_tool_returns_empty_results_deterministically() -> None:
    retriever = _RecordingRetriever()
    tool = SearchDocumentsTool(retriever)

    output = tool.execute(
        ToolInvocation.from_mapping(
            tool_name="search_documents",
            arguments={"query": "nothing matches"},
        )
    )

    assert output == {"query": "nothing matches", "result_count": 0, "results": []}


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"query": 42},
        {"query": "valid", "top_k": 100},
    ],
)
def test_tool_runtime_rejects_invalid_or_model_controlled_arguments_before_retrieval(
    arguments: dict[str, object],
) -> None:
    retriever = _RecordingRetriever()
    runtime = _runtime_for(SearchDocumentsTool(retriever))

    result = runtime.execute(
        ToolInvocation.from_mapping(tool_name="search_documents", arguments=arguments)
    )

    assert result.status is ToolResultStatus.ERROR
    assert result.error is not None
    assert result.error.error_type == ToolInputValidationError.__name__
    assert retriever.requests == []
    assert runtime.execution_traces[0].policy_decision is None


def test_search_documents_tool_rejects_whitespace_query_without_calling_retriever() -> None:
    retriever = _RecordingRetriever()
    runtime = _runtime_for(SearchDocumentsTool(retriever))

    result = runtime.execute(
        ToolInvocation.from_mapping(
            tool_name="search_documents",
            arguments={"query": "   "},
        )
    )

    assert result.status is ToolResultStatus.ERROR
    assert result.error is not None
    assert result.error.error_type == SearchDocumentsToolInputError.__name__
    assert retriever.requests == []
    assert runtime.execution_traces[0].policy_decision is ToolPolicyDecision.ALLOW


def test_tool_runtime_policy_denial_prevents_retrieval() -> None:
    retriever = _RecordingRetriever()
    runtime = _runtime_for(SearchDocumentsTool(retriever), deny=True)

    result = runtime.execute(
        ToolInvocation.from_mapping(
            tool_name="search_documents",
            arguments={"query": "policy boundary"},
        )
    )

    assert result.status is ToolResultStatus.ERROR
    assert retriever.requests == []
    assert runtime.execution_traces[0].policy_decision is ToolPolicyDecision.DENY


def test_retriever_failure_becomes_structured_runtime_error_and_trace() -> None:
    retriever = _RecordingRetriever(error=RetrieverError("retrieval unavailable"))
    runtime = _runtime_for(SearchDocumentsTool(retriever))

    result = runtime.execute(
        ToolInvocation.from_mapping(
            tool_name="search_documents",
            arguments={"query": "architecture"},
            invocation_id="search-call-1",
        )
    )

    assert result.status is ToolResultStatus.ERROR
    assert result.error is not None
    assert result.error.error_type == RetrieverError.__name__
    assert result.error.message == "retrieval unavailable"
    assert runtime.execution_traces[0].invocation.invocation_id == "search-call-1"
    assert runtime.execution_traces[0].policy_decision is ToolPolicyDecision.ALLOW
    assert runtime.execution_traces[0].error == result.error


@pytest.mark.parametrize(
    "result",
    [
        _result("bad-metadata", "content", 0.8, metadata={"unsupported": {"set"}}),
        _result("bad-score", "content", float("nan")),
    ],
)
def test_non_json_safe_search_result_becomes_structured_runtime_error(
    result: SearchResult,
) -> None:
    runtime = _runtime_for(SearchDocumentsTool(_RecordingRetriever((result,))))

    tool_result = runtime.execute(
        ToolInvocation.from_mapping(
            tool_name="search_documents",
            arguments={"query": "invalid output"},
        )
    )

    assert tool_result.status is ToolResultStatus.ERROR
    assert tool_result.error is not None
    assert tool_result.error.error_type == SearchDocumentsToolOutputError.__name__
    assert runtime.execution_traces[0].status is ToolResultStatus.ERROR
