"""Errors raised by the Retriever-backed search tool."""


class SearchDocumentsToolError(Exception):
    """Base exception for search-documents tool failures."""


class SearchDocumentsToolConfigurationError(SearchDocumentsToolError, ValueError):
    """Raised when search-documents tool configuration is invalid."""


class SearchDocumentsToolInputError(SearchDocumentsToolError, ValueError):
    """Raised when a schema-valid query is not semantically usable."""


class SearchDocumentsToolOutputError(SearchDocumentsToolError, ValueError):
    """Raised when a retrieval result cannot become bounded JSON-safe output."""
