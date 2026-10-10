"""Opt-in real answering-tokenizer and native hybrid/reranked evidence-budget checks."""

import os
from dataclasses import asdict
from types import SimpleNamespace

import pytest

from benchmarks.benchmark_evidence_selection import run_benchmark
from context_engine.models.evidence_counting import QwenEvidenceTokenCounter
from context_engine.models.tool_serialization import model_visible_tool_output, render_tool_output
from context_engine.retrieval import Document, SearchResult
from context_engine.retrieval.diagnostics import RetrievalStageDiagnostic
from context_engine.retrieval.evidence_selection import EvidenceSelectionConfig
from context_engine.tools import ToolInvocation, ToolRegistry, ToolResultStatus, ToolRuntime
from context_engine.tools.retrieval import SearchDocumentsTool, SearchDocumentsToolConfig


@pytest.mark.parametrize("strategy", ["dense-memory", "hybrid-reranked-qdrant"])
def test_real_evidence_selection(strategy: str) -> None:
    tokenizer = os.getenv("CONTEXT_ENGINE_EVIDENCE_TOKENIZER_DIRECTORY")
    embedding = os.getenv("CONTEXT_ENGINE_EMBEDDING_MODEL_REFERENCE")
    if (
        not tokenizer
        or not embedding
        or os.getenv("CONTEXT_ENGINE_RUN_EVIDENCE_SELECTION_INTEGRATION") != "1"
    ):
        pytest.skip(
            "Supply prepared tokenizers/models and opt in to evidence selection integration."
        )
    if (
        strategy == "hybrid-reranked-qdrant"
        and os.getenv("CONTEXT_ENGINE_RUN_QDRANT_LEXICAL_INTEGRATION") != "1"
    ):
        pytest.skip("Native hybrid Qdrant integration is opt-in.")
    assert tokenizer is not None and embedding is not None
    report = run_benchmark(
        embedding,
        tokenizer,
        strategy=strategy,
        qdrant_url=os.getenv("CONTEXT_ENGINE_QDRANT_URL", "http://localhost:6333"),
        reranking_reference=os.getenv("CONTEXT_ENGINE_RERANKING_INTEGRATION_MODEL"),
    )
    assert report["failures"] == []
    assert all(row["token_count"] <= row["budget"] for row in report["queries"])
    candidates = tuple(
        SearchResult(
            Document.from_mapping(**item["document"]),
            item["score"],
            tuple(RetrievalStageDiagnostic(**stage) for stage in item["diagnostics"]),
        )
        for item in report["saved_candidates"]["dev-approval"]
    )
    counter = QwenEvidenceTokenCounter(tokenizer)
    tool = SearchDocumentsTool(
        SimpleNamespace(retrieve=lambda _: candidates),
        config=SearchDocumentsToolConfig(top_k=5),
        selection_config=EvidenceSelectionConfig(8192),
        evidence_counter=counter,
    )
    registry = ToolRegistry()
    registry.register(tool)
    result = ToolRuntime(registry).execute(
        ToolInvocation.from_mapping(
            "search_documents", {"query": "When do tools require approval?"}
        )
    )
    assert result.status is ToolResultStatus.SUCCESS
    output = result.output_as_mapping()
    visible = model_visible_tool_output("search_documents", output)
    diagnostic = output["selection_diagnostics"]
    assert isinstance(diagnostic, dict)
    assert counter.count_tokens(render_tool_output(visible)) == diagnostic["token_count"]
    selected_results = visible["results"]
    assert isinstance(selected_results, list) and selected_results
    for selected in selected_results:
        assert not selected["content_truncated"]
        original = next(r for r in candidates if r.document.document_id == selected["document_id"])
        assert selected["content"] == original.document.content
        assert selected["metadata"]["content_sha256"]
        assert (
            selected["diagnostics"] == [asdict(stage) for stage in original.diagnostics]
            if original.diagnostics
            else "diagnostics" not in selected
        )
