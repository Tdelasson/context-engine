"""Versioned technical-workbench labels, alternative support, and grouped uncertainty."""

from __future__ import annotations

import json
import random
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from benchmarks.benchmark_chunked_retrieval import EvidenceDataset, load_evidence_dataset
from context_engine.retrieval import SearchResult
from context_engine.retrieval.evidence_evaluation import (
    EvidenceItem,
    EvidenceSpan,
    evaluate_evidence_query,
    validate_evidence,
)

DEFAULT_TECHNICAL_DATASET = Path(__file__).parent / "data/retrieval/technical-v1/dataset.json"


@dataclass(frozen=True)
class AnswerRequirement:
    requirement_id: str
    reference_fact: str
    alternatives: tuple[EvidenceItem, ...]


@dataclass(frozen=True)
class TechnicalQuery:
    query_id: str
    text: str
    split: str
    group: str
    category: str
    requirements: tuple[AnswerRequirement, ...]
    review_status: str

    @property
    def answerable(self) -> bool:
        return bool(self.requirements)


@dataclass(frozen=True)
class TechnicalDataset:
    corpus: EvidenceDataset
    queries: tuple[TechnicalQuery, ...]
    annotation_status: str


def load_technical_dataset(path: Path = DEFAULT_TECHNICAL_DATASET) -> TechnicalDataset:
    """Validate the original integrity contract plus evaluation-only fact/split labels."""
    corpus = load_evidence_dataset(path)
    raw = json.loads(path.read_text())
    if raw.get("schema_version") != "technical-evaluation-v1":
        raise ValueError("Unknown technical dataset schema.")
    sources = {s.provenance.source_id: s for s in corpus.processed_sources}
    groups = {s["source_id"]: s["group"] for s in raw["sources"]}
    queries = []
    seen_text: set[str] = set()
    group_splits: dict[str, str] = {}
    for row in raw["queries"]:
        normalized = re.sub(r"\W+", " ", row["text"].casefold()).strip()
        if normalized in seen_text:
            raise ValueError("Duplicate normalized query text.")
        seen_text.add(normalized)
        if not row["group"].strip() or not row["category"].strip():
            raise ValueError("Queries need nonblank group and category.")
        participating = {row["group"]}
        requirements = []
        for fact in row["requirements"]:
            if not fact["requirement_id"].strip() or not fact["reference_fact"].strip():
                raise ValueError("Requirements need nonblank identity and reference fact.")
            alternatives = tuple(
                EvidenceItem(a["evidence_id"], tuple(EvidenceSpan(**s) for s in a["spans"]))
                for a in fact["alternatives"]
            )
            if not alternatives:
                raise ValueError("Answer requirements need evidence alternatives.")
            validate_evidence(alternatives, sources)
            participating.update(groups[s.source_id] for a in alternatives for s in a.spans)
            requirements.append(
                AnswerRequirement(fact["requirement_id"], fact["reference_fact"], alternatives)
            )
        if len({r.requirement_id for r in requirements}) != len(requirements):
            raise ValueError("Duplicate requirement identity.")
        if type(row["answerable"]) is not bool or row["answerable"] != bool(requirements):
            raise ValueError("Answerability must agree with requirements.")
        # Existing evaluator's canonical label is the first alternative, never their union.
        if row["evidence"] != [r["alternatives"][0] for r in row["requirements"]]:
            raise ValueError("Canonical labels must equal the first alternative of each fact.")
        review = row["review"]
        if review["status"] not in {"draft", "approved"}:
            raise ValueError("Unknown annotation review status.")
        if review["status"] == "approved" and (
            not isinstance(review.get("reviewer"), str)
            or not review["reviewer"].strip()
            or review["reviewer"] == review["author"]
        ):
            raise ValueError("Approved annotations need an independent identified reviewer.")
        for group in participating:
            if group in group_splits and group_splits[group] != row["split"]:
                raise ValueError("Source/topic group crosses development and held-out splits.")
            group_splits[group] = row["split"]
        queries.append(
            TechnicalQuery(
                row["query_id"],
                row["text"],
                row["split"],
                row["group"],
                row["category"],
                tuple(requirements),
                review["status"],
            )
        )
    return TechnicalDataset(corpus, tuple(queries), raw["annotation_status"])


