"""Evidence-level semantics independent of inference, store, and chunk settings."""

from dataclasses import replace
from typing import Any

import pytest

from context_engine.knowledge.processing import SourceFormat, SourceInput, process_source
from context_engine.retrieval import Document, SearchResult
from context_engine.retrieval.evidence_evaluation import (
    EvidenceItem,
    EvidenceSpan,
    evaluate_evidence_query,
    validate_evidence,
)

REVISION = "a" * 64


def span(start: int, end: int, *, source: str = "source", revision: str = REVISION) -> EvidenceSpan:
    return EvidenceSpan(source, revision, start, end)


def result(
    *intervals: tuple[int, int], source: str = "source", revision: str = REVISION
) -> SearchResult:
    return SearchResult(
        Document.from_mapping(
            document_id="chunk",
            content="fixture",
            metadata={
                "source_id": source,
                "content_sha256": revision,
                "text_representation": "extracted_text",
                "spans": [
                    {
                        "block_index": i,
                        "location": {
                            "start_offset": start,
                            "end_offset": end,
                            "representation": "extracted_text",
                            "page_number": i + 1,
                        },
                    }
                    for i, (start, end) in enumerate(intervals)
                ],
            },
        ),
        1.0,
    )


def test_partial_joint_and_duplicate_coverage() -> None:
    item = EvidenceItem("fact", (span(10, 30),))
    matches = [result((10, 20)), result((10, 20)), result((18, 30))]
    metrics = evaluate_evidence_query(matches, [item], k_values=(1, 2, 3, 10))
    assert metrics.coverage_at_k == {
        1: {"fact": 0.5},
        2: {"fact": 0.5},
        3: {"fact": 1},
        10: {"fact": 1},
    }
    assert metrics.recall_at_k == {1: 0, 2: 0, 3: 1, 10: 1}
    assert metrics.first_support_rank == 3
    assert evaluate_evidence_query(matches, [item], coverage_threshold=0.5).first_support_rank == 1


def test_incidental_overlap_and_wrong_revision_are_not_support() -> None:
    item = EvidenceItem("fact", (span(10, 30),))
    metrics = evaluate_evidence_query(
        [result((0, 11)), result((10, 30), revision="b" * 64)], [item]
    )
    assert metrics.coverage_at_k[5]["fact"] == 0.05
    assert metrics.recall_at_k is not None and metrics.recall_at_k[5] == 0
    assert metrics.first_support_rank is None


def test_multi_block_page_and_multi_source_required_evidence() -> None:
    items = [
        EvidenceItem("pages", (span(10, 20), span(30, 40))),
        EvidenceItem("second", (span(0, 10, source="other"),)),
    ]
    metrics = evaluate_evidence_query(
        [result((10, 20), (30, 40)), result((0, 10), source="other")], items, k_values=(1, 2)
    )
    assert metrics.recall_at_k == {1: 0.5, 2: 1}
    assert metrics.all_required_at_k == {1: False, 2: True}
    assert metrics.first_support_rank == 1


def test_overlapping_labels_have_union_denominator() -> None:
    item = EvidenceItem("fact", (span(0, 10), span(5, 15)))
    metrics = evaluate_evidence_query([result((0, 10))], [item])
    assert metrics.coverage_at_k[1]["fact"] == 10 / 15


def test_empty_results_and_no_support_have_distinct_denominators() -> None:
    metrics = evaluate_evidence_query([], [EvidenceItem("fact", (span(0, 10),))])
    assert metrics.recall_at_k == {1: 0, 5: 0, 10: 0}
    unsupported = evaluate_evidence_query([result((0, 10))], [])
    assert not unsupported.supported and unsupported.returned_count == 1
    assert unsupported.recall_at_k is None and unsupported.all_required_at_k is None


@pytest.mark.parametrize(
    "changes",
    [
        {"start_offset": -1},
        {"end_offset": 0},
        {"start_offset": True},
        {"content_sha256": "stale"},
        {"representation": "bytes"},
    ],
)
def test_invalid_span(changes: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        replace(span(0, 10), **changes)


def test_label_validation_rejects_stale_out_of_bounds_and_duplicate_ids() -> None:
    source = process_source(SourceInput("source", "note.txt", b"abc", SourceFormat.TEXT))
    valid = EvidenceSpan("source", source.provenance.content_sha256, 0, 3)
    validate_evidence([EvidenceItem("fact", (valid,))], {"source": source})
    for items in (
        [EvidenceItem("fact", (span(0, 3),))],
        [EvidenceItem("fact", (replace(valid, end_offset=4),))],
        [EvidenceItem("fact", (valid,)), EvidenceItem("fact", (valid,))],
    ):
        with pytest.raises(ValueError):
            validate_evidence(items, {"source": source})


@pytest.mark.parametrize(
    "k_values,threshold", [((), 1), ((0,), 1), ((True,), 1), ((1,), 0), ((1,), 1.1)]
)
def test_bad_metric_configuration(k_values: tuple[int, ...], threshold: float) -> None:
    with pytest.raises(ValueError):
        evaluate_evidence_query([], [], k_values=k_values, coverage_threshold=threshold)


def test_malformed_result_provenance_fails_explicitly() -> None:
    malformed = SearchResult(Document.from_mapping(document_id="x", content="x"), 1)
    with pytest.raises(ValueError):
        evaluate_evidence_query([malformed], [])
