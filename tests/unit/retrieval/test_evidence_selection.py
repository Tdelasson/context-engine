"""Selection invariants with controlled non-inference counters and canonical locations."""

from dataclasses import replace
from types import SimpleNamespace
from typing import cast

import pytest

from context_engine.models.tool_serialization import model_visible_tool_output, render_tool_output
from context_engine.retrieval import Document, SearchResult
from context_engine.retrieval.evidence_selection import (
    EvidenceSelectionConfig,
    EvidenceSelectionError,
    RankedEvidenceSelector,
    comparable_spans,
)
from context_engine.tools.retrieval import SearchDocumentsTool, SearchDocumentsToolConfig
from context_engine.tools.runtime import ToolInvocation


class Counter:
    model_id = "fixture-answerer"
    configuration_id = "utf8-fixture-v1"
    method = "test-only-utf8-bytes"

    def count_tokens(self, text: str) -> int:
        return len(text.encode())


def candidate(
    start: int = 0,
    end: int = 10,
    *,
    identity: str = "a",
    source: str = "s",
    revision: str = "a" * 64,
    text: str | None = None,
) -> SearchResult:
    return SearchResult(
        Document.from_mapping(
            document_id=identity,
            content=text if text is not None else "x" * (end - start),
            metadata={
                "source_id": source,
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
                            "page_number": 1,
                        }
                    }
                ],
            },
        ),
        1.0,
    )


def serialize(result: SearchResult) -> dict[str, object]:
    return {
        "document_id": result.document.document_id,
        "content": result.document.content,
        "content_truncated": False,
        "metadata": result.document.metadata_as_mapping(),
        "score": result.score,
    }


def selector(
    budget: int = 10000,
    threshold: float | None = 0.8,
    counter: Counter | None = None,
    max_results: int = 5,
) -> RankedEvidenceSelector:
    return RankedEvidenceSelector(
        EvidenceSelectionConfig(budget, max_results, overlap_threshold=threshold),
        counter or Counter(),
        serialize,
    )


def test_complete_serialization_exact_boundary_unicode_and_metadata() -> None:
    result = candidate(text='café "quoted" \\ 😀')
    full = selector().select("find Ω", [result])
    assert full.token_count == Counter().count_tokens(render_tool_output(full.output))
    assert full.rendered == render_tool_output(full.output)
    assert full.token_count > len(result.document.content)
    assert selector(full.token_count).select("find Ω", [result]).selected == (result,)
    assert not selector(full.token_count - 1).select("find Ω", [result]).selected
    assert full.output["results"] == [serialize(result)]


def test_oversized_then_later_fitting_and_excluded_spans_do_not_suppress() -> None:
    small = candidate(identity="small")
    budget = selector().select("q", [small]).token_count
    large = candidate(identity="large", text="A" * 10000)
    selection = selector(budget).select("q", [large, small])
    assert selection.selected == (small,)
    assert [d.reason for d in selection.diagnostics] == ["oversized", "selected"]
    assert selection.diagnostics[1].overlap_fraction == 0


def test_duplicate_union_overlap_and_new_evidence() -> None:
    a, b = candidate(0, 10), candidate(10, 20, identity="b")
    covered = candidate(0, 20, identity="union")
    new = candidate(15, 25, identity="new")
    selection = selector().select("q", [a, a, b, covered, new])
    assert selection.selected == (a, b, new)
    assert [d.reason for d in selection.diagnostics] == [
        "selected",
        "duplicate_identity",
        "selected",
        "source_overlap",
        "selected",
    ]
    assert selection.diagnostics[3].overlap_fraction == 1
    assert selection.diagnostics[4].overlap_fraction == 0.5
    assert [d.original_rank for d in selection.diagnostics] == [1, 2, 3, 4, 5]


def test_threshold_boundary_and_disabled_baseline() -> None:
    a, b = candidate(0, 8), candidate(0, 10, identity="b")
    assert selector().select("q", [a, b]).selected == (a,)
    assert selector(threshold=0.81).select("q", [a, b]).selected == (a, b)
    assert selector(threshold=None).select("q", [a, b]).selected == (a, b)


def test_different_source_and_revision_identical_text_remain_eligible() -> None:
    a = candidate()
    b = candidate(identity="b", source="other")
    c = candidate(identity="c", revision="b" * 64)
    assert selector().select("q", [a, b, c]).selected == (a, b, c)


def test_conflicting_identity_fails_even_beyond_result_limit() -> None:
    with pytest.raises(EvidenceSelectionError, match="Conflicting"):
        selector(max_results=1).select("q", [candidate(), candidate(text="changed")])


def test_multispan_page_union_does_not_double_count() -> None:
    result = candidate(0, 20)
    metadata = result.document.metadata_as_mapping()
    metadata["spans"] = [
        {
            "location": {
                "start_offset": start,
                "end_offset": end,
                "representation": "extracted_text",
                "page_number": page,
            }
        }
        for start, end, page in [(0, 12, 1), (8, 20, 2)]
    ]
    result = replace(
        result, document=Document.from_mapping(document_id="a", content="x" * 20, metadata=metadata)
    )
    second = candidate(0, 20, identity="b")
    assert selector().select("q", [result, second]).selected == (result,)
    assert comparable_spans(result)


@pytest.mark.parametrize(
    "metadata",
    [{}, {"text_representation": "bytes"}, {"text_representation": "extracted_text", "spans": []}],
)
def test_missing_or_incompatible_locations_are_uncomparable(metadata: dict[str, object]) -> None:
    a = SearchResult(Document.from_mapping(document_id="a", content="same", metadata=metadata), 1)
    b = replace(a, document=replace(a.document, document_id="b"))
    selection = selector().select("q", [a, b])
    assert selection.selected == (a, b)
    assert selection.diagnostics[1].overlap_fraction is None