def measure_evidence(results: Sequence[SearchResult], query: TechnicalQuery) -> dict[str, Any]:
    """A fact completes if any alternative completes; alternatives are never combined."""
    if not query.requirements:
        return {"supported": False, "recall": None, "all_required": None, "coverage": {}}
    coverage = {}
    for fact in query.requirements:
        coverage[fact.requirement_id] = max(
            evaluate_evidence_query(
                results, (alternative,), k_values=(max(1, len(results)),)
            ).coverage_at_k[max(1, len(results))][alternative.evidence_id]
            for alternative in fact.alternatives
        )
    recall = mean(float(c == 1) for c in coverage.values())
    return {
        "supported": True,
        "recall": recall,
        "all_required": recall == 1,
        "coverage": coverage,
    }


def grouped_interval(
    observations: Sequence[tuple[str, float]],
    *,
    seed: int = 77,
    repetitions: int = 1000,
) -> dict[str, Any]:
    """Percentile source/topic-cluster bootstrap; paired differences use the same groups."""
    if type(repetitions) is not int or repetitions < 100:
        raise ValueError("At least 100 bootstrap replicates are required.")
    grouped: dict[str, list[float]] = defaultdict(list)
    for group, value in observations:
        if not group or not isinstance(value, (int, float)) or not -1 <= value <= 1:
            raise ValueError("Bootstrap observations need a group and bounded finite value.")
        grouped[group].append(value)
    if not observations:
        return {"estimate": None, "interval_95": None, "queries": 0, "groups": 0}
    keys = sorted(grouped)
    samples = []
    rng = random.Random(seed)
    for _ in range(repetitions):
        sampled = rng.choices(keys, k=len(keys))
        samples.append(mean(value for key in sampled for value in grouped[key]))
    samples.sort()
    return {
        "estimate": mean(value for _, value in observations),
        "interval_95": [samples[int(repetitions * 0.025)], samples[int(repetitions * 0.975)]],
        "queries": len(observations),
        "groups": len(keys),
        "seed": seed,
        "method": "source/topic-cluster-percentile-bootstrap",
        "warning": "Fewer than 10 independent groups; interval is exploratory."
        if len(keys) < 10
        else "Conditional on this corpus and annotation quality; not population certification.",
    }


def dataset_summary(dataset: TechnicalDataset) -> Mapping[str, object]:
    return {
        "dataset_id": dataset.corpus.dataset_id,
        "sha256": dataset.corpus.sha256,
        "source_count": len(dataset.corpus.sources),
        "query_count": len(dataset.queries),
        "annotation_status": dataset.annotation_status,
        "independently_approved": sum(q.review_status == "approved" for q in dataset.queries),
        "categories": dict(Counter((q.split + ":" + q.category) for q in dataset.queries)),
        "answerability": dict(
            Counter((q.split + ":" + str(q.answerable)) for q in dataset.queries)
        ),
    }


def load_evaluation_dataset(path: Path) -> TechnicalDataset:
    """Keep the untouched #64 diagnostic suite usable by the new shared runners."""
    raw = json.loads(path.read_text())
    if raw.get("schema_version") == "technical-evaluation-v1":
        return load_technical_dataset(path)
    corpus = load_evidence_dataset(path)
    sources = {s.provenance.source_id: s for s in corpus.processed_sources}
    return TechnicalDataset(
        corpus,
        tuple(
            TechnicalQuery(
                q.query_id,
                q.text,
                q.split,
                "legacy-diagnostic-correlated",
                "legacy_diagnostic",
                tuple(
                    AnswerRequirement(
                        item.evidence_id,
                        "\n".join(
                            sources[s.source_id].text[s.start_offset : s.end_offset]
                            for s in item.spans
                        ),
                        (item,),
                    )
                    for item in q.evidence
                ),
                "legacy",
            )
            for q in corpus.queries
        ),
        "legacy-diagnostic-not-independent-validation",
    )
