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
from context_engine.retrieval import SearchResult
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


def test_ai_review_preserves_original_corpus_and_does_not_claim_independence() -> None:
    for folder in ("technical-v1", "technical-pdf-v1"):
        directory = DEFAULT_TECHNICAL_DATASET.parent.parent / folder
        before = json.loads((directory / "dataset.json").read_text())
        after = json.loads((directory / "dataset-v2.json").read_text())
        assert before["dataset_id"] != after["dataset_id"]
        assert before["sources"] == after["sources"]
        assert len(before["queries"]) == len(after["queries"])
        for old, new in zip(before["queries"], after["queries"], strict=True):
            assert all(old[k] == new[k] for k in ("query_id", "text", "group", "split"))
            assert old["review"] == new["review"]
            assert new["ai_review"]["status"] == "reviewed"
            assert new["ai_review"]["reviewer_kind"] == "ai-self-review"
        assert (
            dataset_summary(load_technical_dataset(directory / "dataset-v2.json"))[
                "independently_approved"
            ]
            == 0
        )


def test_named_api_evidence_needs_identity_and_actual_behaviour() -> None:
    dataset = load_technical_dataset()
    query = next(q for q in dataset.queries if q.query_id == "json-dumps")
    declaration, behaviour = query.requirements[0].alternatives[0].spans
    source = next(
        s
        for s in dataset.corpus.processed_sources
        if s.provenance.source_id == declaration.source_id
    )

    def passage(span: EvidenceSpan) -> SearchResult:
        return candidate(
            start=span.start_offset,
            end=span.end_offset,
            identity=str(span.start_offset),
            source=span.source_id,
            revision=span.content_sha256,
            text=source.text[span.start_offset : span.end_offset],
        )

    # A description omitting which API it describes cannot answer "which function".
    description = passage(behaviour)
    identity = passage(declaration)
    assert not measure_evidence([description], query)["all_required"]
    assert measure_evidence([identity, description], query)["all_required"]


def test_review_fixes_missing_contracts_and_wrong_pdf_error() -> None:
    dataset = load_technical_dataset()
    sources = {s.provenance.source_id: s.text for s in dataset.corpus.processed_sources}
    queries = {q.query_id: q for q in dataset.queries}

    def excerpts(query: TechnicalQuery) -> str:
        return "\n".join(
            sources[s.source_id][s.start_offset : s.end_offset]
            for r in query.requirements
            for a in r.alternatives
            for s in a.spans
        )

    assert ".read()" in excerpts(queries["json-load"])
    assert ".write()" not in excerpts(queries["json-load"])
    assert "responsible" in excerpts(queries["tempfile-mkstemp"])
    assert "permission" in excerpts(queries["shutil-copy"])
    assert "unrecognized arguments" in excerpts(queries["argparse-parse_known_args"])
    path = DEFAULT_TECHNICAL_DATASET.parent.parent / "technical-pdf-v1/dataset-v2.json"
    pdf = load_technical_dataset(path)
    sources = {s.provenance.source_id: s.text for s in pdf.corpus.processed_sources}
    count = next(q for q in pdf.queries if q.query_id == "pdf-argparse-count")
    assert len(count.requirements) == 2
    assert "'NoneType' and 'int'" in excerpts(count)
    assert "unsupported operand type(s) for **" not in excerpts(count)


def test_review_packet_shows_canonical_text_and_pending_human_review() -> None:
    from benchmarks.review_rag_dataset import review_packet

    packet = review_packet()
    assert "Labelled source text:" in packet
    assert "Surrounding canonical source context:" in packet
    assert "Independent human approval remains pending" in packet
    assert "Which json function returns a JSON string rather than writing to a stream?" in packet


def test_answer_evidence_replay_preserves_actual_observations(tmp_path: Path) -> None:
    from benchmarks.evaluation_artifacts import read_artifact, write_artifact
    from benchmarks.replay_answer_evidence import replay

    original_path = (
        DEFAULT_TECHNICAL_DATASET.parents[3] / "results/technical-v1-answers-qwen-05b.json.gz"
    )
    original = read_artifact(original_path)
    updated = replay(original_path, DEFAULT_TECHNICAL_DATASET)
    assert updated["run_status"] == original["run_status"] == "interrupted"
    assert updated["planned_query_ids"] == original["planned_query_ids"]
    assert updated["not_run_query_ids"] == original["not_run_query_ids"]
    assert updated["answering_configuration"] == original["answering_configuration"]
    assert not updated["label_replay"]["live_inference"]
    assert updated["review_summary"] is None
    for before, after in zip(original["queries"], updated["queries"], strict=True):
        assert all(
            before[k] == after[k]
            for k in ("answer", "outcome", "provider_requests", "tool_results", "tool_traces")
        )
        assert after["review"]["status"] == "pending"
    original["queries"][0]["interactions"][0]["request"]["messages"][-1]["content"] = "changed"
    corrupt = tmp_path / "changed.json"
    write_artifact(corrupt, original)
    with pytest.raises(ValueError, match="Changed question"):
        replay(corrupt, DEFAULT_TECHNICAL_DATASET)
