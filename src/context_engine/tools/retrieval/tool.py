"""Read-only semantic search exposed through the deterministic Tool Runtime."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from math import isfinite
from typing import TypeAlias

from context_engine.retrieval import RetrievalRequest, Retriever, SearchResult
from context_engine.retrieval.evidence_selection import (
    EvidenceSelectionConfig,
    EvidenceTokenCounter,
    RankedEvidenceSelector,
)
from context_engine.tools.retrieval.errors import (
    SearchDocumentsToolConfigurationError,
    SearchDocumentsToolInputError,
    SearchDocumentsToolOutputError,
)
from context_engine.tools.runtime import (
    ToolInputField,
    ToolInputSchema,
    ToolInvocation,
)

JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


@dataclass(frozen=True, slots=True)
class SearchDocumentsToolConfig:
    """Runtime-owned limits for model-visible semantic search results."""

    top_k: int = 3
    max_content_chars: int = 2_000
    candidate_limit: int = 20
    include_ranking_diagnostics: bool = True

    def __post_init__(self) -> None:
        if type(self.include_ranking_diagnostics) is not bool:
            raise SearchDocumentsToolConfigurationError(
                "include_ranking_diagnostics must be a bool."
            )
        if type(self.candidate_limit) is not int or not 1 <= self.candidate_limit <= 1000:
            raise SearchDocumentsToolConfigurationError("candidate_limit must be in [1, 1000].")
        if isinstance(self.top_k, bool) or not isinstance(self.top_k, int) or self.top_k <= 0:
            raise SearchDocumentsToolConfigurationError(
                "top_k must be an integer greater than zero."
            )
        if (
            isinstance(self.max_content_chars, bool)
            or not isinstance(self.max_content_chars, int)
            or self.max_content_chars <= 0
        ):
            raise SearchDocumentsToolConfigurationError(
                "max_content_chars must be an integer greater than zero."
            )


class SearchDocumentsTool:
    """Search documents through an injected provider-independent Retriever."""

    name = "search_documents"
    description = "Search indexed documents for information relevant to a query."
    input_schema = ToolInputSchema(fields=(ToolInputField(name="query", value_type=str),))

    def __init__(
        self,
        retriever: Retriever,
        *,
        config: SearchDocumentsToolConfig | None = None,
        selection_config: EvidenceSelectionConfig | None = None,
        evidence_counter: EvidenceTokenCounter | None = None,
    ) -> None:
        self._retriever = retriever
        self._config = config or SearchDocumentsToolConfig()
        if (selection_config is None) != (evidence_counter is None):
            raise SearchDocumentsToolConfigurationError(
                "Selection requires both config and counter."
            )
        self._selector = (
            RankedEvidenceSelector(
                replace(
                    selection_config,
                    max_results=min(selection_config.max_results, self._config.top_k),
                    max_content_chars=min(
                        selection_config.max_content_chars, self._config.max_content_chars
                    ),
                ),
                evidence_counter,
                lambda result: self._serialize_result(result, preserve_content=True),
                serializer_identity=None
                if self._config.include_ranking_diagnostics
                else "search-documents-without-ranking-diagnostics-v1",
            )
            if selection_config is not None and evidence_counter is not None
            else None
        )

    def execute(self, invocation: ToolInvocation) -> Mapping[str, object]:
        """Retrieve and serialize bounded model-visible search results."""
        raw_query = invocation.arguments_as_mapping().get("query")
        if not isinstance(raw_query, str):
            raise SearchDocumentsToolInputError("query must be a string.")

        query = raw_query.strip()
        if not query:
            raise SearchDocumentsToolInputError("query must contain non-whitespace characters.")

        request = RetrievalRequest(
            query=query,
            top_k=self._config.candidate_limit
            if self._selector is not None
            else self._config.top_k,
        )
        raw_results = self._retriever.retrieve(request)
        if self._selector is not None:
            from itertools import islice

            selection = self._selector.select(
                query, tuple(islice(raw_results, self._config.candidate_limit))
            )
            return {
                **selection.output,
                "selection_diagnostics": {
                    "status": selection.status,
                    "token_count": selection.token_count,
                    "configuration_id": selection.configuration_id,
                    "configuration": asdict(self._selector.config),
                    "counter_id": self._selector.counter.configuration_id,
                    "counting_method": self._selector.counter.method,
                    "answering_model": self._selector.counter.model_id,
                    "include_ranking_diagnostics": self._config.include_ranking_diagnostics,
                    "ranking_diagnostics": {
                        result.document.document_id: [asdict(stage) for stage in result.diagnostics]
                        for result in selection.selected
                        if result.diagnostics
                    },
                    "candidates": [asdict(item) for item in selection.diagnostics],
                },
            }
        bounded_results = tuple(raw_results)[: self._config.top_k]
        results = [self._serialize_result(result) for result in bounded_results]

        return {
            "query": query,
            "result_count": len(results),
            "results": results,
        }

    def _serialize_result(
        self, result: SearchResult, *, preserve_content: bool = False
    ) -> dict[str, object]:
        document_id = result.document.document_id
        if not isinstance(document_id, str) or not document_id:
            raise SearchDocumentsToolOutputError(
                "Search result document_id must be a non-empty string."
            )

        content = result.document.content
        if not isinstance(content, str):
            raise SearchDocumentsToolOutputError(
                f"Search result '{document_id}' content must be a string."
            )

        score = float(result.score)
        if not isfinite(score):
            raise SearchDocumentsToolOutputError(
                f"Search result '{document_id}' has a non-finite score."
            )

        bounded_content = content if preserve_content else content[: self._config.max_content_chars]
        metadata = _normalize_json_mapping(
            result.document.metadata_as_mapping(),
            path=f"document[{document_id}].metadata",
        )
        serialized: dict[str, object] = {
            "document_id": document_id,
            "score": score,
            "content": bounded_content,
            "content_truncated": len(content) > len(bounded_content),
            "metadata": metadata,
        }
        if result.diagnostics and self._config.include_ranking_diagnostics:
            serialized["diagnostics"] = [
                _normalize_json_mapping(asdict(stage), path="diagnostics")
                for stage in result.diagnostics
            ]
        return serialized


def _normalize_json_mapping(
    value: Mapping[str, object],
    *,
    path: str,
) -> dict[str, JsonValue]:
    keys = tuple(value.keys())
    if not all(isinstance(key, str) for key in keys):
        raise SearchDocumentsToolOutputError(f"{path} must use string keys.")

    normalized: dict[str, JsonValue] = {}
    for key in sorted(keys):
        normalized[key] = _normalize_json_value(value[key], path=f"{path}.{key}")
    return normalized


def _normalize_json_value(value: object, *, path: str) -> JsonValue:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise SearchDocumentsToolOutputError(f"{path} must be a finite number.")
        return value
    if isinstance(value, Mapping):
        return _normalize_json_mapping(value, path=path)
    if isinstance(value, (list, tuple)):
        return [
            _normalize_json_value(item, path=f"{path}[{index}]") for index, item in enumerate(value)
        ]
    raise SearchDocumentsToolOutputError(
        f"{path} has unsupported JSON value type: {type(value).__name__}."
    )
