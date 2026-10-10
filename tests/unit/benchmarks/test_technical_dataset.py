"""Dataset integrity, independent split units, alternatives, and uncertainty."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from benchmarks.technical_dataset import (
    DEFAULT_TECHNICAL_DATASET,
    AnswerRequirement,
    TechnicalQuery,
    dataset_summary,
    grouped_interval,
    load_technical_dataset,
    measure_evidence,
)
from context_engine.retrieval.evidence_evaluation import EvidenceItem, EvidenceSpan
from tests.unit.retrieval.test_evidence_selection import candidate


def test_pinned_broader_corpus_and_review_status() -> None:
    dataset = load_technical_dataset()
    summary = dataset_summary(dataset)
    assert summary["source_count"] == 29 and summary["query_count"] == 124
    assert summary["independently_approved"] == 0
    assert dataset.corpus.dataset_id != "m5-evidence-v1"
    assert any(len(q.requirements) > 1 for q in dataset.queries)
    assert any(len(r.alternatives) > 1 for q in dataset.queries for r in q.requirements)
    assert sum(not q.answerable for q in dataset.queries) == 12
    assert any(s.provenance.format.value == "pdf" for s in dataset.corpus.processed_sources)


@pytest.mark.parametrize(
    "mutation",
    [
        "hash",
        "coordinate",
        "duplicate_text",
        "group",
        "review",
        "answerability",
        "alternative",
        "canonical",
    ],
)
def test_invalid_annotations_rejected(tmp_path: Path, mutation: str) -> None:
    raw = json.loads(DEFAULT_TECHNICAL_DATASET.read_text())
    for source in raw["sources"]:
        target = tmp_path / source["path"]
        target.write_bytes((DEFAULT_TECHNICAL_DATASET.parent / source["path"]).read_bytes())
    first = raw["queries"][0]
    if mutation == "hash":
        raw["sources"][0]["content_sha256"] = "0" * 64
    if mutation == "coordinate":
        first["evidence"][0]["spans"][0]["end_offset"] = 9999999
    if mutation == "duplicate_text":
        raw["queries"][1]["text"] = first["text"].upper()
    if mutation == "group":
        raw["queries"][0]["split"] = "held_out"
    if mutation == "review":
        first["review"]["status"] = "approved"
    if mutation == "answerability":
        first["answerable"] = False
    if mutation == "alternative":
        first["requirements"][0]["alternatives"] = []
    if mutation == "canonical":
        first["requirements"][0]["alternatives"][0]["evidence_id"] = "changed"
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError):
        load_technical_dataset(path)


def test_alternatives_complete_independently_and_no_partial_union() -> None:
    c = candidate(text="x" * 10, start=0)
    meta = c.document.metadata_as_mapping()
    source, revision = meta["source_id"], meta["content_sha256"]

    assert isinstance(source, str) and isinstance(revision, str)

    def span(a: int, b: int) -> EvidenceSpan:
        return EvidenceSpan(source, revision, a, b)

    requirement = AnswerRequirement(
        "fact",
        "reference",
        (
            EvidenceItem("one", (span(0, 20),)),
            EvidenceItem("two", (span(20, 40),)),
        ),
    )
    q = TechnicalQuery(
        "q", "question", "development", "topic", "multi_span", (requirement,), "draft"
    )
    other = candidate(identity="second", text="x" * 10, start=20, end=30)
    result = measure_evidence([c, other], q)
    assert result["recall"] == 0 and result["coverage"]["fact"] == 0.5
    complete = candidate(text="x" * 20, start=20, end=40)
    assert measure_evidence([complete], q)["all_required"]
    assert measure_evidence([], replace(q, requirements=()))["recall"] is None


def test_group_bootstrap_is_reproducible_and_paired() -> None:
    values = [("a", 0.0), ("a", 1.0), ("b", 1.0)]
    assert grouped_interval(values) == grouped_interval(values)
    assert grouped_interval(values)["groups"] == 2
    assert grouped_interval([("a", 0.0), ("b", 0.0)])["interval_95"] == [0.0, 0.0]
    assert grouped_interval([])["estimate"] is None
    with pytest.raises(ValueError):
        grouped_interval([("a", float("nan"))])
    with pytest.raises(ValueError):
        grouped_interval(values, repetitions=1)


def test_published_pdf_diagnostic_pins_layout_and_canonical_spans() -> None:
    path = DEFAULT_TECHNICAL_DATASET.parent.parent / "technical-pdf-v1/dataset.json"
    dataset = load_technical_dataset(path)
    raw = json.loads(path.read_text())
    assert len(dataset.corpus.sources) == 2 and len(dataset.queries) == 12
    assert all(s["provenance"] == "public-published-layout-excerpt" for s in raw["sources"])
    assert all(len(s["upstream_archive_sha256"]) == 64 for s in raw["sources"])
    assert {q.split for q in dataset.queries} == {"development", "held_out"}
    assert all(q.answerable and q.review_status == "draft" for q in dataset.queries)
    assert {s.provenance.format.value for s in dataset.corpus.processed_sources} == {"pdf"}
