from __future__ import annotations

import json
from collections.abc import Sequence

from context_engine.agent import AgentRuntime, AgentRuntimeExecutionOutcome
from context_engine.models import (
    ModelFinishReason,
    ModelRequest,
    ModelResponse,
    ModelRole,
    ModelToolCall,
    ModelToolResultStatus,
)
from context_engine.retrieval import Document, RetrievalRequest, SearchResult
from context_engine.tools import (
    ToolPolicyDecision,
    ToolRegistry,
    ToolResultStatus,
    ToolRuntime,
)
from context_engine.tools.retrieval import SearchDocumentsTool, SearchDocumentsToolConfig


class _RecordingRetriever:
    def __init__(self, results: Sequence[SearchResult]) -> None:
        self._results = tuple(results)
        self.requests: list[RetrievalRequest] = []

    def retrieve(self, request: RetrievalRequest) -> Sequence[SearchResult]:
        self.requests.append(request)
        return self._results


class _SequenceGateway:
    def __init__(self, responses: Sequence[ModelResponse]) -> None:
        self._responses = list(responses)
        self.requests: list[ModelRequest] = []

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        return self._responses.pop(0)


def test_agent_runtime_can_search_documents_then_respond_with_tool_evidence() -> None:
    retriever = _RecordingRetriever(
        (
            SearchResult(
                document=Document.from_mapping(
                    document_id="adr-002",
                    content="Every tool call crosses registry, validation, policy, and approval.",
                    metadata={"title": "Tool Security Boundary"},
                ),
                score=0.95,
            ),
        )
    )
    registry = ToolRegistry()
    registry.register(
        SearchDocumentsTool(
            retriever,
            config=SearchDocumentsToolConfig(top_k=1, max_content_chars=200),
        )
    )
    gateway = _SequenceGateway(
        (
            ModelResponse(
                model_id="deterministic-model",
                output_text="",
                finish_reason=ModelFinishReason.STOP,
                tool_call=ModelToolCall.from_mapping(
                    tool_name="search_documents",
                    arguments={"query": "How are tool calls controlled?"},
                    tool_call_id="search-1",
                ),
            ),
            ModelResponse(
                model_id="deterministic-model",
                output_text=("Tool calls cross registry lookup, validation, policy, and approval."),
                finish_reason=ModelFinishReason.STOP,
            ),
        )
    )
    runtime = AgentRuntime(model_gateway=gateway, tool_runtime=ToolRuntime(registry))

    result = runtime.run(
        model_id="deterministic-model",
        user_prompt="How does Context Engine control tool calls?",
        max_model_iterations=3,
    )

    assert result.outcome is AgentRuntimeExecutionOutcome.RESPONDED
    assert result.proposed_response == (
        "Tool calls cross registry lookup, validation, policy, and approval."
    )
    assert retriever.requests == [RetrievalRequest(query="How are tool calls controlled?", top_k=1)]
    assert len(runtime.tool_results) == 1
    tool_result = runtime.tool_results[0]
    assert tool_result.status is ToolResultStatus.SUCCESS
    assert tool_result.invocation.invocation_id == "search-1"
    output = tool_result.output_as_mapping()
    assert output["result_count"] == 1
    json.dumps(output, allow_nan=False, sort_keys=True)

    assert len(runtime.tool_execution_traces) == 1
    trace = runtime.tool_execution_traces[0]
    assert trace.policy_decision is ToolPolicyDecision.ALLOW
    assert trace.status is ToolResultStatus.SUCCESS
    assert trace.output_as_mapping() == output

    assert len(gateway.requests) == 2
    first_request = gateway.requests[0]
    assert len(first_request.tools) == 1
    assert first_request.tools[0].name == "search_documents"
    assert first_request.tools[0].input_schema == {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
        "additionalProperties": False,
    }

    second_request = gateway.requests[1]
    assert [message.role for message in second_request.messages] == [
        ModelRole.USER,
        ModelRole.ASSISTANT,
        ModelRole.TOOL,
    ]
    assert second_request.messages[1].tool_call == ModelToolCall.from_mapping(
        tool_name="search_documents",
        arguments={"query": "How are tool calls controlled?"},
        tool_call_id="search-1",
    )
    model_tool_result = second_request.messages[2].tool_result
    assert model_tool_result is not None
    assert model_tool_result.status is ModelToolResultStatus.SUCCESS
    assert model_tool_result.tool_call_id == "search-1"
    assert model_tool_result.output_as_mapping() == output
