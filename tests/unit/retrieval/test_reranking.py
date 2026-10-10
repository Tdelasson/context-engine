"""Deterministic ranking, boundaries and failure tests; no model downloads."""

from dataclasses import replace
from typing import Any, cast

import pytest

from context_engine.retrieval.diagnostics import RetrievalStageDiagnostic
from context_engine.retrieval.embeddings import Document
from context_engine.retrieval.local_cross_encoder import (
    LocalCrossEncoderConfig,
    LocalCrossEncoderReranker,
)
from context_engine.retrieval.reranking import (
    RerankerConfigurationError,
    RerankerInferenceError,
    RerankerInitializationError,
    RerankerInputCompatibilityError,
    RerankingCandidate,
    RerankingRequest,
    RerankingRetriever,
    RerankingRetrieverConfig,
    RerankingScore,
)
from context_engine.retrieval.retriever import RetrievalRequest
from context_engine.retrieval.vector_store import MetadataFilter, SearchResult


class Upstream:
    def __init__(self, results: Any) -> None:
        self.results = results
        self.request: RetrievalRequest | None = None

    def retrieve(self, request: RetrievalRequest) -> Any:
        self.request = request
        return self.results


class Scorer:
    model_id = "fake"
    configuration_id = "fake-v1"
    score_kind = "logit"

    def __init__(self, scores: Any) -> None:
        self.scores = scores
        self.calls = 0

    def score(self, request: RerankingRequest) -> Any:
        self.calls += 1
        if isinstance(self.scores, Exception):
            raise self.scores
        return self.scores


def results() -> Any:
    return tuple(
        SearchResult(
            Document.from_mapping(
                document_id=name,
                content="text " + name,
                metadata={"source_id": "source", "source_revision": "revision"},
            ),
            score,
        )
        for name, score in [("a", 0.9), ("b", 0.8), ("c", 0.7)]
    )


@pytest.mark.parametrize(
    "scores,order",
    [
        ([1, 3, 2], ["b", "c", "a"]),
        ([1, 2, 3], ["c", "b", "a"]),
        ([3, 2, 1], ["a", "b", "c"]),
        ([1, 1, 1], ["a", "b", "c"]),
    ],
)
def test_order_provenance_filters_limits(scores: Any, order: Any) -> None:
    original = results()
    upstream = Upstream(original)
    scorer = Scorer([RerankingScore(r.document.document_id, s) for r, s in zip(original, scores)])
    wrapper = RerankingRetriever(upstream, scorer, config=RerankingRetrieverConfig(4, 3))
    filters = MetadataFilter.from_mapping({"source_id": "source"})
    out = wrapper.retrieve(RetrievalRequest(" query ", 2, filters))
    assert [r.document.document_id for r in out] == order[:2]
    assert upstream.request == RetrievalRequest(" query ", 4, filters)
    for r in out:
        old = next(v for v in original if v.document.document_id == r.document.document_id)
        assert r.document is old.document
        assert r.diagnostics[-2].score == old.score
        assert r.diagnostics[-1].candidate_count == 3


def test_empty_and_duplicates() -> None:
    scorer = Scorer([])
    assert RerankingRetriever(Upstream([]), scorer).retrieve(RetrievalRequest("q")) == ()
    assert scorer.calls == 0
    for candidates in (
        [results()[0], results()[0]],
        [
            replace(results()[0], document=replace(results()[0].document, content="conflict")),
            results()[0],
        ],
    ):
        with pytest.raises(RerankerConfigurationError):
            RerankingRetriever(Upstream(candidates), scorer).retrieve(RetrievalRequest("q"))


@pytest.mark.parametrize(
    "bad",
    [
        [],
        [RerankingScore("a", 1)],
        [RerankingScore("a", 1), RerankingScore("a", 2), RerankingScore("c", 3)],
        [RerankingScore("a", 1), RerankingScore("b", 2), RerankingScore("unknown", 3)],
        [object()],
        RuntimeError("failed"),
    ],
)
def test_invalid_outputs_fail(bad: Any) -> None:
    with pytest.raises(RerankerInferenceError):
        RerankingRetriever(Upstream(results()), Scorer(bad)).retrieve(RetrievalRequest("q"))


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), True, "1"])
def test_invalid_score(bad: Any) -> None:
    with pytest.raises(RerankerInferenceError):
        RerankingScore("a", bad)


@pytest.mark.parametrize("bad", [0, -1, True, 1.5])
def test_invalid_limits(bad: Any) -> None:
    with pytest.raises(RerankerConfigurationError):
        RerankingRetrieverConfig(bad, 1)
    with pytest.raises(RerankerConfigurationError):
        LocalCrossEncoderConfig(batch_size=bad)


