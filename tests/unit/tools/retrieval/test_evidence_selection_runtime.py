"""Accounting representation survives policy, runtime history and workbench presentation."""

import json
from types import SimpleNamespace

import pytest

from context_engine.agent import AgentRuntime
from context_engine.models import ModelFinishReason, ModelResponse, ModelToolCall
from context_engine.models.evidence_counting import QwenEvidenceTokenCounter
from context_engine.models.ollama import OllamaModelGateway
from context_engine.models.tool_serialization import render_tool_output
from context_engine.retrieval.evidence_selection import (
    EvidenceSelectionConfig,
    EvidenceSelectionError,
)
from context_engine.tools import ToolInvocation, ToolRegistry, ToolResultStatus, ToolRuntime
from context_engine.tools.policy import ToolNamePolicy, ToolPolicyDecision
from context_engine.tools.retrieval import SearchDocumentsTool
from context_engine.workbench.application import configure_evidence_selection
from context_engine.workbench.config import WorkbenchConfigurationError, WorkbenchSettings
from context_engine.workbench.presentation import build_run_view
from tests.unit.retrieval.test_evidence_selection import Counter, candidate
from tests.unit.tools.retrieval.test_agent_integration import _SequenceGateway


def test_policy_failure_accounted_history_and_selected_workbench_evidence() -> None:
    result = candidate(text="Whole café passage.")
    calls = []

    def retrieve(request: object) -> list[object]:
        calls.append(request)
        return [result]

    tool = SearchDocumentsTool(
        SimpleNamespace(retrieve=retrieve),
        selection_config=EvidenceSelectionConfig(5000),
        evidence_counter=Counter(),
    )
    registry = ToolRegistry()
    registry.register(tool)
    invocation = ToolInvocation.from_mapping("search_documents", {"query": "q"})
    denied = ToolRuntime(
        registry, policy=ToolNamePolicy((), default_decision=ToolPolicyDecision.DENY)
    ).execute(invocation)
    assert denied.status is ToolResultStatus.ERROR and not calls
    gateway = _SequenceGateway(
        [
            ModelResponse(
                "fixture-answerer",
                "",
                ModelFinishReason.STOP,
                tool_call=ModelToolCall.from_mapping("search_documents", {"query": "q"}),
            ),
            ModelResponse("fixture-answerer", "answer", ModelFinishReason.STOP),
        ]
    )
    runtime = AgentRuntime(model_gateway=gateway, tool_runtime=ToolRuntime(registry))
    run = runtime.run(model_id="fixture-answerer", user_prompt="q", max_model_iterations=3)
    model_result = gateway.requests[1].messages[-1].tool_result
    assert model_result is not None
    output = model_result.output_as_mapping()
    assert "selection_diagnostics" not in output
    runtime_output = runtime.tool_results[0].output_as_mapping()
    diagnostic = runtime_output["selection_diagnostics"]
    assert isinstance(diagnostic, dict)
    assert diagnostic["token_count"] == Counter().count_tokens(render_tool_output(output))
    # The provider's JSON envelope contains the exact counted output serialization.
    message = OllamaModelGateway(model_name="fixture-answerer")._translate_message(
        gateway.requests[1].messages[-1]
    )
    content = message["content"]
    assert isinstance(content, str)
    envelope = json.loads(content)
    assert render_tool_output(envelope["output"]) == render_tool_output(output)
    assert render_tool_output(output) in content
    view = build_run_view(
        prompt="q",
        result=run,
        tool_results=runtime.tool_results,
        traces=runtime.tool_execution_traces,
    )
    assert view.evidence[0].evidence_selected
    assert view.evidence[0].content == result.document.content
    assert not view.evidence[0].content_truncated
    assert runtime.tool_execution_traces[0].output_as_mapping() == runtime_output


def test_counting_error_is_a_structured_tool_failure() -> None:
    registry = ToolRegistry()
    registry.register(
        SearchDocumentsTool(
            SimpleNamespace(retrieve=lambda _: []),
            selection_config=EvidenceSelectionConfig(1),
            evidence_counter=Counter(),
        )
    )
    result = ToolRuntime(registry).execute(
        ToolInvocation.from_mapping("search_documents", {"query": "q"})
    )
    assert result.status is ToolResultStatus.ERROR
    assert result.error and result.error.error_type == "EvidenceSelectionError"


def test_workbench_explicit_configuration_and_unavailable_counter(tmp_path: object) -> None:
    with pytest.raises(WorkbenchConfigurationError):
        WorkbenchSettings(evidence_selection_enabled=True)
    with pytest.raises(WorkbenchConfigurationError):
        WorkbenchSettings(evidence_token_budget=True)
    settings = WorkbenchSettings(
        model_id="qwen2.5:0.5b",
        evidence_selection_enabled=True,
        evidence_tokenizer_directory="/does-not-exist",
    )
    with pytest.raises(Exception, match="evidence_selection"):
        configure_evidence_selection(SimpleNamespace(retrieve=lambda _: []), settings)
    assert configure_evidence_selection(SimpleNamespace(retrieve=lambda _: []), WorkbenchSettings())


def test_tokenizer_rejects_other_models_missing_files_and_wrong_revision(tmp_path: object) -> None:
    from pathlib import Path

    path = Path(str(tmp_path))
    with pytest.raises(EvidenceSelectionError, match="supported"):
        QwenEvidenceTokenCounter(str(path), model_id="llama3.2:1b")
    with pytest.raises(EvidenceSelectionError, match="unavailable"):
        QwenEvidenceTokenCounter(str(path))
    (path / "tokenizer_config.json").write_text('{"tokenizer_class":"Qwen2Tokenizer"}')
    (path / "tokenizer.json").write_text("{}")
    with pytest.raises(EvidenceSelectionError, match="incompatible"):
        QwenEvidenceTokenCounter(str(path))


def test_environment_selection_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTEXT_ENGINE_EVIDENCE_SELECTION_ENABLED", "true")
    monkeypatch.setenv("CONTEXT_ENGINE_WORKBENCH_MODEL", "qwen2.5:0.5b")
    monkeypatch.setenv("CONTEXT_ENGINE_EVIDENCE_TOKENIZER_DIRECTORY", "/local/qwen")
    monkeypatch.setenv("CONTEXT_ENGINE_EVIDENCE_TOKEN_BUDGET", "2048")
    monkeypatch.setenv("CONTEXT_ENGINE_EVIDENCE_OVERLAP_THRESHOLD", "0.5")
    settings = WorkbenchSettings.from_environment()
    assert settings.evidence_token_budget == 2048 and settings.evidence_overlap_threshold == 0.5
