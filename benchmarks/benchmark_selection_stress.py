"""Authored fixed-ranking overlap diagnostics, separate from population quality."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from benchmarks.benchmark_rag_ablation import ablate, save_candidate
from benchmarks.evaluation_artifacts import write_artifact
from benchmarks.technical_dataset import AnswerRequirement, TechnicalQuery, load_technical_dataset
from context_engine.models.evidence_counting import QwenEvidenceTokenCounter
from context_engine.retrieval import Document, SearchResult
from context_engine.retrieval.evidence_evaluation import EvidenceItem, EvidenceSpan


def controlled_cases() -> list[tuple[TechnicalQuery, tuple[SearchResult, ...]]]:
    dataset = load_technical_dataset()
    source = next(
        s
        for s in dataset.corpus.processed_sources
        if s.provenance.source_id == "stress:retry-new.md"
    )
    text = source.text
    identity, revision = source.provenance.source_id, source.provenance.content_sha256
    heading_end = text.index("\n")
    fact_start = text.index("JN-481")
    requirements = tuple(
        AnswerRequirement(
            name,
            text[start:end],
            (EvidenceItem(name, (EvidenceSpan(identity, revision, start, end),)),),
        )
        for name, start, end in (
            ("revision", 0, heading_end),
            ("retry-policy", fact_start, len(text.rstrip())),
        )
    )
    cases = {
        "exact-duplicate": ((0, len(text)), (0, len(text))),
        "high-overlap-new-fact": ((0, len(text) - 20), (10, len(text))),
        "complementary": ((0, fact_start), (fact_start, len(text))),
    }
    output = []
    for case, offsets in cases.items():
        query = TechnicalQuery(
            case,
            "Which revision is this retry policy and how many JN-481 retries precede escalation?",
            "development",
            "controlled-overlap-diagnostic",
            "authored-selection-stress",
            requirements,
            "draft",
        )
        candidates = tuple(
            SearchResult(
                Document.from_mapping(
                    document_id=f"controlled:{case}:{i}",
                    content=text[start:end],
                    metadata={
                        "source_id": identity,
                        "content_sha256": revision,
                        "text_representation": "extracted_text",
                        "start_offset": start,
                        "end_offset": end,
                        "spans": [
                            {
                                "location": {
                                    "start_offset": start,
                                    "end_offset": end,
                                    "representation": "extracted_text",
                                }
                            }
                        ],
                    },
                ),
                1.0 - i * 0.1,
            )
            for i, (start, end) in enumerate(offsets)
        )
        output.append((query, candidates))
    return output


def run(counter: Any) -> dict[str, Any]:
    cases = controlled_cases()
    return {
        "schema_version": "controlled-selection-stress-v1",
        "interpretation": (
            "Authored canonical overlapping spans with fixed synthetic ranking, not embedding "
            "retrieval or production-frequency evidence. Correlated three-case diagnostic."
        ),
        "counter_id": counter.configuration_id,
        "counting_method": counter.method,
        "runtime_metrics": "deferred-to-80",
        "saved_candidates": {q.query_id: [save_candidate(r) for r in c] for q, c in cases},
        "queries": [
            ablate(q, candidates, counter, budget=2048, threshold=t, include_diagnostics=False)
            for q, candidates in cases
            for t in (None, 0.8)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tokenizer-directory", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_artifact(args.output, run(QwenEvidenceTokenCounter(args.tokenizer_directory)))


if __name__ == "__main__":
    main()
