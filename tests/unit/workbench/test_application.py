from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from context_engine.models import (
    ModelFinishReason,
    ModelGatewayExecutionError,
    ModelRequest,
    ModelResponse,
    ModelToolCall,
)
from context_engine.retrieval import (
    Document,
    Embedding,
    Ingestor,
    MetadataFilter,
    SearchResult,
    VectorStore,
    VectorStoreRecord,
)
from context_engine.tools import (
    ToolInputField,
    ToolInputSchema,
    ToolInvocation,
    ToolRegistry,
)
from context_engine.tools.calculator.tool import Calculator
from context_engine.workbench.application import (
    PROMPT_PRESETS,
    WorkbenchApplication,
)
from context_engine.workbench.config import WorkbenchSettings
from context_engine.workbench.documents import DocumentCatalog
from context_engine.workbench.presentation import WorkbenchRunStatus


class _Gateway:
    def __init__(self, responses: Sequence[ModelResponse]) -> None:
        self._responses = list(responses)
        self.requests: list[ModelRequest] = []

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        return self._responses.pop(0)


class _FailingGateway:
    def generate(self, request: ModelRequest) -> ModelResponse:
        del request
        raise ModelGatewayExecutionError("local Ollama timed out")


class _MalformedProposalGateway:
    def generate(self, request: ModelRequest) -> ModelResponse:
        del request
        return ModelResponse(
            model_id="fake-model",
            output_text="malformed",
            finish_reason=cast(ModelFinishReason, "malformed"),
        )


class _NoOpEmbeddingProvider:
    model_id = "fake"
    dimensions = 2

    def embed_documents(self, documents: Sequence[Document]) -> Sequence[Embedding]:
        return tuple(
            Embedding.from_sequence(vector=(1.0, 0.0), model_id=self.model_id) for _ in documents
        )

    def embed_query(self, query: str) -> Embedding:
        del query
        return Embedding.from_sequence(vector=(1.0, 0.0), model_id=self.model_id)


class _NoOpVectorStore(VectorStore):
    def upsert(self, records: Sequence[VectorStoreRecord]) -> None:
        del records

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
        del document_ids


class _SearchFixtureTool:
    name = "search_documents"
    description = "Search deterministic fixture documents."
    input_schema = ToolInputSchema(fields=(ToolInputField(name="query", value_type=str),))

    def execute(self, invocation: ToolInvocation) -> Mapping[str, object]:
        return {
            "query": invocation.arguments_as_mapping()["query"],
            "result_count": 1,
            "results": [
                {
                    "document_id": "uploaded-fact",
                    "score": 0.91,
                    "content": "The bridge opened in 2000.",
                    "content_truncated": False,
                    "metadata": {
                        "source_kind": "uploaded",
                        "source_name": "facts.md",
                    },
                }
            ],
        }


class _FailingSearchTool(_SearchFixtureTool):
    def execute(self, invocation: ToolInvocation) -> Mapping[str, object]:
        del invocation
        raise RuntimeError("retrieval backend unavailable")


def _application(*, gateway: object, search_tool: object | None = None) -> WorkbenchApplication:
    store = _NoOpVectorStore()
    registry = ToolRegistry()
    registry.register(Calculator())
    if search_tool is not None:
        registry.register(search_tool)  # type: ignore[arg-type]
    return WorkbenchApplication(
        settings=WorkbenchSettings(),
        document_catalog=DocumentCatalog(
            ingestor=Ingestor(
                embedding_provider=_NoOpEmbeddingProvider(),
                vector_store=store,
            ),
            vector_store=store,
            preloaded_documents=(Document(document_id="preloaded", content="demo"),),
        ),
        model_gateway=gateway,  # type: ignore[arg-type]
        tool_registry=registry,
    )


def _tool_call_response(tool_name: str, arguments: Mapping[str, object]) -> ModelResponse:
    return ModelResponse(
        model_id="fake-model",
        output_text="",
        finish_reason=ModelFinishReason.STOP,
        tool_call=ModelToolCall.from_mapping(tool_name, arguments),
    )


def _final_response(text: str) -> ModelResponse:
    return ModelResponse(
        model_id="fake-model",
        output_text=text,
        finish_reason=ModelFinishReason.STOP,
    )


