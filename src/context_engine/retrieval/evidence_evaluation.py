"""Deterministic evidence coverage in canonical extracted-text coordinates."""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from context_engine.knowledge.processing import ProcessedSource
from context_engine.retrieval.vector_store import SearchResult


@dataclass(frozen=True, slots=True)
class EvidenceSpan:
    source_id: str
    content_sha256: str
    start_offset: int
    end_offset: int
    representation: str = "extracted_text"

    def __post_init__(self) -> None:
        if (
            not isinstance(self.source_id, str)
            or not self.source_id.strip()
            or not isinstance(self.content_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", self.content_sha256) is None
            or type(self.start_offset) is not int
            or type(self.end_offset) is not int
            or not 0 <= self.start_offset < self.end_offset
            or self.representation != "extracted_text"
        ):
            raise ValueError("Evidence needs a source revision and nonempty extracted-text span.")


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    evidence_id: str
    spans: tuple[EvidenceSpan, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, str) or not self.evidence_id.strip() or not self.spans:
            raise ValueError("Evidence items require an identity and supporting spans.")
        if any(not isinstance(span, EvidenceSpan) for span in self.spans):
            raise ValueError("Evidence items require typed spans.")


def validate_evidence(
    items: Sequence[EvidenceItem], sources: Mapping[str, ProcessedSource]
) -> None:
    """Reject changed revisions or invalid offsets before running an experiment."""
    if len({item.evidence_id for item in items}) != len(items):
        raise ValueError("Duplicate evidence IDs.")
    for item in items:
        for span in item.spans:
            source = sources.get(span.source_id)
            if source is None or source.provenance.content_sha256 != span.content_sha256:
                raise ValueError("Unknown or stale evidence source revision.")
            if span.end_offset > len(source.text):
                raise ValueError("Evidence offset exceeds extracted text.")


@dataclass(frozen=True, slots=True)
class EvidenceQueryMetrics:
    supported: bool
    returned_count: int
    coverage_at_k: Mapping[int, Mapping[str, float]]
    recall_at_k: Mapping[int, float] | None
    all_required_at_k: Mapping[int, bool] | None
    first_support_rank: int | None


def _union_length(intervals: Sequence[tuple[int, int]]) -> int:
    total = 0
    end = -1
    for start, stop in sorted(intervals):
        total += max(0, stop - max(start, end))
        end = max(end, stop)
    return total


def _result_spans(result: SearchResult) -> tuple[EvidenceSpan, ...]:
    metadata = result.document.metadata_as_mapping()
    if metadata.get("text_representation") != "extracted_text":
        raise ValueError("Retrieved chunks require canonical extracted-text provenance.")
    source_id = metadata.get("source_id")
    revision = metadata.get("content_sha256")
    if not isinstance(source_id, str) or not isinstance(revision, str):
        raise ValueError("Retrieved chunk lacks source identity or revision.")
    raw_spans = metadata.get("spans")
    if not isinstance(raw_spans, list) or not raw_spans:
        raise ValueError("Retrieved chunk has no contributing provenance spans.")
    spans = []
    for raw in raw_spans:
        if not isinstance(raw, dict) or not isinstance(raw.get("location"), dict):
            raise ValueError("Malformed chunk provenance span.")
        location = raw["location"]
        spans.append(
            EvidenceSpan(
                source_id=source_id,
                content_sha256=revision,
                start_offset=location.get("start_offset"),
                end_offset=location.get("end_offset"),
                representation=location.get("representation"),
            )
        )
    return tuple(spans)


def _coverage(item: EvidenceItem, retrieved: Sequence[EvidenceSpan]) -> float:
    keys = {(span.source_id, span.content_sha256) for span in item.spans}
    denominator = 0
    numerator = 0
    for key in keys:
        labels = [
            (s.start_offset, s.end_offset)
            for s in item.spans
            if (s.source_id, s.content_sha256) == key
        ]
        denominator += _union_length(labels)
        intersections = [
            (max(start, span.start_offset), min(end, span.end_offset))
            for start, end in labels
            for span in retrieved
            if (span.source_id, span.content_sha256) == key
            and max(start, span.start_offset) < min(end, span.end_offset)
        ]
        numerator += _union_length(intersections)
    return numerator / denominator


def evaluate_evidence_query(
    results: Sequence[SearchResult],
    items: Sequence[EvidenceItem],
    *,
    k_values: Sequence[int] = (1, 5, 10),
    coverage_threshold: float = 1.0,
) -> EvidenceQueryMetrics:
    """Cumulative union coverage; each complete evidence item counts once.

    First-support rank is the first prefix completing any item. Duplicate chunks
    still occupy result positions but cannot add duplicate covered characters.
    No-support queries have no recall, all-required or support-rank denominator.
    """
    if not k_values or any(type(k) is not int or k <= 0 for k in k_values):
        raise ValueError("K values must be positive integers.")
    if isinstance(coverage_threshold, bool) or not 0 < coverage_threshold <= 1:
        raise ValueError("Coverage threshold must be in (0, 1].")
    if len({item.evidence_id for item in items}) != len(items):
        raise ValueError("Duplicate evidence IDs.")
    spans = tuple(_result_spans(result) for result in results)
    if not items:
        return EvidenceQueryMetrics(False, len(results), {}, None, None, None)
    prefixes: list[dict[str, float]] = [{item.evidence_id: 0.0 for item in items}]
    accumulated: list[EvidenceSpan] = []
    for result_spans in spans:
        accumulated.extend(result_spans)
        prefixes.append({item.evidence_id: _coverage(item, accumulated) for item in items})
    coverage = {k: prefixes[min(k, len(results))] for k in dict.fromkeys(k_values)}
    recall = {
        k: sum(value >= coverage_threshold for value in values.values()) / len(items)
        for k, values in coverage.items()
    }
    first = next(
        (
            rank
            for rank, values in enumerate(prefixes[1:], 1)
            if any(value >= coverage_threshold for value in values.values())
        ),
        None,
    )
    return EvidenceQueryMetrics(
        True,
        len(results),
        coverage,
        recall,
        {k: value == 1.0 for k, value in recall.items()},
        first,
    )
