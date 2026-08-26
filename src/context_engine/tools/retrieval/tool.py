"""Read-only semantic search exposed through the deterministic Tool Runtime."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from typing import TypeAlias

from context_engine.retrieval import RetrievalRequest, Retriever, SearchResult
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

    def __post_init__(self) -> None:
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
    ) -> None:
        self._retriever = retriever
        self._config = config or SearchDocumentsToolConfig()

    def execute(self, invocation: ToolInvocation) -> Mapping[str, object]:
        """Retrieve and serialize bounded model-visible search results."""
        raw_query = invocation.arguments_as_mapping().get("query")
        if not isinstance(raw_query, str):
            raise SearchDocumentsToolInputError("query must be a string.")

        query = raw_query.strip()
        if not query:
            raise SearchDocumentsToolInputError("query must contain non-whitespace characters.")

        request = RetrievalRequest(query=query, top_k=self._config.top_k)
        raw_results = self._retriever.retrieve(request)
        bounded_results = tuple(raw_results)[: self._config.top_k]
        results = [self._serialize_result(result) for result in bounded_results]

        return {
            "query": query,
            "result_count": len(results),
            "results": results,
        }

    def _serialize_result(self, result: SearchResult) -> dict[str, object]:
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

        bounded_content = content[: self._config.max_content_chars]
        metadata = _normalize_json_mapping(
            result.document.metadata_as_mapping(),
            path=f"document[{document_id}].metadata",
        )
        return {
            "document_id": document_id,
            "score": score,
            "content": bounded_content,
            "content_truncated": len(content) > len(bounded_content),
            "metadata": metadata,
        }


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
