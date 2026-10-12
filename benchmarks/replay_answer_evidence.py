"""Regrade saved answer-path evidence after label repair; never regenerate or score answers."""

import argparse
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

from benchmarks.evaluation_artifacts import read_artifact, write_artifact
from benchmarks.technical_dataset import dataset_summary, load_technical_dataset, measure_evidence
from context_engine.retrieval import Document, SearchResult


def replay(artifact: Path, dataset_path: Path) -> dict[str, Any]:
    output = read_artifact(artifact)
    previous_dataset = deepcopy(output["dataset"])
    dataset = load_technical_dataset(dataset_path)
    queries = {q.query_id: q for q in dataset.queries}
    revisions = {
        s.provenance.source_id: s.provenance.content_sha256
        for s in dataset.corpus.processed_sources
    }
    for row in output["queries"]:
        query = queries[row["query_id"]]
        messages = row["interactions"][0]["request"]["messages"]
        users = [m["content"] for m in messages if m["role"] == "user"]
        if not users or users[-1] != query.text:
            raise ValueError("Changed question requires new execution, not evidence replay.")
        if row["split"] != query.split or row["group"] != query.group:
            raise ValueError("Replay must preserve original split and grouping.")
        candidates = []
        for call in row["retrieval_calls"]:
            for saved in call["candidates"]:
                document = Document.from_mapping(**saved["document"])
                metadata = document.metadata_as_mapping()
                if metadata.get("content_sha256") != revisions.get(str(metadata.get("source_id"))):
                    raise ValueError("Candidate revision differs from the reviewed corpus.")
                candidates.append(SearchResult(document, saved["score"]))
        by_id = {r.document.document_id: r for r in candidates}
        selected = []
        for tool in row["tool_results"]:
            if tool["status"] != "success":
                continue
            result = tool["output"]
            mapping = result if isinstance(result, dict) else dict(result)
            for item in mapping["results"]:
                candidate = by_id[item["document_id"]]
                if (
                    item["content_truncated"]
                    or candidate.document.content != item["content"]
                    or candidate.document.metadata_as_mapping() != item["metadata"]
                ):
                    raise ValueError("Replay requires the actual complete delivered passages.")
                selected.append(candidate)
        row["stages"] = {
            "retrieved": measure_evidence(candidates, query),
            "selected": measure_evidence(selected, query),
        }
        row["reference_facts"] = {r.requirement_id: r.reference_fact for r in query.requirements}
        # Previous answer judgments cannot silently certify changed reference requirements.
        row["previous_label_review"] = deepcopy(row["review"])
        row["review"].update(
            status="pending",
            reviewer=None,
            requirements={r.requirement_id: None for r in query.requirements},
            factual_correctness=None,
            unsupported_claims=None,
            citation_support=None,
            abstained=None,
            notes="Evidence labels revised; answer review remains pending.",
        )
    output["dataset"] = dataset_summary(dataset)
    output["review_summary"] = None
    output["label_replay"] = {
        "original_artifact": artifact.name,
        "original_artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
        "previous_dataset": previous_dataset,
        "live_inference": False,
        "answer_quality_scored": False,
        "note": "Only evidence/reference labels regraded; original answers, requests, failures "
        "and incomplete-run status retained. No new held-out validation or provider measurements.",
    }
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_artifact(args.output, replay(args.artifact, args.dataset))


if __name__ == "__main__":
    main()
