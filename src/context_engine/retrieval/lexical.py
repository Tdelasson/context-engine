"""Provider-independent lexical indexing and application retrieval contracts."""

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from hashlib import sha256
from math import isfinite
from typing import Protocol, runtime_checkable

from context_engine.retrieval.diagnostics import RetrievalStageDiagnostic
from context_engine.retrieval.embeddings import Document
from context_engine.retrieval.retriever import RetrievalRequest, Retriever, RetrieverError
from context_engine.retrieval.vector_store import MetadataFilter, SearchResult


class LexicalIndexError(RetrieverError):
    """Lexical encoding, storage, or search failed."""


class LexicalConfigurationError(LexicalIndexError, ValueError):
    """Invalid lexical configuration or request."""


class LexicalCompatibilityError(LexicalIndexError, ValueError):
    """Index configuration is incompatible; explicit rebuild is required."""


@dataclass(frozen=True, slots=True)
class LexicalIndexConfig:
    """Explicit BM25 representation identity, independent of provider objects.

    Native encoding uses English word tokenization, lowercasing, English Snowball stemming, no
    stopword removal. Average length is a fixed parameter, not a corpus estimate.
    """

    index_version: str = "bm25-word-v1"
    language: str = "english"
    encoding_version: str = "1.16.3"
    k: float = 1.2
    b: float = 0.75
    average_document_length: float = 128.0

    def __post_init__(self) -> None:
        if self.index_version != "bm25-word-v1" or self.language != "english":
            raise LexicalConfigurationError("Only bm25-word-v1 English encoding is supported.")
        if (
            not isinstance(self.encoding_version, str)
            or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", self.encoding_version) is None
        ):
            raise LexicalConfigurationError("Invalid encoding version.")
        if any(
            type(value) not in (int, float) or not isfinite(value)
            for value in (self.k, self.b, self.average_document_length)
        ):
            raise LexicalConfigurationError("BM25 parameters must be finite numbers.")
        if self.k <= 0 or not 0 <= self.b <= 1 or self.average_document_length <= 0:
            raise LexicalConfigurationError("Invalid BM25 k, b, or average length.")

    @property
    def configuration_id(self) -> str:
        return sha256(
            json.dumps(
                {
                    "version": self.index_version,
                    "language": self.language,
                    "k": self.k,
                    "b": self.b,
                    "avg_len": self.average_document_length,
                    "encoding": f"qdrant-native-{self.encoding_version}",
                    "tokenizer": "word",
                    "lowercase": True,
                    "stemmer": "english-snowball",
                    "stopwords": {},
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()


@runtime_checkable
class LexicalIndex(Protocol):
    @property
    def config(self) -> LexicalIndexConfig: ...

    def upsert(self, documents: Sequence[Document]) -> None:
        """Index chunks under the application's source lifecycle ownership."""

    def search(self, request: RetrievalRequest) -> Sequence[SearchResult]:
        """Search text while enforcing metadata and committed-source visibility."""

    def delete(self, document_ids: Sequence[str]) -> None:
        """Remove chunks under the application's source lifecycle ownership."""


def validate_lexical_request(request: RetrievalRequest) -> None:
    if not isinstance(request, RetrievalRequest) or not request.query.strip():
        raise LexicalConfigurationError("Lexical query must contain non-whitespace text.")
    if request.metadata_filter is not None:
        if not isinstance(request.metadata_filter, MetadataFilter):
            raise LexicalConfigurationError("metadata_filter must be a MetadataFilter.")
        keys = []
        for key, value in request.metadata_filter.equals:
            if (
                not isinstance(key, str)
                or not key.strip()
                or type(value) not in (str, int, float, bool)
                or isinstance(value, float)
                and not isfinite(value)
            ):
                raise LexicalConfigurationError("Invalid exact-match metadata filter.")
            keys.append(key)
        if len(set(keys)) != len(keys):
            raise LexicalConfigurationError("Metadata filter keys must be unique.")


class LexicalRetriever(Retriever):
    """Text retrieval without dense embedding inference or provider types."""

    def __init__(self, *, lexical_index: LexicalIndex) -> None:
        self._index = lexical_index

    def retrieve(self, request: RetrievalRequest) -> tuple[SearchResult, ...]:
        validate_lexical_request(request)
        results = tuple(self._index.search(request))
        for result in results:
            if (
                not isinstance(result, SearchResult)
                or not isinstance(result.document, Document)
                or not isinstance(result.document.document_id, str)
                or not result.document.document_id.strip()
                or not isinstance(result.document.content, str)
                or not result.document.content.strip()
                or type(result.score) not in (int, float)
                or not isfinite(result.score)
                or result.score < 0
            ):
                raise LexicalIndexError("Lexical index returned an invalid record or BM25 score.")
        if len(results) > request.top_k or len({r.document.document_id for r in results}) != len(
            results
        ):
            raise LexicalIndexError("Lexical index returned excessive or duplicate results.")
        ordered = sorted(results, key=lambda result: (-result.score, result.document.document_id))
        output = []
        for rank, result in enumerate(ordered, 1):
            if not isfinite(result.score) or result.score < 0:
                raise LexicalIndexError("BM25 scores must be finite and nonnegative.")
            if request.metadata_filter is not None and any(
                result.document.metadata_as_mapping().get(key) != value
                for key, value in request.metadata_filter.equals
            ):
                raise LexicalIndexError("Lexical index returned a result outside metadata filters.")
            output.append(
                replace(
                    result,
                    diagnostics=result.diagnostics
                    + (
                        RetrievalStageDiagnostic(
                            "lexical",
                            "bm25",
                            result.score,
                            rank,
                            self._index.config.configuration_id,
                        ),
                    ),
                )
            )
        return tuple(output)
