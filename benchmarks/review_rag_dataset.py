"""Render a concrete annotation packet without silently approving authored labels."""

import argparse
from pathlib import Path

from benchmarks.technical_dataset import DEFAULT_TECHNICAL_DATASET, load_technical_dataset


def review_packet(path: Path = DEFAULT_TECHNICAL_DATASET) -> str:
    dataset = load_technical_dataset(path)
    lines = [
        "# English technical-workbench annotation review",
        "",
        f"Dataset SHA-256: `{dataset.corpus.sha256}`",
        "",
        "All annotations are authored drafts. An independent reviewer must check the question, "
        "answerability, required facts, each complete alternative, source revision and offsets, "
        "category and grouping. Check surrounding source context, not just the excerpt. "
        "Record disagreements and resolve them before approval. Do not infer correctness from "
        "a successful loader check or approve unseen questions.",
        "",
        "To approve reviewed labels, set each dataset query review.status to approved and "
        "review.reviewer to your identity. Keep the author identity. Add review notes for disputed "
        "or revised labels. Update the dataset version when facts/splits change; rerun recorded "
        "comparisons against the new manifest hash. No runner auto-approves annotations.",
        "",
    ]
    for query in dataset.queries:
        lines.extend(
            [
                f"## {query.query_id}",
                "",
                f"{query.split} / {query.group} / {query.category} / {query.review_status}",
                "",
                query.text,
                "",
                f"Expected answerable: {query.answerable}",
                "",
            ]
        )
        for fact in query.requirements:
            lines.extend([f"Fact `{fact.requirement_id}`:", "", fact.reference_fact, ""])
            for alternative in fact.alternatives:
                lines.extend(
                    [f"Alternative `{alternative.evidence_id}`:"]
                    + [
                        f"- `{s.source_id}` revision `{s.content_sha256}` "
                        f"extracted-text characters [{s.start_offset}, {s.end_offset})"
                        for s in alternative.spans
                    ]
                    + [""]
                )
        lines.extend(["Review decision / disagreements / resolution: **pending**", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_TECHNICAL_DATASET)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(review_packet(args.dataset))


if __name__ == "__main__":
    main()
