"""Paired stage comparisons across pinned compatible chunk/model/path experiments."""

import argparse
from pathlib import Path
from typing import Any

from benchmarks.evaluation_artifacts import read_artifact, write_artifact
from benchmarks.technical_dataset import grouped_interval


def chosen_held_out(artifact: dict[str, Any], path: str) -> dict[str, dict[str, Any]]:
    config = artifact["chosen_on_development"][path]
    return {
        r["query_id"]: r
        for r in artifact["queries"]
        if r["path"] == path
        and r["split"] == "held_out"
        and r["budget"] == config["budget"]
        and r["threshold"] == config["threshold"]
        and r["include_ranking_diagnostics"] == config["include_ranking_diagnostics"]
    }


def compare(
    left: dict[str, Any], right: dict[str, Any], left_path: str, right_path: str, *, hypothesis: str
) -> dict[str, Any]:
    if not hypothesis.strip():
        raise ValueError("An explicit comparison hypothesis is required.")
    if left["dataset"]["sha256"] != right["dataset"]["sha256"]:
        raise ValueError("Paired comparisons require the exact same dataset revision.")
    a, b = chosen_held_out(left, left_path), chosen_held_out(right, right_path)
    if not a or a.keys() != b.keys():
        raise ValueError("Paired held-out query sets must match exactly.")
    differences = {}
    for stage in ("candidates_20", "ranked_5", "selected"):
        if any(a[k]["stages"][stage]["supported"] != b[k]["stages"][stage]["supported"] for k in a):
            raise ValueError("Answerability differs between supposedly identical labels.")
        differences[stage] = grouped_interval(
            [
                (
                    a[key]["group"],
                    b[key]["stages"][stage]["recall"] - a[key]["stages"][stage]["recall"],
                )
                for key in a
                if a[key]["stages"][stage]["supported"]
            ]
        )
    return {
        "hypothesis": hypothesis,
        "difference_direction": "right-minus-left",
        "left_path": left_path,
        "right_path": right_path,
        "left_configuration": left["configuration"],
        "right_configuration": right["configuration"],
        "left_selected_config": left["chosen_on_development"][left_path],
        "right_selected_config": right["chosen_on_development"][right_path],
        "paired_recall_differences": differences,
        "regressions": [
            key
            for key in a
            if a[key]["stages"]["selected"]["supported"]
            and b[key]["stages"]["selected"]["recall"] < a[key]["stages"]["selected"]["recall"]
        ],
        "interpretation": (
            "Candidates/ranked prefixes compare upstream quality. Selected-stage "
            "differences also include independently dev-selected budget policies; "
            "use identical-candidate equal-budget ablations for causal selection claims."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left", type=Path, required=True)
    parser.add_argument("--right", type=Path, required=True)
    parser.add_argument("--left-path", default="dense")
    parser.add_argument("--right-path", default="dense")
    parser.add_argument("--hypothesis", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_artifact(
        args.output,
        compare(
            read_artifact(args.left),
            read_artifact(args.right),
            args.left_path,
            args.right_path,
            hypothesis=args.hypothesis,
        ),
    )


if __name__ == "__main__":
    main()
