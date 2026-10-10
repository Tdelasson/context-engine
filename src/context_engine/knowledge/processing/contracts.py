"""Immutable source-processing contracts, independent of acquisition and retrieval."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class ProcessingErrorCode(StrEnum):
    INVALID_INPUT = "invalid_input"
    UNSUPPORTED_FORMAT = "unsupported_format"
    INVALID_ENCODING = "invalid_encoding"
    EMPTY_CONTENT = "empty_content"
    BYTE_LIMIT = "byte_limit"
    TEXT_LIMIT = "text_limit"
    INVALID_CONFIGURATION = "invalid_configuration"
    MISSING_DEPENDENCY = "missing_dependency"
    MALFORMED_PDF = "malformed_pdf"
    ENCRYPTED_PDF = "encrypted_pdf"
    PAGE_LIMIT = "page_limit"


class ProcessingError(ValueError):
    """Explicit processing failure with a machine-readable reason."""

    def __init__(self, code: ProcessingErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class SourceFormat(StrEnum):
    TEXT = "text"
    MARKDOWN = "markdown"
    PDF = "pdf"


@dataclass(frozen=True, slots=True)
class SourceInput:
    """Supplied bytes; source_id is assigned by the caller, never inferred from content."""

    source_id: str
    source_name: str
    content: bytes
    format: SourceFormat
    source_kind: str = "supplied"

    def __post_init__(self) -> None:
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (self.source_id, self.source_name, self.source_kind)
        ) or not isinstance(self.content, bytes):
            raise ProcessingError(
                ProcessingErrorCode.INVALID_INPUT,
                "Source identifiers and supplied bytes are required.",
            )
        if not isinstance(self.format, SourceFormat):
            raise ProcessingError(
                ProcessingErrorCode.UNSUPPORTED_FORMAT,
                "Only text, Markdown, and PDF formats are supported.",
            )


@dataclass(frozen=True, slots=True)
class ProcessingLimits:
    max_bytes: int = 256 * 1024
    max_text_characters: int = 256 * 1024
    max_pages: int = 100

    def __post_init__(self) -> None:
        if any(
            type(value) is not int or value <= 0
            for value in (self.max_bytes, self.max_text_characters, self.max_pages)
        ):
            raise ProcessingError(
                ProcessingErrorCode.INVALID_CONFIGURATION,
                "Processing limits must be positive integers.",
            )


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    source_id: str
    source_name: str
    source_kind: str
    format: SourceFormat
    content_sha256: str
    byte_length: int
    encoding: Literal["utf-8"] | None = "utf-8"


class BlockKind(StrEnum):
    TEXT = "text"
    HEADING = "heading"
    CODE = "code"
    WHITESPACE = "whitespace"


@dataclass(frozen=True, slots=True)
class BlockLocation:
    """Character span in ProcessedSource.text, and inclusive one-based line span."""

    start_offset: int
    end_offset: int
    start_line: int
    end_line: int
    representation: Literal["extracted_text"] = "extracted_text"
    page_number: int | None = None


@dataclass(frozen=True, slots=True)
class ExtractedBlock:
    kind: BlockKind
    text: str
    location: BlockLocation
    heading_level: int | None = None


class DiagnosticCode(StrEnum):
    BOM_REMOVED = "bom_removed"
    UNCLOSED_CODE_FENCE = "unclosed_code_fence"
    EMPTY_PAGE = "empty_page"
    PARTIAL_EXTRACTION = "partial_extraction"


@dataclass(frozen=True, slots=True)
class ProcessingDiagnostic:
    code: DiagnosticCode
    message: str
    location: BlockLocation | None = None


@dataclass(frozen=True, slots=True)
class ProcessedSource:
    text: str
    blocks: tuple[ExtractedBlock, ...]
    provenance: SourceProvenance
    diagnostics: tuple[ProcessingDiagnostic, ...] = ()
