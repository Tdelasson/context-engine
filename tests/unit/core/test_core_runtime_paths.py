"""Runtime paths the facade must keep: calculator, prompts, bad proposals, live composition."""

from __future__ import annotations

from typing import cast

import pytest

from context_engine.core import ApplicationSettings, RunStatus
from context_engine.core.prompts import PROMPT_PRESETS
from context_engine.models import ModelFinishReason, ModelResponse
from tests.unit.core.test_core_application import _application, _final, _Gateway, _tool_call


class _MalformedProposalGateway:
    def generate(self, request: object) -> ModelResponse:
        del request
        return ModelResponse(
            model_id="fake-model",
            output_text="malformed",
            finish_reason=cast(ModelFinishReason, "malformed"),
        )


def test_calculator_uses_the_same_runtime_boundary() -> None:
    app = _application(
        _Gateway(
            [
                _tool_call("calculator", {"expression": "(144 / 12) + 7"}),
                _final("The result is 19."),
            ]
        )
    )

    record = app.run_prompt(PROMPT_PRESETS["Calculator"], timeout=5)

    assert record.status is RunStatus.SUCCESS
    assert record.tool_results[0].output_as_mapping() == {"value": 19.0}
    assert record.traces[0].invocation.tool_name == "calculator"


def test_preset_and_free_form_prompts_share_the_same_execution_path() -> None:
    gateway = _Gateway([_final("preset"), _final("free form")])
    app = _application(gateway)

    preset = app.run_prompt(PROMPT_PRESETS["Project architecture"], timeout=5)
    free_form = app.run_prompt("A completely editable question", timeout=5)

    assert preset.status is RunStatus.SUCCESS
    assert free_form.status is RunStatus.SUCCESS
    assert len(gateway.requests) == 2
    assert gateway.requests[0].tools == gateway.requests[1].tools


def test_unknown_tool_proposal_is_rejected_before_policy() -> None:
    app = _application(_Gateway([_tool_call("missing", {"query": "x"}), _final("Unavailable.")]))

    record = app.run_prompt("use a missing tool", timeout=5)

    assert record.status is RunStatus.FAILED
    assert record.traces[0].policy_decision is None
    assert record.traces[0].error is not None
    assert record.traces[0].error.error_type == "UnknownToolError"


def test_malformed_model_proposal_is_reported_as_failed() -> None:
    record = _application(_MalformedProposalGateway()).run_prompt("hello", timeout=5)

    assert record.status is RunStatus.FAILED
    assert record.error_phase == "agent_runtime"
    assert record.error_message is not None
    assert "Unsupported model finish reason" in record.error_message


def test_live_hybrid_composition_retains_tool_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    from context_engine.core import composition
    from context_engine.retrieval import VectorStoreCollectionConfig
    from context_engine.retrieval.hybrid import HybridRetriever
    from context_engine.retrieval.retriever import RetrievalRequest
    from context_engine.retrieval.vector_store import SearchResult
    from context_engine.tools.retrieval import SearchDocumentsTool
    from tests.source_index_fixtures import (
        CharacterCounter,
        FixtureEmbeddingProvider,
        MemorySourceStore,
        fixture_chunker,
    )

    class Provider(FixtureEmbeddingProvider):
        indexing_identity = "fixture-v1"

        def build_token_counter(self) -> CharacterCounter:
            return CharacterCounter()

    class EmptyLexical:
        def retrieve(self, request: RetrievalRequest) -> tuple[SearchResult, ...]:
            return ()

    captured: list[object] = []

    def store_factory(config: VectorStoreCollectionConfig, **kwargs: object) -> MemorySourceStore:
        store = MemorySourceStore(fixture_chunker())
        store.collection_config = config
        return store

    def capture_tool(retriever: object) -> object:
        captured.append(retriever)
        return SearchDocumentsTool(retriever)  # type: ignore[arg-type]

    monkeypatch.setattr(composition, "LocalEmbeddingProvider", lambda _: Provider())
    monkeypatch.setattr(
        "context_engine.retrieval.qdrant_lexical_index.QdrantBM25ChunkStore", store_factory
    )
    monkeypatch.setattr(composition, "_build_lexical_retriever", lambda _: EmptyLexical())
    monkeypatch.setattr(composition, "SearchDocumentsTool", capture_tool)

    built = composition.build_live_application(
        ApplicationSettings(retrieval_strategy="hybrid", chunk_overlap_tokens=0)
    )

    assert isinstance(captured[0], HybridRetriever)
    assert built.settings.retrieval_strategy == "hybrid"