class Backend:
    max_input_tokens = 512
    identity = "fixture-tokenizer-and-weights"
    model_parameter_bytes = 42

    def __init__(self) -> None:
        self.batches: list[tuple[tuple[str, str], ...]] = []

    def count_pair(self, query: Any, passage: Any) -> Any:
        return len(query) + len(passage) + 3

    def score_pairs(self, pairs: Any) -> Any:
        self.batches.append(tuple(pairs))
        return [len(passage) for _, passage in pairs]


def request(contents: tuple[str, ...] = ("abc", "🦊å")) -> RerankingRequest:
    return RerankingRequest(
        "q",
        tuple(
            RerankingCandidate(Document.from_mapping(document_id=str(i), content=text))
            for i, text in enumerate(contents)
        ),
    )


def test_pair_exact_boundary_prefixes_unicode_and_batches() -> None:
    backend = Backend()
    config = LocalCrossEncoderConfig(
        max_input_tokens=11, batch_size=1, query_prefix="Q:", passage_prefix="P:"
    )
    reranker = LocalCrossEncoderReranker(config, backend_factory=lambda _: backend)
    out = reranker.score(request())
    assert [s.candidate_id for s in out] == ["0", "1"]
    assert backend.batches == [(("Q:q", "P:abc"),), (("Q:q", "P:🦊å"),)]
    assert reranker.model_parameter_bytes == 42
    assert (
        reranker.configuration_id
        != LocalCrossEncoderReranker(
            replace(config, query_prefix=""), backend_factory=lambda _: backend
        ).configuration_id
    )


def test_all_pairs_validated_before_inference() -> None:
    backend = Backend()
    reranker = LocalCrossEncoderReranker(
        LocalCrossEncoderConfig(max_input_tokens=8, batch_size=1), backend_factory=lambda _: backend
    )
    with pytest.raises(RerankerInputCompatibilityError, match="Candidate '1'.*9 pair tokens"):
        reranker.score(request(("abc", "abcde")))
    assert not backend.batches


def test_load_failure_and_model_limit() -> None:
    def failed(_: Any) -> Any:
        raise RuntimeError("load")

    with pytest.raises(RerankerInitializationError):
        LocalCrossEncoderReranker(backend_factory=failed)
    with pytest.raises(RerankerConfigurationError):
        LocalCrossEncoderReranker(
            LocalCrossEncoderConfig(max_input_tokens=513), backend_factory=lambda _: Backend()
        )


@pytest.mark.parametrize(
    "bad", [None, object(), SearchResult(results()[0].document, cast(Any, "bad"))]
)
def test_invalid_upstream_is_typed(bad: Any) -> None:
    with pytest.raises(RerankerInferenceError):
        RerankingRetriever(Upstream([bad]), Scorer([])).retrieve(RetrievalRequest("q"))


def test_blank_and_incompatible_config() -> None:
    with pytest.raises(RerankerConfigurationError):
        RerankingRequest("  ", ())
    with pytest.raises(RerankerConfigurationError):
        RerankingCandidate(cast(Any, object()))
    with pytest.raises(RerankerConfigurationError):
        RerankingRetrieverConfig(2, 3)
    with pytest.raises(RerankerConfigurationError):
        RerankingRetriever(Upstream([]), Scorer([])).retrieve(RetrievalRequest(" "))


@pytest.mark.parametrize(
    "field,value",
    [
        ("score", True),
        ("rank", 0),
        ("rank", True),
        ("duration_seconds", float("nan")),
        ("candidate_count", 0),
        ("configuration_id", ""),
    ],
)
def test_diagnostic_validation(field: Any, value: Any) -> None:
    with pytest.raises(ValueError):
        RetrievalStageDiagnostic(
            **(
                {
                    "strategy": "test",
                    "score_kind": "native",
                    "score": 1.0,
                    "rank": 1,
                    "configuration_id": "id",
                }
                | {field: value}
            )
        )


def test_backend_inference_bad_count_and_failure() -> None:
    for output in ([], [float("nan")], RuntimeError("inference")):
        backend = Backend()

        def score_pairs(pairs: Any) -> Any:
            if isinstance(output, Exception):
                raise output
            return output

        setattr(backend, "score_pairs", score_pairs)
        reranker = LocalCrossEncoderReranker(backend_factory=lambda _: backend)
        with pytest.raises(RerankerInferenceError):
            reranker.score(request(("abc",)))


