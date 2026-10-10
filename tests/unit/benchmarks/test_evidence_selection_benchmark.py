"""Equal-budget baseline and duplicate/source accounting use the identical candidate list."""

from dataclasses import replace

from benchmarks.benchmark_evidence_selection import compare_candidates, redundancy
from context_engine.retrieval import Document
from tests.unit.retrieval.test_evidence_selection import Counter, candidate


def test_budget_baseline_preserves_candidates_and_reports_real_cost() -> None:
    candidates = (candidate(), candidate(5, 15, identity="b"))
    baseline = compare_candidates("q", candidates, Counter(), 5000, None)
    suppressed = compare_candidates("q", candidates, Counter(), 5000, 0.5)
    assert baseline["selection"].selected == candidates
    assert suppressed["selection"].selected == candidates[:1]
    assert baseline["redundancy"]["repeated_source_characters"] == 5
    assert suppressed["redundancy"]["repeated_source_characters"] == 0
    assert baseline["selection"].token_count <= 5000
    assert suppressed["selection"].token_count < baseline["selection"].token_count
    assert baseline["selection_seconds"] >= 0


def test_distinct_source_coordinates_and_uncomparable_candidates_are_not_conflated() -> None:
    a, b = candidate(), candidate(identity="b", source="other")
    unknown = replace(a, document=Document.from_mapping(document_id="unknown", content="x"))
    assert redundancy([a, b, unknown]) == {
        "repeated_source_characters": 0,
        "repeated_source_fraction": 0,
        "uncomparable_candidates": 1,
    }


def test_result_serialization_is_stable_and_lossless() -> None:
    import json

    from benchmarks.benchmark_evidence_selection import serialize_artifact

    payload = {
        "queries": [{"query": 'café "quoted"', "tokens": 123}],
        "failures": [],
        "saved_candidates": {"q": [{"content": "line\nline", "score": 0.5}]},
    }
    rendered = serialize_artifact(payload)
    assert json.loads(rendered) == payload
    assert serialize_artifact(dict(reversed(list(payload.items())))) == rendered
