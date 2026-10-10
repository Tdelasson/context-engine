"""Provider-independent scoring and bounded retrieval orchestration."""

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import islice
from math import isfinite
from time import perf_counter
from typing import Protocol

from context_engine.retrieval.diagnostics import RetrievalStageDiagnostic
from context_engine.retrieval.embeddings import Document
from context_engine.retrieval.retriever import RetrievalRequest, Retriever, RetrieverError
from context_engine.retrieval.vector_store import SearchResult


class RerankerError(RetrieverError):
    """Explicit enabled-reranking failure; never converted to an upstream fallback."""


class RerankerConfigurationError(RerankerError, ValueError):
    """Invalid scoring request or configuration."""


class RerankerInputCompatibilityError(RerankerError, ValueError):
    """The full preprocessed pair exceeds the effective model input limit."""


class RerankerInitializationError(RerankerError, RuntimeError):
    """Optional dependency or local model could not be loaded."""


class RerankerInferenceError(RerankerError, RuntimeError):
    """Inference failed or returned invalid/incomplete scores."""


def positive_integer(name: str, value: int) -> None:
    """Validate application-controlled resource limits."""
    if type(value) is not int or value <= 0:
        raise RerankerConfigurationError(f"{name} must be a positive integer.")


@dataclass(frozen=True, slots=True)
class RerankingCandidate:
    """Original immutable evidence; document_id is the canonical candidate identity."""

    document: Document

    def __post_init__(self) -> None:
        if not isinstance(self.document, Document):
            raise RerankerConfigurationError("Candidate must contain a Document.")

    @property
    def candidate_id(self) -> str:
        return self.document.document_id


@dataclass(frozen=True, slots=True)
class RerankingRequest:
    """Score every unique candidate against the unchanged query."""

    query: str
    candidates: tuple[RerankingCandidate, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.query, str) or not self.query.strip():
            raise RerankerConfigurationError("query must contain non-whitespace characters.")
        identities: set[str] = set()
        for candidate in self.candidates:
            if not isinstance(candidate, RerankingCandidate):
                raise RerankerConfigurationError("candidates must be RerankingCandidate values.")
            if not candidate.candidate_id or candidate.candidate_id in identities:
                raise RerankerConfigurationError("Candidates must have unique nonblank identities.")
            if not isinstance(candidate.document.content, str) or not candidate.document.content:
                raise RerankerConfigurationError("Candidate content must be nonempty text.")
            identities.add(candidate.candidate_id)


@dataclass(frozen=True, slots=True)
class RerankingScore:
    """Native higher-is-more-relevant score explicitly associated with evidence."""

    candidate_id: str
    score: float

    def __post_init__(self) -> None:
        if not isinstance(self.candidate_id, str) or not self.candidate_id.strip():
            raise RerankerInferenceError("Scored candidate identity must be nonblank.")
        if (
            isinstance(self.score, bool)
            or not isinstance(self.score, (int, float))
            or not isfinite(self.score)
        ):
            raise RerankerInferenceError("Relevance scores must be finite numeric values.")


class Reranker(Protocol):
    """A scoring provider cannot change, fabricate, or drop candidate evidence."""

    @property
    def model_id(self) -> str: ...

    @property
    def configuration_id(self) -> str: ...

    @property
    def score_kind(self) -> str: ...

    def score(self, request: RerankingRequest) -> Sequence[RerankingScore]: ...


@dataclass(frozen=True, slots=True)
class RerankingRetrieverConfig:
    """Candidate budget and output ceiling, independent of adapter inference batching."""

    candidate_limit: int = 20
    final_limit: int = 5

    def __post_init__(self) -> None:
        positive_integer("candidate_limit", self.candidate_limit)
        positive_integer("final_limit", self.final_limit)
        if self.final_limit > self.candidate_limit:
            raise RerankerConfigurationError("final_limit cannot exceed candidate_limit.")


class RerankingRetriever:
    """Wrap any Retriever while preserving evidence and upstream ranking diagnostics."""

    def __init__(
        self,
        upstream: Retriever,
        reranker: Reranker,
        *,
        config: RerankingRetrieverConfig | None = None,
    ) -> None:
        self._upstream = upstream
        self._reranker = reranker
        self._config = config or RerankingRetrieverConfig()

    def retrieve(self, request: RetrievalRequest) -> tuple[SearchResult, ...]:
        if not request.query.strip():
            raise RerankerConfigurationError("query must contain non-whitespace characters.")
        candidates = tuple(
            islice(
                self._upstream.retrieve(
                    RetrievalRequest(
                        request.query, self._config.candidate_limit, request.metadata_filter
                    )
                ),
                self._config.candidate_limit + 1,
            )
        )
        if len(candidates) > self._config.candidate_limit:
            raise RerankerInferenceError("Upstream exceeded the configured candidate limit.")
        if not all(isinstance(result, SearchResult) for result in candidates):
            raise RerankerInferenceError("Upstream supplied malformed candidates.")
        scoring_request = RerankingRequest(
            request.query, tuple(RerankingCandidate(result.document) for result in candidates)
        )
        if not candidates:
            return ()
        for result in candidates:
            if (
                isinstance(result.score, bool)
                or not isinstance(result.score, (int, float))
                or not isfinite(result.score)
            ):
                raise RerankerInferenceError("Upstream supplied an invalid score.")
        started = perf_counter()
        try:
            outputs = tuple(self._reranker.score(scoring_request))
        except RerankerError:
            raise
        except Exception as exc:
            raise RerankerInferenceError("Enabled reranking failed.") from exc
        elapsed = perf_counter() - started
        scores: dict[str, float] = {}
        expected = {candidate.candidate_id for candidate in scoring_request.candidates}
        for output in outputs:
            if not isinstance(output, RerankingScore):
                raise RerankerInferenceError("Reranker returned a malformed score record.")
            if output.candidate_id not in expected or output.candidate_id in scores:
                raise RerankerInferenceError("Reranker returned an unknown or duplicate identity.")
            if isinstance(output.score, bool) or not isfinite(output.score):
                raise RerankerInferenceError("Reranker returned a non-finite score.")
            scores[output.candidate_id] = output.score
        if set(scores) != expected:
            raise RerankerInferenceError("Reranker did not score every candidate.")
        ordered = sorted(
            enumerate(candidates, 1),
            key=lambda item: (-scores[item[1].document.document_id], item[0]),
        )
        results: list[SearchResult] = []
        for rank, (upstream_rank, result) in enumerate(ordered, 1):
            score = scores[result.document.document_id]
            upstream_diagnostic = RetrievalStageDiagnostic(
                "upstream", "native", result.score, upstream_rank, "injected-retriever"
            )
            reranking_diagnostic = RetrievalStageDiagnostic(
                "reranking",
                self._reranker.score_kind,
                score,
                rank,
                self._reranker.configuration_id,
                self._reranker.model_id,
                len(candidates),
                elapsed,
            )
            results.append(
                SearchResult(
                    result.document,
                    score,
                    result.diagnostics + (upstream_diagnostic, reranking_diagnostic),
                )
            )
        return tuple(results[: min(request.top_k, self._config.final_limit)])