def test_tool_boundary_diagnostics_and_policy() -> None:
    from context_engine.tools.policy import ToolNamePolicy, ToolPolicyDecision
    from context_engine.tools.retrieval.tool import SearchDocumentsTool
    from context_engine.tools.runtime import (
        ToolInvocation,
        ToolRegistry,
        ToolResultStatus,
        ToolRuntime,
    )

    scorer = Scorer([RerankingScore(r.document.document_id, 1) for r in results()])
    registry = ToolRegistry()
    registry.register(SearchDocumentsTool(RerankingRetriever(Upstream(results()), scorer)))
    invocation = ToolInvocation.from_mapping(tool_name="search_documents", arguments={"query": "q"})
    denied = ToolRuntime(
        registry, policy=ToolNamePolicy((), default_decision=ToolPolicyDecision.DENY)
    ).execute(invocation)
    assert denied.status is ToolResultStatus.ERROR
    assert scorer.calls == 0
    successful = ToolRuntime(registry).execute(invocation)
    assert successful.status is ToolResultStatus.SUCCESS
    evidence = cast(list[dict[str, Any]], successful.output_as_mapping()["results"])[0]
    assert evidence["diagnostics"][-1]["strategy"] == "reranking"
    assert evidence["metadata"] == {"source_id": "source", "source_revision": "revision"}
    scorer.scores = RuntimeError("failed")
    failed = ToolRuntime(registry).execute(invocation)
    assert failed.status is ToolResultStatus.ERROR
    assert failed.error is not None
    assert failed.error.error_type == "RerankerInferenceError"


def test_workbench_configuration_disabled_and_enabled(monkeypatch: Any) -> None:
    from context_engine.workbench.application import configure_reranking
    from context_engine.workbench.config import WorkbenchConfigurationError, WorkbenchSettings

    upstream = Upstream(results())
    assert configure_reranking(upstream, WorkbenchSettings()) is upstream
    scorer = Scorer([RerankingScore(r.document.document_id, 1) for r in results()])
    monkeypatch.setattr(
        "context_engine.workbench.application.LocalCrossEncoderReranker", lambda _: scorer
    )
    enabled = configure_reranking(upstream, WorkbenchSettings(reranking_enabled=True))
    assert isinstance(enabled, RerankingRetriever)
    assert (
        enabled.retrieve(RetrievalRequest("q"))[0].document is results()[0].document
        or enabled.retrieve(RetrievalRequest("q"))[0].document == results()[0].document
    )
    monkeypatch.setenv("CONTEXT_ENGINE_RERANKING_ENABLED", "true")
    assert WorkbenchSettings.from_environment().reranking_enabled
    monkeypatch.setenv("CONTEXT_ENGINE_RERANKING_ENABLED", "maybe")
    with pytest.raises(WorkbenchConfigurationError):
        WorkbenchSettings.from_environment()


def test_library_path_disables_truncation_and_preserves_exact_text() -> None:
    from contextlib import nullcontext
    from types import SimpleNamespace

    from context_engine.retrieval.local_cross_encoder import _SentenceTransformersBackend

    class Tensor:
        shape = (2, 5)

        def to(self, device: Any) -> Any:
            assert device == "cpu"
            return self

        def __getitem__(self, index: Any) -> Any:
            return self

        def detach(self) -> Any:
            return self

        def cpu(self) -> Any:
            return self

        def tolist(self) -> Any:
            return [1.0, 2.0]

    calls = []

    def tokenizer(query: Any, passage: Any, **kwargs: Any) -> Any:
        calls.append((query, passage, kwargs))
        assert kwargs["truncation"] is False
        assert kwargs["add_special_tokens"] is True
        if kwargs["padding"] is False:
            return {"input_ids": [1, 2, 3, 4, 5]}
        return {"input_ids": Tensor()}

    backend = _SentenceTransformersBackend.__new__(_SentenceTransformersBackend)
    backend._tokenizer = tokenizer
    backend._torch = SimpleNamespace(inference_mode=nullcontext)
    backend._cross_encoder = SimpleNamespace(device="cpu")
    logits = Tensor()
    logits.shape = (2, 1)
    backend._model = lambda **kwargs: SimpleNamespace(logits=logits)
    backend.max_input_tokens = 5
    assert backend.count_pair(" q ", "Heading\n🦊å") == 5
    assert backend.score_pairs([(" q ", "Heading\n🦊å"), ("q", "b")]) == (1.0, 2.0)
    assert calls[0][:2] == (" q ", "Heading\n🦊å")
    assert calls[1][0] == [" q ", "q"]