def test_search_run_exposes_full_lifecycle_evidence_and_trace() -> None:
    gateway = _Gateway(
        (
            _tool_call_response("search_documents", {"query": "bridge"}),
            _final_response("The uploaded evidence says the bridge opened in 2000."),
        )
    )
    application = _application(gateway=gateway, search_tool=_SearchFixtureTool())

    view = application.run_prompt("When did the bridge open?")

    assert view.status is WorkbenchRunStatus.FAILED
    assert view.error_phase == "tool_execution"
    assert view.final_response == "The uploaded evidence says the bridge opened in 2000."
    assert [step.name for step in view.lifecycle] == [
        "User prompt",
        "Model tool proposal",
        "Registry + schema validation",
        "Policy decision",
        "Tool execution",
        "Structured ToolResult",
        "Final model response",
    ]
    assert view.evidence[0].document_id == "uploaded-fact"
    assert view.evidence[0].score == 0.91
    assert view.evidence[0].source_kind == "uploaded"
    assert view.evidence[0].source_name == "facts.md"
    assert view.traces[0].tool_name == "search_documents"
    assert view.traces[0].policy == "allow"
    assert view.traces[0].status == "success"


def test_calculator_uses_the_same_runtime_boundary() -> None:
    gateway = _Gateway(
        (
            _tool_call_response("calculator", {"expression": "(144 / 12) + 7"}),
            _final_response("The result is 19."),
        )
    )
    application = _application(gateway=gateway)

    view = application.run_prompt(PROMPT_PRESETS["Calculator"])

    assert view.status is WorkbenchRunStatus.SUCCESS
    assert view.tool_results[0].output_as_mapping() == {"value": 19.0}
    assert view.traces[0].tool_name == "calculator"


def test_preset_and_free_form_prompts_share_the_same_execution_path() -> None:
    gateway = _Gateway((_final_response("preset"), _final_response("free form")))
    application = _application(gateway=gateway)

    preset_view = application.run_prompt(PROMPT_PRESETS["Project architecture"])
    free_form_view = application.run_prompt("A completely editable question")

    assert preset_view.status is WorkbenchRunStatus.SUCCESS
    assert free_form_view.status is WorkbenchRunStatus.SUCCESS
    assert len(gateway.requests) == 2
    assert gateway.requests[0].tools == gateway.requests[1].tools


def test_model_timeout_is_labeled_as_failed_live_run() -> None:
    view = _application(gateway=_FailingGateway()).run_prompt("hello")

    assert view.status is WorkbenchRunStatus.FAILED
    assert view.error_phase == "agent_runtime"
    assert view.error_message is not None
    assert "Model gateway failed" in view.error_message
    assert view.final_response is None


def test_structured_retrieval_error_is_not_presented_as_successful_tool_execution() -> None:
    gateway = _Gateway(
        (
            _tool_call_response("search_documents", {"query": "bridge"}),
            _final_response("Retrieval failed, so I cannot answer."),
        )
    )
    view = _application(gateway=gateway, search_tool=_FailingSearchTool()).run_prompt("bridge?")

    assert view.status is WorkbenchRunStatus.SUCCESS
    assert view.tool_results[0].status.value == "error"
    assert view.tool_results[0].error is not None
    assert view.tool_results[0].error.error_type == "RuntimeError"
    assert view.traces[0].status == "error"
    assert view.evidence == ()
    tool_execution = next(step for step in view.lifecycle if step.name == "Tool execution")
    assert tool_execution.status == "error"


def test_unknown_tool_proposal_surfaces_validation_failure() -> None:
    gateway = _Gateway(
        (
            _tool_call_response("missing", {"query": "x"}),
            _final_response("The proposed tool was unavailable."),
        )
    )
    view = _application(gateway=gateway).run_prompt("use a missing tool")

    validation = next(
        step for step in view.lifecycle if step.name == "Registry + schema validation"
    )
    assert validation.status == "failed"
    assert "UnknownToolError" in validation.detail
    assert view.traces[0].policy == "not_reached"
    assert view.status is WorkbenchRunStatus.FAILED


def test_malformed_model_proposal_is_labeled_as_failed() -> None:
    view = _application(gateway=_MalformedProposalGateway()).run_prompt("hello")

    assert view.status is WorkbenchRunStatus.FAILED
    assert view.error_phase == "agent_runtime"
    assert view.error_message is not None
    assert "Unsupported model finish reason" in view.error_message


def test_blank_prompt_fails_before_model_execution() -> None:
    gateway = _Gateway((_final_response("unused"),))

    view = _application(gateway=gateway).run_prompt("   ")

    assert view.status is WorkbenchRunStatus.FAILED
    assert view.error_phase == "prompt_validation"
    assert gateway.requests == []