def test_incomplete_locations_are_uncomparable_and_zero_length_is_invalid() -> None:
    a = candidate(0, 10)
    metadata = a.document.metadata_as_mapping()
    metadata["end_offset"] = 20
    partial = replace(a, document=replace(a.document, metadata=tuple(metadata.items())))
    assert comparable_spans(partial) is None
    metadata["spans"] = [
        {"location": {"start_offset": 0, "end_offset": 0, "representation": "extracted_text"}}
    ]
    with pytest.raises(EvidenceSelectionError, match="provenance"):
        comparable_spans(replace(a, document=replace(a.document, metadata=tuple(metadata.items()))))


def test_empty_no_fit_and_empty_envelope_failure() -> None:
    assert selector().select("q", []).status == "no_candidates"
    budget = selector().select("q", []).token_count
    assert selector(budget).select("q", [candidate()]).status == "no_fit"
    with pytest.raises(EvidenceSelectionError, match="empty"):
        selector(budget - 1).select("q", [])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"token_budget": True},
        {"token_budget": 0},
        {"max_results": False},
        {"max_content_chars": 0},
        {"overlap_threshold": True},
        {"overlap_threshold": 0},
        {"overlap_threshold": float("nan")},
        {"overlap_threshold": 1.1},
    ],
)
def test_invalid_limits(kwargs: dict[str, object]) -> None:
    with pytest.raises(EvidenceSelectionError):
        EvidenceSelectionConfig(**{"token_budget": 1000, **kwargs})  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [True, -1, 1.5])
def test_malformed_count_result_is_rejected(value: object) -> None:
    counter = Counter()
    counter.count_tokens = lambda text: cast(int, value)  # type: ignore[method-assign]
    with pytest.raises(EvidenceSelectionError, match="nonnegative"):
        selector(counter=counter).select("q", [])


def test_nonadditive_count_uses_complete_output() -> None:
    class Nonadditive(Counter):
        def count_tokens(self, text: str) -> int:
            return 1 if '"result_count": 1' in text else len(text)

    selected = selector(100, counter=Nonadditive()).select("q", [candidate()])
    assert selected.token_count == 1 and len(selected.rendered) > 100


def test_count_failure_and_truncating_serializer_are_explicit() -> None:
    class Broken(Counter):
        def count_tokens(self, text: str) -> int:
            raise RuntimeError("counter offline")

    with pytest.raises(EvidenceSelectionError, match="counting"):
        selector(counter=Broken()).select("q", [])
    truncating = RankedEvidenceSelector(
        EvidenceSelectionConfig(1000),
        Counter(),
        lambda _: {"content": "truncated", "content_truncated": True},
    )
    with pytest.raises(EvidenceSelectionError, match="whole"):
        truncating.select("q", [candidate()])


def test_tool_resource_bounds_and_ui_diagnostics() -> None:
    big, small = candidate(identity="big", text="z" * 100), candidate(identity="small")
    retriever = SimpleNamespace(retrieve=lambda _: [big, small])
    tool = SearchDocumentsTool(
        retriever,
        config=SearchDocumentsToolConfig(1, 20, 2),
        selection_config=EvidenceSelectionConfig(10000),
        evidence_counter=Counter(),
    )
    output = tool.execute(ToolInvocation.from_mapping("search_documents", {"query": "q"}))
    visible = model_visible_tool_output("search_documents", output)
    assert visible["results"] == [tool._serialize_result(small, preserve_content=True)]
    diagnostics = output["selection_diagnostics"]
    assert isinstance(diagnostics, dict)
    assert diagnostics["token_count"] == Counter().count_tokens(render_tool_output(visible))
    assert diagnostics["candidates"][0]["reason"] == "content_resource_limit"
    assert "selection_diagnostics" not in visible


@pytest.mark.parametrize("score", [True, "1", float("inf"), float("nan")])
def test_malformed_candidate_scores_are_explicit(score: object) -> None:
    with pytest.raises(EvidenceSelectionError):
        selector().select("q", [replace(candidate(), score=score)])  # type: ignore[arg-type]


def test_blank_passage_is_rejected() -> None:
    with pytest.raises(EvidenceSelectionError, match="nonblank"):
        selector().select("q", [candidate(text=" ")])


def test_remaining_budget_result_limit_and_original_score() -> None:
    a, b, c = candidate(), candidate(20, 30, identity="b"), candidate(40, 50, identity="c")
    budget = max(selector().select("q", [item]).token_count for item in (a, b))
    selection = selector(budget).select("q", [a, b])
    assert selection.diagnostics[1].reason == "remaining_budget"
    assert selection.diagnostics[1].original_score == b.score
    capped = selector(max_results=1).select("q", [a, b, c])
    assert [d.reason for d in capped.diagnostics] == ["selected", "result_limit", "result_limit"]


def test_configuration_identity_is_stable_and_changes_with_budget() -> None:
    assert selector(1000).configuration_id == selector(1000).configuration_id
    assert selector(1000).configuration_id != selector(1001).configuration_id
    assert selector(threshold=None).configuration_id != selector().configuration_id


def test_malformed_canonical_coordinates_and_serialization_fail_explicitly() -> None:
    result = candidate()
    metadata = result.document.metadata_as_mapping()
    metadata["end_offset"] = 5
    with pytest.raises(EvidenceSelectionError, match="exceed"):
        selector().select(
            "q",
            [replace(result, document=replace(result.document, metadata=tuple(metadata.items())))],
        )
    bad = RankedEvidenceSelector(
        EvidenceSelectionConfig(1000),
        Counter(),
        lambda r: {"content": r.document.content, "metadata": object()},
    )
    with pytest.raises(EvidenceSelectionError, match="rendering"):
        bad.select("q", [result])
