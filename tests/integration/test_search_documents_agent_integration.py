from __future__ import annotations

import os
import uuid

import pytest

from context_engine.agent import AgentRuntime, AgentRuntimeExecutionOutcome
from context_engine.models import ModelRequest, ModelResponse, OllamaModelGateway
from context_engine.retrieval import (
    Document,
    EmbeddingVectorStoreRetriever,
    LocalEmbeddingProvider,
    LocalEmbeddingProviderConfig,
    LocalEmbeddingProviderInitializationError,
    VectorDistanceMetric,
    VectorStoreCollectionConfig,
    VectorStoreConfigurationError,
    VectorStoreRecord,
)
from context_engine.retrieval.qdrant_vector_store import QdrantVectorStore
from context_engine.tools import ToolRegistry, ToolResultStatus, ToolRuntime
from context_engine.tools.retrieval import SearchDocumentsTool, SearchDocumentsToolConfig


def _skip_unless_search_tool_integration_enabled() -> None:
    if os.getenv("CONTEXT_ENGINE_RUN_SEARCH_TOOL_INTEGRATION") != "1":
        pytest.skip(
            "Set CONTEXT_ENGINE_RUN_SEARCH_TOOL_INTEGRATION=1 to run the live local "
            "search-tool integration test."
        )


def _build_local_provider() -> LocalEmbeddingProvider:
    model_reference = os.getenv("CONTEXT_ENGINE_EMBEDDING_MODEL")
    if not model_reference:
        pytest.skip("Set CONTEXT_ENGINE_EMBEDDING_MODEL to a locally available model.")
    assert model_reference is not None

    try:
        return LocalEmbeddingProvider(
            LocalEmbeddingProviderConfig(
                model_id=os.getenv("CONTEXT_ENGINE_EMBEDDING_MODEL_ID", model_reference),
                model_reference=model_reference,
                batch_size=int(os.getenv("CONTEXT_ENGINE_EMBEDDING_BATCH_SIZE", "8")),
                normalize_embeddings=(os.getenv("CONTEXT_ENGINE_EMBEDDING_NORMALIZE", "0") == "1"),
                query_prefix=os.getenv("CONTEXT_ENGINE_EMBEDDING_QUERY_PREFIX", ""),
                document_prefix=os.getenv("CONTEXT_ENGINE_EMBEDDING_DOCUMENT_PREFIX", ""),
            )
        )
    except LocalEmbeddingProviderInitializationError as exc:
        pytest.skip(f"Local embedding model/runtime unavailable: {exc}")
    raise AssertionError("pytest.skip should exit before this line.")


def _build_gateway() -> OllamaModelGateway:
    model_name = os.getenv("CONTEXT_ENGINE_OLLAMA_MODEL")
    if not model_name:
        pytest.skip("Set CONTEXT_ENGINE_OLLAMA_MODEL to a locally available Ollama model.")

    return OllamaModelGateway(
        base_url=os.getenv("CONTEXT_ENGINE_OLLAMA_BASE_URL", "http://localhost:11434"),
        model_name=model_name,
        timeout_seconds=float(os.getenv("CONTEXT_ENGINE_OLLAMA_TIMEOUT_SECONDS", "30")),
    )


class _RecordingGateway:
    def __init__(self, gateway: OllamaModelGateway) -> None:
        self._gateway = gateway
        self.requests: list[ModelRequest] = []
        self.responses: list[ModelResponse] = []

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        response = self._gateway.generate(request)
        self.responses.append(response)
        return response


def test_local_agent_can_search_live_documents_then_respond() -> None:
    _skip_unless_search_tool_integration_enabled()
    provider = _build_local_provider()
    gateway = _RecordingGateway(_build_gateway())
    model_name = os.getenv("CONTEXT_ENGINE_OLLAMA_MODEL")
    assert model_name is not None

    documents = (
        Document.from_mapping(
            document_id="tool-security-boundary",
            content=(
                "Context Engine controls tool execution through registry lookup, schema "
                "validation, policy evaluation, approval when required, deterministic "
                "execution, and a structured execution trace."
            ),
            metadata={"title": "Tool Security Boundary", "topic": "tools"},
        ),
        Document.from_mapping(
            document_id="retrieval-boundary",
            content=(
                "The Retriever coordinates query embedding and vector-store search without "
                "exposing provider-specific vector database types."
            ),
            metadata={"title": "Retrieval Boundary", "topic": "retrieval"},
        ),
    )
    embeddings = provider.embed_documents(documents)
    assert embeddings

    try:
        vector_store = QdrantVectorStore(
            VectorStoreCollectionConfig(
                collection_name=f"context-engine-search-tool-it-{uuid.uuid4().hex}",
                embedding_model_id=embeddings[0].model_id,
                dimensions=embeddings[0].dimensions,
                distance_metric=VectorDistanceMetric.COSINE,
            ),
            url=os.getenv("CONTEXT_ENGINE_QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("CONTEXT_ENGINE_QDRANT_API_KEY"),
            timeout_seconds=float(os.getenv("CONTEXT_ENGINE_QDRANT_TIMEOUT_SECONDS", "5")),
        )
    except VectorStoreConfigurationError as exc:
        pytest.skip(f"Qdrant integration dependency/runtime unavailable: {exc}")

    vector_store.upsert(
        tuple(
            VectorStoreRecord(document=document, embedding=embedding)
            for document, embedding in zip(documents, embeddings, strict=True)
        )
    )
    retriever = EmbeddingVectorStoreRetriever(
        embedding_provider=provider,
        vector_store=vector_store,
    )
    registry = ToolRegistry()
    registry.register(
        SearchDocumentsTool(
            retriever,
            config=SearchDocumentsToolConfig(top_k=2, max_content_chars=500),
        )
    )
    runtime = AgentRuntime(model_gateway=gateway, tool_runtime=ToolRuntime(registry))

    result = runtime.run(
        model_id=model_name,
        system_prompt=(
            "You must call search_documents exactly once before answering. "
            "Call it with exactly "
            '{"query":"How does Context Engine control tool execution?"}. '
            "Do not answer from prior knowledge. After receiving the tool result, answer "
            "briefly using only the retrieved evidence."
        ),
        user_prompt="How does Context Engine control tool execution?",
        temperature=0.0,
        max_output_tokens=160,
        max_model_iterations=4,
    )

    assert result.outcome is AgentRuntimeExecutionOutcome.RESPONDED
    assert result.proposed_response
    assert len(gateway.requests) >= 2
    assert gateway.responses[0].tool_call is not None
    assert gateway.responses[0].tool_call.tool_name == "search_documents"
    assert len(runtime.tool_results) == 1
    assert runtime.tool_results[0].status is ToolResultStatus.SUCCESS
    output = runtime.tool_results[0].output_as_mapping()
    assert output["result_count"]
    results = output["results"]
    assert isinstance(results, list)
    assert any(
        isinstance(item, dict) and item.get("document_id") == "tool-security-boundary"
        for item in results
    )
