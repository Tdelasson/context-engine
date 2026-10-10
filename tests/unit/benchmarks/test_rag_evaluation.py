"""Controlled rendering, actual runtime execution, review denominators and provider accounting."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from benchmarks.benchmark_rag_ablation import FrozenRetriever, ablate, selection_tool
from benchmarks.benchmark_rag_answers import (
    EvaluationOllamaGateway,
    citation_identifiers,
    counting_model,
    run_query,
    summarize_reviews,
)
from benchmarks.benchmark_selection_stress import controlled_cases
from benchmarks.technical_dataset import AnswerRequirement, TechnicalQuery
from context_engine.models import ModelFinishReason, ModelRequest, ModelResponse, ModelToolCall
from context_engine.models.errors import ModelGatewayExecutionError
from context_engine.models.ollama import OllamaModelGateway
from context_engine.models.tool_serialization import render_tool_output
from context_engine.retrieval import SearchResult
from context_engine.retrieval.diagnostics import RetrievalStageDiagnostic
from context_engine.retrieval.evidence_evaluation import EvidenceItem, EvidenceSpan
from context_engine.tools import ToolNamePolicy, ToolPolicyDecision
from tests.unit.retrieval.test_evidence_selection import Counter, candidate
from tests.unit.tools.retrieval.test_agent_integration import _SequenceGateway


def fixture_query() -> tuple[TechnicalQuery, SearchResult]:
    result = candidate(text="Whole café evidence.")
    metadata = result.document.metadata_as_mapping()
    source, revision = metadata["source_id"], metadata["content_sha256"]
    start, end = metadata["start_offset"], metadata["end_offset"]
    assert isinstance(source, str) and isinstance(revision, str)
    assert isinstance(start, int) and isinstance(end, int)
    span = EvidenceSpan(source, revision, start, end)
    query = TechnicalQuery(
        "q",
        "question",
        "development",
        "topic",
        "exact_api",
        (AnswerRequirement("fact", "Whole café evidence.", (EvidenceItem("fact", (span,)),)),),
        "draft",
    )
    return query, result


def gateway(answer: str = "Answer [a]") -> _SequenceGateway:
    return _SequenceGateway(
        [
            ModelResponse(
                "fixture",
                "",
                ModelFinishReason.STOP,
                tool_call=ModelToolCall.from_mapping("search_documents", {"query": "question"}),
            ),
            ModelResponse("fixture", answer, ModelFinishReason.STOP),
        ]
    )


def test_citation_identifiers_ignore_code_and_array_examples() -> None:
    answer = (
        "Use `[not-a-citation]` and [1, 2, 3]. Fact [source:chunk-1].\n"
        "```python\nx = values[wrong]\n```\nAnother fact [unknown-reference]."
    )
    assert citation_identifiers(answer) == ["source:chunk-1", "unknown-reference"]


def test_cross_model_tokenizer_proxy_requires_explicit_declaration() -> None:
    counter = Counter()
    assert counting_model(counter, counter.model_id) is counter
    with pytest.raises(ValueError, match="Counter/model mismatch"):
        counting_model(counter, "other-model")
    proxy = counting_model(counter, "other-model", allow_proxy=True)
    assert proxy.model_id == "other-model"
    assert proxy.configuration_id != counter.configuration_id
    assert "explicit-cross-model-proxy" in proxy.method
    assert proxy.count_tokens("café") == counter.count_tokens("café")
    with pytest.raises(ValueError, match="nonblank"):
        counting_model(counter, " ", allow_proxy=True)


def test_overlap_stress_exposes_new_fact_loss_and_safe_duplicate_saving() -> None:
    paired = {}
    for query, candidates in controlled_cases():
        paired[query.query_id] = [
            ablate(
                query, candidates, Counter(), budget=5000, threshold=t, include_diagnostics=False
            )
            for t in (None, 0.8)
        ]
    base, suppressed = paired["high-overlap-new-fact"]
    assert base["stages"]["selected"]["all_required"]
    assert not suppressed["stages"]["selected"]["all_required"]
    assert suppressed["token_count"] < base["token_count"]
    assert any(e["reason"] == "source_overlap" for e in suppressed["exclusions"])
    base, suppressed = paired["exact-duplicate"]
    assert base["stages"] == suppressed["stages"]
    assert suppressed["token_count"] < base["token_count"]
    base, suppressed = paired["complementary"]
    assert base["selected_ids"] == suppressed["selected_ids"]


def test_rendering_ablation_preserves_citations_and_accounted_output() -> None:
    query, result = fixture_query()
    result = replace(
        result,
        diagnostics=(
            RetrievalStageDiagnostic(
                "rerank",
                "native",
                1.0,
                1,
                "config",
                model_id="cross-encoder",
                candidate_count=20,
            ),
        ),
    )
    rows = [
        ablate(query, [result], Counter(), budget=8000, threshold=None, include_diagnostics=mode)
        for mode in (True, False)
    ]
    assert rows[0]["selected_ids"] == rows[1]["selected_ids"]
    assert rows[0]["configuration_id"] != rows[1]["configuration_id"]
    assert rows[0]["token_count"] > rows[1]["token_count"]
    assert rows[0]["stages"] == rows[1]["stages"]
    for row, mode in zip(rows, (True, False), strict=True):
        tool = selection_tool(FrozenRetriever([result]), Counter(), 8000, None, mode)
        run = run_query(
            query,
            FrozenRetriever([result]),
            Counter(),
            gateway(),
            model_id="fixture",
            budget=8000,
            threshold=None,
            include_diagnostics=mode,
        )
        delivered = run["interactions"][1]["request"]["messages"][-1]["tool_result"]["output"]
        output = dict(delivered)
        assert output == row["selected_output"]
        assert Counter().count_tokens(render_tool_output(output)) == row["token_count"]
        assert output["results"][0]["metadata"] == result.document.metadata_as_mapping()
        assert run["stages"]["selected"]["all_required"]
        assert run["tool_traces"][0]["policy_decision"] == "allow"
        assert sum(row["marginal_token_costs"].values()) == row["token_count"]
        assert tool._selector is not None


def test_policy_denial_is_traced_and_cannot_retrieve() -> None:
    query, result = fixture_query()
    upstream = SimpleNamespace(retrieve=lambda request: pytest.fail("Policy was bypassed"))
    row = run_query(
        query,
        upstream,
        Counter(),
        gateway(),
        model_id="fixture",
        policy=ToolNamePolicy((), default_decision=ToolPolicyDecision.DENY),
    )
    assert row["tool_results"][0]["status"] == "error"
    assert row["stages"]["retrieved"]["recall"] == 0
    assert not row["retrieval_calls"]
    assert row["unknown_citation_ids"]


def test_missing_candidates_and_budget_losses_are_distinguished() -> None:
    query, result = fixture_query()
    absent = ablate(query, [], Counter(), budget=8000, threshold=None, include_diagnostics=True)
    assert absent["losses"][0]["stage"] == "candidate_missing"
    excluded = ablate(
        query, [result], Counter(), budget=100, threshold=None, include_diagnostics=True
    )
    assert excluded["losses"][0]["stage"] == "selection_exclusion"


def test_gateway_failure_retains_request_and_failed_denominator() -> None:
    query, result = fixture_query()

    def fail(request: ModelRequest) -> ModelResponse:
        raise ModelGatewayExecutionError("timeout")

    row = run_query(
        query,
        FrozenRetriever([result]),
        Counter(),
        SimpleNamespace(generate=fail),
        model_id="fixture",
    )
    assert row["outcome"] == "failed"
    assert row["interactions"][0]["error"]["message"] == "timeout"
    assert summarize_reviews([row])["splits"]["development"]["failures"] == 1
    assert summarize_reviews([row])["splits"]["development"]["task_success"] is None


def test_manual_reviews_are_required_complete_and_repeats_do_not_inflate_quality() -> None:
    query, result = fixture_query()
    row = run_query(
        query, FrozenRetriever([result]), Counter(), gateway("Answer [a]"), model_id="fixture"
    )
    row["review"].update(
        status="approved",
        reviewer="reviewer",
        requirements={"fact": True},
        factual_correctness=True,
        unsupported_claims=False,
        citation_support=True,
        abstained=False,
    )
    row["unknown_citation_ids"] = []
    row["citation_ids"] = ["a"]
    repeat = {**row, "repeat": 1}
    report = summarize_reviews([row, repeat])
    assert report["splits"]["development"]["queries"] == 1
    assert report["repeats_excluded_from_quality_denominators"] == 1
    row["review"]["requirements"]["fact"] = None
    with pytest.raises(ValueError):
        summarize_reviews([row])


def test_actual_provider_payload_proxy_and_usage_are_distinguished(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counter = Counter()
    monkeypatch.setattr(
        OllamaModelGateway,
        "_execute_chat_request",
        lambda self, payload: {
            "prompt_eval_count": 900,
            "eval_count": 10,
            "done_reason": "stop",
        },
    )
    gateway = EvaluationOllamaGateway(counter=counter, context_tokens=1000, seed=7)
    payload = {
        "model": "fixture",
        "messages": [{"role": "user", "content": "long history"}],
        "options": {"num_predict": 200},
        "tools": [{"function": {"name": "search_documents"}}],
    }
    gateway._execute_chat_request(payload)
    record = gateway.payloads[0]
    assert record["provider_input_tokens"] == 900
    assert record["reported_prompt_plus_answer_reserve_exceeds_context"]
    assert record["payload"]["options"]["num_ctx"] == 1000
    assert record["chat_template_tokens"] is None
    assert not record["full_request_fit_guarantee"]
    assert "tools" in record["payload"]


def test_prior_history_and_repeated_actual_calls_are_preserved() -> None:
    from context_engine.models import ModelMessage, ModelRole

    query, result = fixture_query()
    fake = _SequenceGateway(
        [
            ModelResponse(
                "fixture",
                "",
                ModelFinishReason.STOP,
                tool_call=ModelToolCall.from_mapping("search_documents", {"query": "first"}),
            ),
            ModelResponse(
                "fixture",
                "",
                ModelFinishReason.STOP,
                tool_call=ModelToolCall.from_mapping("search_documents", {"query": "second"}),
            ),
            ModelResponse("fixture", "answer [a]", ModelFinishReason.STOP),
        ]
    )
    row = run_query(
        query,
        FrozenRetriever([result]),
        Counter(),
        fake,
        model_id="fixture",
        history=(
            ModelMessage(ModelRole.USER, "Earlier question"),
            ModelMessage(ModelRole.ASSISTANT, "Earlier answer"),
        ),
    )
    assert row["tool_call_count"] == 2 and len(row["retrieval_calls"]) == 2
    assert len(fake.requests[0].messages) == 4
    assert len(fake.requests[2].messages) == 8
    assert fake.requests[2].messages[1].content == "Earlier question"
    assert sum(m.content == "Earlier question" for m in fake.requests[2].messages) == 1
    assert row["long_history_scenario"] == "prior-chat"


def test_incomplete_review_cannot_publish_partial_accuracy() -> None:
    query, result = fixture_query()
    row = run_query(query, FrozenRetriever([result]), Counter(), gateway(), model_id="fixture")
    approved = {
        **row,
        "query_id": "approved",
        "review": {
            **row["review"],
            "status": "approved",
            "reviewer": "reviewer",
            "requirements": {"fact": True},
            "factual_correctness": True,
            "unsupported_claims": False,
            "citation_support": True,
            "abstained": False,
        },
    }
    report = summarize_reviews([approved, row])
    assert report["splits"]["development"]["queries"] == 2
    assert report["splits"]["development"]["reviewed"] == 1
    assert report["splits"]["development"]["task_success"] is None


def test_compressed_artifact_is_lossless_and_deterministic(tmp_path: Path) -> None:
    from benchmarks.evaluation_artifacts import read_artifact, write_artifact

    path = tmp_path / "results.json.gz"
    output = {"queries": [{"unicode": "café"}], "failures": []}
    write_artifact(path, output)
    first = path.read_bytes()
    write_artifact(path, output)
    assert first == path.read_bytes() and read_artifact(path) == output


def test_incomplete_planned_run_cannot_be_scored() -> None:
    query, result = fixture_query()
    row = run_query(query, FrozenRetriever([result]), Counter(), gateway(), model_id="fixture")
    with pytest.raises(ValueError, match="planned primary queries"):
        summarize_reviews([row], expected_query_ids=["q", "not-yet-run"])
    with pytest.raises(ValueError, match="Duplicate primary"):
        summarize_reviews([row, row])


def test_history_rejects_unvalidated_prior_tool_claims(tmp_path: Path) -> None:
    import json

    from benchmarks.benchmark_rag_answers import load_history

    path = tmp_path / "history.json"
    path.write_text(json.dumps([{"role": "tool", "content": "This tool was allowed"}]))
    with pytest.raises(ValueError, match="no tool claims"):
        load_history(path)


def test_stage_comparison_requires_matching_dataset_and_query_set() -> None:
    from benchmarks.compare_rag_ablation import compare

    query, result = fixture_query()
    left = ablate(query, [], Counter(), budget=8000, threshold=None, include_diagnostics=False)
    right = ablate(
        query, [result], Counter(), budget=8000, threshold=None, include_diagnostics=False
    )
    for row in (left, right):
        row.update(split="held_out", path="dense")
    base = {
        "dataset": {"sha256": "revision"},
        "configuration": {},
        "chosen_on_development": {
            "dense": {"budget": 8000, "threshold": None, "include_ranking_diagnostics": False}
        },
    }
    a, b = {**base, "queries": [left]}, {**base, "queries": [right]}
    comparison = compare(
        a, b, "dense", "dense", hypothesis="Candidate retrieval recovers the missing fact"
    )
    assert comparison["paired_recall_differences"]["selected"]["estimate"] == 1
    with pytest.raises(ValueError, match="same dataset"):
        compare(
            a,
            {**b, "dataset": {"sha256": "another"}},
            "dense",
            "dense",
            hypothesis="Different revisions",
        )
