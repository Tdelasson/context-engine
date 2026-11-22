"""Controlled evidence ablations, staged quality and replay artifacts; no load metrics."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from typing import Any

from benchmarks.benchmark_evidence_selection import redundancy
from benchmarks.evaluation_artifacts import write_artifact
from benchmarks.rag_pipeline import indexed_pipeline
from benchmarks.technical_dataset import (
    DEFAULT_TECHNICAL_DATASET,
    TechnicalQuery,
    dataset_summary,
    grouped_interval,
    load_evaluation_dataset,
    measure_evidence,
)
from context_engine.models.evidence_counting import QwenEvidenceTokenCounter
from context_engine.models.tool_serialization import render_tool_output
from context_engine.retrieval import RetrievalRequest, SearchResult
from context_engine.retrieval.evidence_selection import (
    EvidenceSelectionConfig,
    EvidenceTokenCounter,
)
from context_engine.tools.retrieval import SearchDocumentsTool, SearchDocumentsToolConfig


class FrozenRetriever:
    """Replay exact candidates for a single query through the ordinary search tool."""

    def __init__(self, candidates: Sequence[SearchResult]) -> None:
        self.candidates = tuple(candidates)

    def retrieve(self, request: RetrievalRequest) -> Sequence[SearchResult]:
        return self.candidates[: request.top_k]


def selection_tool(
    retriever: Any,
    counter: EvidenceTokenCounter,
    budget: int,
    threshold: float | None,
    include_diagnostics: bool,
) -> SearchDocumentsTool:
    return SearchDocumentsTool(
        retriever,
        config=SearchDocumentsToolConfig(
            top_k=5,
            candidate_limit=20,
            include_ranking_diagnostics=include_diagnostics,
        ),
        selection_config=EvidenceSelectionConfig(
            budget,
            max_results=5,
            max_content_chars=2000,
            overlap_threshold=threshold,
        ),
        evidence_counter=counter,
    )


def ablate(
    query: TechnicalQuery,
    candidates: Sequence[SearchResult],
    counter: EvidenceTokenCounter,
    *,
    budget: int,
    threshold: float | None,
    include_diagnostics: bool,
) -> dict[str, Any]:
    tool = selection_tool(
        FrozenRetriever(candidates), counter, budget, threshold, include_diagnostics
    )
    selector = tool._selector
    assert selector is not None
    chosen = selector.select(query.text, candidates)
    # Cost attribution is sequential whole-envelope marginal counting, not additive fragments.
    empty = {"query": query.text, "result_count": len(chosen.selected), "results": []}
    content_only = {**empty, "results": [{"content": r.document.content} for r in chosen.selected]}
    no_diagnostics_tool = selection_tool(FrozenRetriever(()), counter, budget, threshold, False)
    citations = {
        **empty,
        "results": [
            no_diagnostics_tool._serialize_result(r, preserve_content=True) for r in chosen.selected
        ],
    }
    counts = [
        counter.count_tokens(render_tool_output(o))
        for o in (
            empty,
            content_only,
            citations,
            chosen.output,
        )
    ]
    candidate_metrics = measure_evidence(candidates, query)
    selected_metrics = measure_evidence(chosen.selected, query)
    losses = []
    for requirement in query.requirements:
        key = requirement.requirement_id
        if selected_metrics["coverage"][key] < 1:
            losses.append(
                {
                    "requirement_id": key,
                    "stage": "candidate_missing"
                    if candidate_metrics["coverage"][key] < 1
                    else "selection_exclusion",
                }
            )
    return {
        "query_id": query.query_id,
        "split": query.split,
        "group": query.group,
        "category": query.category,
        "budget": budget,
        "threshold": threshold,
        "include_ranking_diagnostics": include_diagnostics,
        "configuration_id": chosen.configuration_id,
        "token_count": chosen.token_count,
        "stages": {
            "candidates_20": candidate_metrics,
            "ranked_5": measure_evidence(candidates[:5], query),
            "selected": selected_metrics,
        },
        "selected_ids": [r.document.document_id for r in chosen.selected],
        "selected_output": chosen.output,
        "exclusions": [asdict(d) for d in chosen.diagnostics],
        "losses": losses,
        "redundancy": redundancy(chosen.selected),
        "marginal_token_costs": dict(
            zip(
                ("envelope", "passage_content", "citations_and_metadata", "ranking_diagnostics"),
                (counts[0], counts[1] - counts[0], counts[2] - counts[1], counts[3] - counts[2]),
                strict=True,
            )
        ),
    }


def aggregate(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    supported = [r for r in rows if r["stages"]["selected"]["supported"]]
    return {
        "queries": len(rows),
        "supported_queries": len(supported),
        "unsupported_queries": len(rows) - len(supported),
        "categories": dict(Counter(r["category"] for r in rows)),
        "recall": grouped_interval(
            [(r["group"], r["stages"]["selected"]["recall"]) for r in supported]
        ),
        "all_required": grouped_interval(
            [(r["group"], float(r["stages"]["selected"]["all_required"])) for r in supported]
        ),
        "mean_tokens": mean(r["token_count"] for r in rows) if rows else None,
        "loss_stages": dict(Counter(loss["stage"] for r in rows for loss in r["losses"])),
    }


def save_candidate(result: SearchResult) -> dict[str, Any]:
    return {
        "document": {
            "document_id": result.document.document_id,
            "content": result.document.content,
            "metadata": result.document.metadata_as_mapping(),
        },
        "score": result.score,
        "diagnostics": [asdict(d) for d in result.diagnostics],
    }


def run(
    dataset_path: Path,
    embedding_reference: str,
    tokenizer_directory: str,
    *,
    model_id: str = "sentence-transformers/all-MiniLM-L6-v2",
    qdrant_url: str | None = None,
    reranking_reference: str | None = None,
    chunk_tokens: int = 128,
    overlap: int = 16,
    budgets: tuple[int, ...] = (2048, 4096),
) -> dict[str, Any]:
    if not budgets or any(type(b) is not int or b <= 0 for b in budgets):
        raise ValueError("Positive predeclared budgets required.")
    dataset = load_evaluation_dataset(dataset_path)
    counter = QwenEvidenceTokenCounter(tokenizer_directory)
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    saved: dict[str, Any] = {}
    chosen: dict[str, Any] = {}
    with indexed_pipeline(
        dataset.corpus,
        embedding_reference,
        model_id=model_id,
        chunk_tokens=chunk_tokens,
        overlap=overlap,
        qdrant_url=qdrant_url,
        reranking_reference=reranking_reference,
    ) as (paths, configuration):
        for name, retriever in paths.items():
            frozen = {}
            for query in dataset.queries:
                try:
                    frozen[query.query_id] = tuple(
                        retriever.retrieve(RetrievalRequest(query.text, 20))
                    )
                except Exception as exc:
                    # Preserve failed retrieval as empty coverage; never drop its denominator.
                    frozen[query.query_id] = ()
                    failures.append(
                        {
                            "path": name,
                            "query_id": query.query_id,
                            "error_type": type(exc).__name__,
                            "message": str(exc),
                        }
                    )
                saved[name + ":" + query.query_id] = [
                    save_candidate(r) for r in frozen[query.query_id]
                ]
            configurations = [
                (b, t, d) for b in budgets for t in (None, 0.8) for d in (True, False)
            ]
            development = [q for q in dataset.queries if q.split == "development"]
            summaries = []
            for budget, threshold, diagnostics in configurations:
                group = []
                for query in development:
                    row = ablate(
                        query,
                        frozen[query.query_id],
                        counter,
                        budget=budget,
                        threshold=threshold,
                        include_diagnostics=diagnostics,
                    )
                    row["path"] = name
                    rows.append(row)
                    group.append(row)
                summaries.append(
                    {
                        "budget": budget,
                        "threshold": threshold,
                        "include_ranking_diagnostics": diagnostics,
                        **aggregate(group),
                    }
                )
            best = min(
                summaries,
                key=lambda s: (
                    -s["recall"]["estimate"],
                    -s["all_required"]["estimate"],
                    s["mean_tokens"],
                    s["budget"],
                    s["threshold"] is not None,
                    s["include_ranking_diagnostics"],
                ),
            )
            chosen[name] = best
            # Freeze dev choice before opening held-out quality; paired baseline uses same budget.
            for query in (q for q in dataset.queries if q.split == "held_out"):
                for threshold, diagnostics in dict.fromkeys(
                    [
                        (best["threshold"], best["include_ranking_diagnostics"]),
                        (None, best["include_ranking_diagnostics"]),
                        (0.8, best["include_ranking_diagnostics"]),
                        (best["threshold"], not best["include_ranking_diagnostics"]),
                    ]
                ):
                    row = ablate(
                        query,
                        frozen[query.query_id],
                        counter,
                        budget=best["budget"],
                        threshold=threshold,
                        include_diagnostics=diagnostics,
                    )
                    row["path"] = name
                    rows.append(row)
    return {
        "schema_version": "rag-ablation-v1",
        "dataset": dataset_summary(dataset),
        "configuration": configuration,
        "counter_id": counter.configuration_id,
        "counting_method": counter.method,
        "predeclared_budgets": budgets,
        "chosen_on_development": chosen,
        "queries": rows,
        "saved_candidates": saved,
        "paired_comparisons": paired_comparisons(rows, chosen),
        "failures": failures,
        "recommendation": "Provisional: independent label review required before default changes.",
        "runtime_metrics": "Deferred to #80; quality and evidence accounting only.",
    }


def paired_comparisons(rows: list[dict[str, Any]], chosen: dict[str, Any]) -> list[dict[str, Any]]:
    comparisons = []
    for name, best in chosen.items():
        held = [
            r
            for r in rows
            if r["path"] == name and r["split"] == "held_out" and r["budget"] == best["budget"]
        ]
        selected = [
            r
            for r in held
            if r["threshold"] == best["threshold"]
            and r["include_ranking_diagnostics"] == best["include_ranking_diagnostics"]
        ]
        for kind in ("overlap", "rendering"):
            if kind == "overlap":
                left = [
                    r
                    for r in held
                    if r["threshold"] is None
                    and r["include_ranking_diagnostics"] == best["include_ranking_diagnostics"]
                ]
                right = [
                    r
                    for r in held
                    if r["threshold"] == 0.8
                    and r["include_ranking_diagnostics"] == best["include_ranking_diagnostics"]
                ]
            else:
                left = [
                    r
                    for r in held
                    if r["threshold"] == best["threshold"] and r["include_ranking_diagnostics"]
                ]
                right = [
                    r
                    for r in held
                    if r["threshold"] == best["threshold"] and not r["include_ranking_diagnostics"]
                ]
            byid = {r["query_id"]: r for r in left}
            if set(byid) != {r["query_id"] for r in right}:
                raise ValueError("Predeclared held-out paired baseline is missing.")
            comparisons.append(
                {
                    "path": name,
                    "comparison": kind,
                    "held_out_selected": aggregate(selected),
                    "difference_direction": (
                        "overlap-0.8-minus-disabled"
                        if kind == "overlap"
                        else "without-minus-with-ranking-diagnostics"
                    ),
                    "paired_recall_difference": grouped_interval(
                        [
                            (
                                r["group"],
                                r["stages"]["selected"]["recall"]
                                - byid[r["query_id"]]["stages"]["selected"]["recall"],
                            )
                            for r in right
                            if r["stages"]["selected"]["supported"]
                        ]
                    ),
                }
            )
    return comparisons


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_TECHNICAL_DATASET)
    parser.add_argument("--embedding-reference", required=True)
    parser.add_argument("--model-id", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--tokenizer-directory", required=True)
    parser.add_argument("--qdrant-url")
    parser.add_argument("--reranking-reference")
    parser.add_argument("--chunk-tokens", type=int, default=128)
    parser.add_argument("--overlap", type=int, default=16)
    parser.add_argument("--budgets", type=int, nargs="+", default=[2048, 4096])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        output = run(
            args.dataset,
            args.embedding_reference,
            args.tokenizer_directory,
            model_id=args.model_id,
            qdrant_url=args.qdrant_url,
            reranking_reference=args.reranking_reference,
            chunk_tokens=args.chunk_tokens,
            overlap=args.overlap,
            budgets=tuple(args.budgets),
        )
    except Exception as exc:
        output = {"failures": [{"error_type": type(exc).__name__, "message": str(exc)}]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_artifact(args.output, output)
    if output["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
