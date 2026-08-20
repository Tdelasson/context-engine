from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict, cast

DATASET_PATH = (
    Path(__file__).resolve().parents[3]
    / "benchmarks"
    / "data"
    / "retrieval"
    / "m4-retrieval-dataset-v1.json"
)


class DatasetDocument(TypedDict):
    document_id: str
    content: str
    metadata: dict[str, Any]


class DatasetQuery(TypedDict):
    query_id: str
    text: str
    intent: str


class RelevanceJudgment(TypedDict):
    query_id: str
    relevant_document_ids: list[str]


class BenchmarkDataset(TypedDict):
    dataset_id: str
    version: str
    description: str
    documents: list[DatasetDocument]
    queries: list[DatasetQuery]
    relevance_judgments: list[RelevanceJudgment]


def _load_dataset() -> BenchmarkDataset:
    with DATASET_PATH.open("r", encoding="utf-8") as dataset_file:
        return cast(BenchmarkDataset, json.load(dataset_file))


def test_dataset_has_expected_top_level_sections() -> None:
    dataset = _load_dataset()

    assert dataset["dataset_id"] == "m4-retrieval-benchmark-v1"
    assert dataset["version"] == "1.0.0"
    assert isinstance(dataset["documents"], list)
    assert isinstance(dataset["queries"], list)
    assert isinstance(dataset["relevance_judgments"], list)


def test_document_ids_are_unique() -> None:
    dataset = _load_dataset()

    document_ids = [document["document_id"] for document in dataset["documents"]]
    assert len(document_ids) == len(set(document_ids))


def test_query_ids_are_unique() -> None:
    dataset = _load_dataset()

    query_ids = [query["query_id"] for query in dataset["queries"]]
    assert len(query_ids) == len(set(query_ids))


def test_every_query_has_exactly_one_judgment_entry() -> None:
    dataset = _load_dataset()

    query_ids = {query["query_id"] for query in dataset["queries"]}
    judged_query_ids = {judgment["query_id"] for judgment in dataset["relevance_judgments"]}

    assert judged_query_ids == query_ids


def test_relevance_judgments_reference_only_existing_documents() -> None:
    dataset = _load_dataset()

    document_ids = {document["document_id"] for document in dataset["documents"]}
    for judgment in dataset["relevance_judgments"]:
        for document_id in judgment["relevant_document_ids"]:
            assert document_id in document_ids


def test_dataset_has_single_and_multi_relevance_queries() -> None:
    dataset = _load_dataset()

    cardinalities = [
        len(judgment["relevant_document_ids"]) for judgment in dataset["relevance_judgments"]
    ]
    assert any(count == 1 for count in cardinalities)
    assert any(count > 1 for count in cardinalities)


def test_dataset_size_targets_are_in_expected_range() -> None:
    dataset = _load_dataset()

    assert 30 <= len(dataset["documents"]) <= 50
    assert 15 <= len(dataset["queries"]) <= 25
    assert len(dataset["relevance_judgments"]) == len(dataset["queries"])


def test_dataset_contains_no_model_specific_vectors_or_scores() -> None:
    dataset = _load_dataset()

    assert "vectors" not in dataset
    for section_name in ("documents", "queries", "relevance_judgments"):
        for entry in dataset[section_name]:
            assert "vector" not in entry
            assert "score" not in entry
