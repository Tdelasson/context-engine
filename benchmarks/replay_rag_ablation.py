"""Recount frozen candidate artifacts without retrieval/model inference or label tuning."""

import argparse
from pathlib import Path
from typing import Any

from benchmarks.benchmark_rag_ablation import ablate, aggregate, paired_comparisons
from benchmarks.evaluation_artifacts import read_artifact, write_artifact
from benchmarks.technical_dataset import dataset_summary, load_evaluation_dataset
from context_engine.models.evidence_counting import QwenEvidenceTokenCounter
from context_engine.retrieval import Document, SearchResult
from context_engine.retrieval.diagnostics import RetrievalStageDiagnostic


def replay(source: Path, dataset_path: Path, tokenizer_directory: str) -> dict[str, Any]:
    output = read_artifact(source)
    dataset = load_evaluation_dataset(dataset_path)
    queries = {q.query_id: q for q in dataset.queries}
    counter = QwenEvidenceTokenCounter(tokenizer_directory)
    if counter.configuration_id != output["counter_id"]:
        raise ValueError("Replay requires the same identified tokenizer.")
    rows = []
    for original in output["queries"]:
        query = queries[original["query_id"]]
        if original["selected_output"]["query"] != query.text:
            raise ValueError("Changed query text requires new retrieval, not candidate replay.")
        candidates = tuple(
            SearchResult(
                Document.from_mapping(**c["document"]),
                c["score"],
                diagnostics=tuple(RetrievalStageDiagnostic(**d) for d in c["diagnostics"]),
            )
            for c in output["saved_candidates"][original["path"] + ":" + query.query_id]
        )
        revisions = {
            s.provenance.source_id: s.provenance.content_sha256
            for s in dataset.corpus.processed_sources
        }
        if any(
            c.document.metadata_as_mapping().get("content_sha256")
            != revisions.get(str(c.document.metadata_as_mapping().get("source_id")))
            for c in candidates
        ):
            raise ValueError("Candidate source revisions do not match the replay corpus.")
        row = ablate(
            query,
            candidates,
            counter,
            budget=original["budget"],
            threshold=original["threshold"],
            include_diagnostics=original["include_ranking_diagnostics"],
        )
        if (
            row["selected_ids"] != original["selected_ids"]
            or row["token_count"] != original["token_count"]
        ):
            raise ValueError("Replay changed selected identities or complete serialization count.")
        row["path"] = original["path"]
        rows.append(row)
    output["queries"] = rows
    output["dataset"] = dataset_summary(dataset)
    output["replay"] = {
        "original_dataset_sha256": read_artifact(source)["dataset"]["sha256"],
        "selection_and_tokens_verified": True,
        "note": "Labels/grouping re-evaluated; development choice remains frozen.",
    }
    for name, best in output["chosen_on_development"].items():
        development = [
            r
            for r in rows
            if r["path"] == name
            and r["split"] == "development"
            and r["budget"] == best["budget"]
            and r["threshold"] == best["threshold"]
            and r["include_ranking_diagnostics"] == best["include_ranking_diagnostics"]
        ]
        best.update(aggregate(development))
    # Replay the predeclared 0.8 paired baseline even when dev selected disabled overlap.
    for name, best in output["chosen_on_development"].items():
        for query in dataset.queries:
            if query.split != "held_out":
                continue
            if any(
                r["path"] == name
                and r["query_id"] == query.query_id
                and r["threshold"] == 0.8
                and r["include_ranking_diagnostics"] == best["include_ranking_diagnostics"]
                for r in rows
            ):
                continue
            candidates = tuple(
                SearchResult(
                    Document.from_mapping(**c["document"]),
                    c["score"],
                    diagnostics=tuple(RetrievalStageDiagnostic(**d) for d in c["diagnostics"]),
                )
                for c in output["saved_candidates"][name + ":" + query.query_id]
            )
            row = ablate(
                query,
                candidates,
                counter,
                budget=best["budget"],
                threshold=0.8,
                include_diagnostics=best["include_ranking_diagnostics"],
            )
            row["path"] = name
            rows.append(row)
    output["paired_comparisons"] = paired_comparisons(rows, output["chosen_on_development"])
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--tokenizer-directory", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_artifact(args.output, replay(args.artifact, args.dataset, args.tokenizer_directory))


if __name__ == "__main__":
    main()
