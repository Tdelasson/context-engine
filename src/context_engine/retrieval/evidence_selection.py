"""Deterministic whole-passage selection, independent of retrieval and inference."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
from math import isfinite
from typing import Protocol

from context_engine.models.tool_serialization import render_tool_output
from context_engine.retrieval import Document, SearchResult
from context_engine.retrieval.evidence_evaluation import EvidenceSpan, _result_spans, _union_length


class EvidenceSelectionError(ValueError):
    """Invalid configuration, candidates, provenance, rendering or counting."""


class EvidenceTokenCounter(Protocol):
    model_id: str
    configuration_id: str
    method: str

    def count_tokens(self, text: str) -> int: ...


@dataclass(frozen=True, slots=True)
class EvidenceSelectionConfig:
    token_budget: int
    max_results: int = 5
    max_content_chars: int = 100_000
    overlap_threshold: float | None = 0.8

    def __post_init__(self) -> None:
        for value in (self.token_budget, self.max_results, self.max_content_chars):
            if type(value) is not int or value <= 0:
                raise EvidenceSelectionError(
                    "Budgets and resource limits must be positive integers."
                )
        if self.overlap_threshold is not None and (
            type(self.overlap_threshold) not in (int, float)
            or not isfinite(self.overlap_threshold)
            or not 0 < self.overlap_threshold <= 1
        ):
            raise EvidenceSelectionError("Overlap threshold must be in (0, 1] or disabled.")


@dataclass(frozen=True, slots=True)
class SelectionDiagnostic:
    candidate_id: str
    original_rank: int
    original_score: float
    reason: str
    overlap_fraction: float | None
    provenance_status: str


@dataclass(frozen=True, slots=True)
class EvidenceSelection:
    selected: tuple[SearchResult, ...]
    output: Mapping[str, object]
    rendered: str
    token_count: int
    configuration_id: str
    diagnostics: tuple[SelectionDiagnostic, ...]
    status: str


class EvidenceSelector(Protocol):
    def select(self, query: str, candidates: Sequence[SearchResult]) -> EvidenceSelection: ...


# Serialization is injected by the tool so selected output is exactly what is delivered.
ResultSerializer = Callable[[SearchResult], dict[str, object]]


def comparable_spans(candidate: SearchResult) -> tuple[EvidenceSpan, ...] | None:
    metadata = candidate.document.metadata_as_mapping()
    if not metadata.get("spans") or metadata.get("text_representation") != "extracted_text":
        return None
    try:
        spans = _result_spans(candidate)
    except (ValueError, TypeError) as exc:
        raise EvidenceSelectionError("Malformed canonical candidate provenance.") from exc
    start, end = metadata.get("start_offset"), metadata.get("end_offset")
    if type(start) is not int or type(end) is not int or not 0 <= start < end:
        raise EvidenceSelectionError("Canonical chunks require valid passage offsets.")
    if any(s.start_offset < start or s.end_offset > end for s in spans):
        raise EvidenceSelectionError("Contributing spans exceed the passage offsets.")
    if _union_length([(s.start_offset, s.end_offset) for s in spans]) != end - start:
        return None  # Incomplete coordinates cannot establish reliable redundancy.
    return spans


def overlap_fraction(spans: Sequence[EvidenceSpan], selected: Sequence[EvidenceSpan]) -> float:
    denominator = _union_length([(s.start_offset, s.end_offset) for s in spans])
    intersections = [
        (max(a.start_offset, b.start_offset), min(a.end_offset, b.end_offset))
        for a in spans
        for b in selected
        if (a.source_id, a.content_sha256) == (b.source_id, b.content_sha256)
        and max(a.start_offset, b.start_offset) < min(a.end_offset, b.end_offset)
    ]
    return _union_length(intersections) / denominator


class RankedEvidenceSelector:
    def __init__(
        self,
        config: EvidenceSelectionConfig,
        counter: EvidenceTokenCounter,
        serializer: ResultSerializer,
    ) -> None:
        self.config, self.counter, self.serializer = config, counter, serializer
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (counter.model_id, counter.configuration_id, counter.method)
        ):
            raise EvidenceSelectionError("An identified answering-model counter is required.")
        self.configuration_id = sha256(
            render_tool_output(
                {"selection": asdict(config), "counter": counter.configuration_id}
            ).encode()
        ).hexdigest()

    def _render(
        self, query: str, results: list[dict[str, object]]
    ) -> tuple[dict[str, object], str, int]:
        output: dict[str, object] = {
            "query": query,
            "result_count": len(results),
            "results": results,
        }
        try:
            rendered = render_tool_output(output)
            count = self.counter.count_tokens(rendered)
        except Exception as exc:
            raise EvidenceSelectionError("Evidence rendering or token counting failed.") from exc
        if type(count) is not int or count < 0:
            raise EvidenceSelectionError("Counter must return a nonnegative integer.")
        return output, rendered, count

    def select(self, query: str, candidates: Sequence[SearchResult]) -> EvidenceSelection:
        if not isinstance(query, str) or not query.strip():
            raise EvidenceSelectionError("Query must be nonblank.")
        # Validate all records before exclusions, including conflicts too late to fit.
        seen: dict[str, SearchResult] = {}
        prepared = []
        for candidate in candidates:
            if (
                not isinstance(candidate, SearchResult)
                or not isinstance(candidate.document, Document)
                or not isinstance(candidate.document.content, str)
                or not candidate.document.content.strip()
            ):
                raise EvidenceSelectionError("Expected typed candidates with nonblank content.")
            identity = candidate.document.document_id
            if (
                not isinstance(identity, str)
                or not identity.strip()
                or type(candidate.score) not in (int, float)
                or not isfinite(candidate.score)
            ):
                raise EvidenceSelectionError("Candidate identity and finite score are required.")
            previous = seen.get(identity)
            if previous is not None and previous.document != candidate.document:
                raise EvidenceSelectionError("Conflicting records for the same chunk identity.")
            seen[identity] = candidate
            try:
                serialized = self.serializer(candidate)
            except Exception as exc:
                raise EvidenceSelectionError("Candidate serialization failed.") from exc
            if serialized.get("content") != candidate.document.content or serialized.get(
                "content_truncated"
            ):
                raise EvidenceSelectionError("Serializer must preserve whole passages.")
            prepared.append((candidate, serialized, comparable_spans(candidate)))
        output, rendered, count = self._render(query, [])
        if count > self.config.token_budget:
            raise EvidenceSelectionError("Even the empty evidence envelope exceeds the budget.")
        selected: list[SearchResult] = []
        serialized_results: list[dict[str, object]] = []
        covered: list[EvidenceSpan] = []
        encountered: set[str] = set()
        diagnostics = []
        for rank, (candidate, serialized, spans) in enumerate(prepared, 1):
            identity = candidate.document.document_id
            fraction = overlap_fraction(spans, covered) if spans is not None else None
            reason = "selected"
            if identity in encountered:
                reason = "duplicate_identity"
            elif len(candidate.document.content) > self.config.max_content_chars:
                reason = "content_resource_limit"
            elif len(selected) >= self.config.max_results:
                reason = "result_limit"
            elif (
                fraction is not None
                and self.config.overlap_threshold is not None
                and fraction >= self.config.overlap_threshold
            ):
                reason = "source_overlap"
            else:
                trial_output, trial_rendered, trial_count = self._render(
                    query, serialized_results + [serialized]
                )
                if trial_count > self.config.token_budget:
                    _, _, alone_count = self._render(query, [serialized])
                    reason = (
                        "oversized"
                        if alone_count > self.config.token_budget
                        else "remaining_budget"
                    )
                else:
                    selected.append(candidate)
                    serialized_results.append(serialized)
                    output, rendered, count = trial_output, trial_rendered, trial_count
                    covered.extend(spans or ())
            encountered.add(identity)
            diagnostics.append(
                SelectionDiagnostic(
                    identity,
                    rank,
                    candidate.score,
                    reason,
                    fraction,
                    "comparable" if spans is not None else "uncomparable_retained",
                )
            )
        status = "selected" if selected else "no_candidates" if not candidates else "no_fit"
        return EvidenceSelection(
            tuple(selected),
            output,
            rendered,
            count,
            self.configuration_id,
            tuple(diagnostics),
            status,
        )
