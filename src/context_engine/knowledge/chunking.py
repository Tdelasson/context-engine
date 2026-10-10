"""Deterministic, lossless source chunking with exact embedding-input accounting."""

from __future__ import annotations

import json
import re
from bisect import bisect_right
from dataclasses import asdict, dataclass
from enum import StrEnum
from hashlib import sha256
from typing import Protocol

from context_engine.knowledge.processing.contracts import (
    BlockKind,
    BlockLocation,
    ExtractedBlock,
    ProcessedSource,
    ProcessingDiagnostic,
    SourceFormat,
    SourceProvenance,
)
from context_engine.retrieval import Document


class ChunkingErrorCode(StrEnum):
    INVALID_CONFIGURATION = "invalid_configuration"
    INVALID_SOURCE = "invalid_source"
    EMPTY_CONTENT = "empty_content"
    INCOMPATIBLE_TOKENIZER = "incompatible_tokenizer"
    TOKEN_COUNT_FAILED = "token_count_failed"
    INPUT_BUDGET = "input_budget"


class ChunkingError(ValueError):
    """Chunking failure with a machine-readable reason."""

    def __init__(self, code: ChunkingErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class TokenCounter(Protocol):
    """Count without truncation using the configured embedding model's tokenizer.

    tokenizer_id must identify the tokenizer revision and preprocessing settings.
    max_input_tokens is the actual embedding runtime limit (not a guessed window).
    """

    model_id: str
    tokenizer_id: str
    max_input_tokens: int

    def count_tokens(self, text: str, *, add_special_tokens: bool = True) -> int: ...


@dataclass(frozen=True, slots=True)
class ChunkingConfig:
    """Explicit benchmark settings; no chunk-size or overlap quality default."""

    model_id: str
    max_input_tokens: int
    overlap_tokens: int
    document_prefix: str = ""
    include_heading_context: bool = True
    strategy_version: str = "structure-aware-v1"

    def __post_init__(self) -> None:
        if (
            not isinstance(self.model_id, str)
            or not self.model_id.strip()
            or type(self.max_input_tokens) is not int
            or self.max_input_tokens <= 0
            or type(self.overlap_tokens) is not int
            or not 0 <= self.overlap_tokens < self.max_input_tokens
            or not isinstance(self.document_prefix, str)
            or type(self.include_heading_context) is not bool
            or self.strategy_version != "structure-aware-v1"
        ):
            raise ChunkingError(
                ChunkingErrorCode.INVALID_CONFIGURATION,
                "Provide a model, positive limit, overlap below the limit, and supported strategy.",
            )


@dataclass(frozen=True, slots=True)
class ChunkSpan:
    """Clipped contributing block in the exact ProcessedSource.text representation."""

    block_index: int
    location: BlockLocation


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    chunk_id: str
    index: int
    source: SourceProvenance
    source_text: str
    content: str
    start_offset: int
    end_offset: int
    spans: tuple[ChunkSpan, ...]
    section_headings: tuple[str, ...]
    heading_context: str
    overlap_start_offset: int | None
    overlap_end_offset: int | None
    token_count: int
    configuration_id: str
    config: ChunkingConfig
    tokenizer_id: str
    processing_diagnostics: tuple[ProcessingDiagnostic, ...] = ()

    @property
    def page_numbers(self) -> tuple[int, ...]:
        return tuple(
            sorted(
                {
                    span.location.page_number
                    for span in self.spans
                    if span.location.page_number is not None
                }
            )
        )

    def to_document(self) -> Document:
        """Map for explicit later ingestion; the provider adds document_prefix once."""
        return Document.from_mapping(
            document_id=self.chunk_id,
            content=self.content,
            metadata={
                "source_id": self.source.source_id,
                "source_name": self.source.source_name,
                "source_kind": self.source.source_kind,
                "source_format": self.source.format.value,
                "content_sha256": self.source.content_sha256,
                "source_byte_length": self.source.byte_length,
                "source_encoding": self.source.encoding,
                "text_representation": "extracted_text",
                "chunk_index": self.index,
                "chunk_configuration_id": self.configuration_id,
                "chunk_configuration": asdict(self.config),
                "tokenizer_id": self.tokenizer_id,
                "embedding_input_tokens": self.token_count,
                "start_offset": self.start_offset,
                "end_offset": self.end_offset,
                "spans": [asdict(span) for span in self.spans],
                "page_numbers": list(self.page_numbers),
                "section_headings": list(self.section_headings),
                "heading_context": self.heading_context,
                "overlap_start_offset": self.overlap_start_offset,
                "overlap_end_offset": self.overlap_end_offset,
                "processing_diagnostics": [
                    {
                        "code": diagnostic.code.value,
                        "message": diagnostic.message,
                        "page_number": (
                            diagnostic.location.page_number
                            if diagnostic.location is not None
                            else None
                        ),
                    }
                    for diagnostic in self.processing_diagnostics
                ],
            },
        )


class StructureAwareChunker:
    """Split at sections, paragraphs, sentences, then Unicode character boundaries."""

    def __init__(self, config: ChunkingConfig, counter: TokenCounter) -> None:
        self.config = config
        self.counter = counter
        if (
            counter.model_id != config.model_id
            or not isinstance(counter.tokenizer_id, str)
            or not counter.tokenizer_id.strip()
            or type(counter.max_input_tokens) is not int
            or config.max_input_tokens > counter.max_input_tokens
        ):
            raise ChunkingError(
                ChunkingErrorCode.INCOMPATIBLE_TOKENIZER,
                "Tokenizer identity and runtime limit must match the embedding configuration.",
            )
        self.configuration_id = _digest(
            {"config": asdict(config), "tokenizer_id": counter.tokenizer_id}
        )

    def _count(self, text: str, *, special: bool = True) -> int:
        try:
            count = self.counter.count_tokens(text, add_special_tokens=special)
        except Exception as exc:
            raise ChunkingError(
                ChunkingErrorCode.TOKEN_COUNT_FAILED, "Tokenizer failed to count input."
            ) from exc
        if type(count) is not int or count < 0:
            raise ChunkingError(
                ChunkingErrorCode.TOKEN_COUNT_FAILED, "Tokenizer must return a nonnegative integer."
            )
        return count

    def chunk(self, source: ProcessedSource) -> tuple[DocumentChunk, ...]:
        _validate_source(source)
        text = source.text
        paragraph_ends = [match.end() for match in re.finditer(r"(?:\r?\n[ \t]*){2,}", text)]
        sentence_ends = [match.end() for match in re.finditer(r"[.!?](?:[ \t]+|\r?\n)", text)]
        heading_starts = [
            block.location.start_offset
            for block in source.blocks
            if block.kind == BlockKind.HEADING
        ]
        line_starts = [0]
        for line in text.splitlines(keepends=True):
            line_starts.append(line_starts[-1] + len(line))
        chunks: list[DocumentChunk] = []
        start = 0
        previous_end = 0
        while previous_end < len(text):
            sections = _sections(source, previous_end)
            in_heading = any(
                block.kind == BlockKind.HEADING
                and block.location.start_offset <= previous_end < block.location.end_offset
                for block in source.blocks
            )
            context_headings = list(sections)
            context = "\n".join(context_headings) + "\n\n" if context_headings else ""
            if not self.config.include_heading_context or in_heading:
                context = ""
            # Context is supplemental. Keep all headings in provenance, include only
            # complete trailing headings that leave room for the next source character.
            while (
                context
                and self._count(
                    self.config.document_prefix + context + text[previous_end : previous_end + 1]
                )
                > self.config.max_input_tokens
            ):
                context_headings.pop(0)
                context = "\n".join(context_headings) + "\n\n" if context_headings else ""
            next_heading = next((p for p in heading_starts if p > previous_end), len(text))
            cap = next_heading
            # Heading boundaries start a fresh section without overlap from its predecessor.
            if previous_end in heading_starts:
                start = previous_end
            while True:
                end = self._end(
                    text, start, previous_end, cap, context, paragraph_ends, sentence_ends
                )
                if end is not None:
                    break
                if start < previous_end:
                    start += 1  # Shrink overlap rather than losing new source content.
                else:
                    raise ChunkingError(
                        ChunkingErrorCode.INPUT_BUDGET,
                        "Embedding overhead and next source character exceed the input limit.",
                    )
            spans = _spans(source, start, end, line_starts)
            content = context + text[start:end]
            chunks.append(
                DocumentChunk(
                    chunk_id=_digest(
                        {
                            "source_id": source.provenance.source_id,
                            "revision": source.provenance.content_sha256,
                            "configuration": self.configuration_id,
                            "index": len(chunks),
                            "start": start,
                            "end": end,
                            "content": content,
                        }
                    ),
                    index=len(chunks),
                    source=source.provenance,
                    source_text=text[start:end],
                    content=content,
                    start_offset=start,
                    end_offset=end,
                    spans=spans,
                    section_headings=sections,
                    heading_context=context,
                    overlap_start_offset=start if start < previous_end else None,
                    overlap_end_offset=previous_end if start < previous_end else None,
                    token_count=self._count(self.config.document_prefix + content),
                    configuration_id=self.configuration_id,
                    config=self.config,
                    tokenizer_id=self.counter.tokenizer_id,
                    processing_diagnostics=source.diagnostics,
                )
            )
            previous_end = end
            start = end
            if self.config.overlap_tokens:
                # Examine exact Unicode suffixes; token counts need not be monotonic.
                for candidate in range(chunks[-1].start_offset + 1, end):
                    if (
                        self._count(text[candidate:end], special=False)
                        <= self.config.overlap_tokens
                    ):
                        start = candidate
                        break
        return tuple(chunks)

    def _end(
        self,
        text: str,
        start: int,
        previous_end: int,
        cap: int,
        context: str,
        paragraphs: list[int],
        sentences: list[int],
    ) -> int | None:
        def fits(end: int) -> bool:
            return (
                self._count(self.config.document_prefix + context + text[start:end])
                <= self.config.max_input_tokens
            )

        # Exponential probing and bisection are size heuristics, not a claim that
        # token counts are monotonic. Every selected candidate is counted exactly.
        # Finding the globally longest fitting prefix is unnecessary for coverage.
        best: int | None = None
        distance = 1
        upper = cap
        while True:
            probe = min(previous_end + distance, cap)
            if fits(probe):
                best = probe
                if probe == cap:
                    return cap
                distance *= 2
            else:
                upper = probe
                break
        if best is not None:
            lower = best
            while lower + 1 < upper:
                probe = (lower + upper) // 2
                if fits(probe):
                    best = lower = probe
                else:
                    upper = probe
        else:
            # A longer prefix can tokenize more cheaply than a single character.
            # This rare slow path searches until it finds any fitting Unicode slice.
            for probe in range(previous_end + 2, cap + 1):
                if fits(probe):
                    best = probe
                    break
        if best is None:
            return None
        for boundaries in (paragraphs, sentences):
            right = bisect_right(boundaries, best)
            left = bisect_right(boundaries, previous_end)
            # Bound structural candidate checks; tokenization is model-dependent.
            for end in reversed(boundaries[max(left, right - 16) : right]):
                if fits(end):
                    return end
        return best


def _digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _validate_source(source: ProcessedSource) -> None:
    if not isinstance(source, ProcessedSource) or not isinstance(source.text, str):
        raise ChunkingError(ChunkingErrorCode.INVALID_SOURCE, "A processed source is required.")
    if not source.text.strip():
        raise ChunkingError(ChunkingErrorCode.EMPTY_CONTENT, "Source has no non-whitespace text.")
    provenance = source.provenance
    if (
        not isinstance(provenance, SourceProvenance)
        or any(
            not isinstance(value, str) or not value.strip()
            for value in (provenance.source_id, provenance.source_name, provenance.source_kind)
        )
        or not isinstance(provenance.format, SourceFormat)
        or not isinstance(provenance.content_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", provenance.content_sha256) is None
        or type(provenance.byte_length) is not int
        or provenance.byte_length < 0
    ):
        raise ChunkingError(ChunkingErrorCode.INVALID_SOURCE, "Source provenance is inconsistent.")
    offset = 0
    for block in source.blocks:
        if not isinstance(block, ExtractedBlock) or not isinstance(block.location, BlockLocation):
            raise ChunkingError(ChunkingErrorCode.INVALID_SOURCE, "Invalid extracted block.")
        location = block.location
        if (
            type(location.start_offset) is not int
            or type(location.end_offset) is not int
            or location.start_offset != offset
            or not offset <= location.end_offset <= len(source.text)
            or block.text != source.text[offset : location.end_offset]
            or not isinstance(block.kind, BlockKind)
            or type(location.start_line) is not int
            or type(location.end_line) is not int
            or not 1 <= location.start_line <= location.end_line
            or (
                location.page_number is not None
                and (type(location.page_number) is not int or location.page_number <= 0)
            )
            or location.representation != "extracted_text"
            or (
                block.kind == BlockKind.HEADING
                and (type(block.heading_level) is not int or block.heading_level not in range(1, 7))
            )
        ):
            raise ChunkingError(
                ChunkingErrorCode.INVALID_SOURCE, "Blocks must exactly cover the extracted text."
            )
        offset = location.end_offset
    if offset != len(source.text):
        raise ChunkingError(ChunkingErrorCode.INVALID_SOURCE, "Blocks do not cover the source.")


def _sections(source: ProcessedSource, offset: int) -> tuple[str, ...]:
    headings: list[tuple[int, str]] = []
    for block in source.blocks:
        if block.location.start_offset > offset:
            break
        if block.kind == BlockKind.HEADING and block.heading_level is not None:
            headings = [(level, text) for level, text in headings if level < block.heading_level]
            headings.append((block.heading_level, block.text.rstrip("\r\n")))
    return tuple(text for _, text in headings)


def _spans(
    source: ProcessedSource, start: int, end: int, line_starts: list[int]
) -> tuple[ChunkSpan, ...]:
    spans: list[ChunkSpan] = []
    for index, block in enumerate(source.blocks):
        left = max(start, block.location.start_offset)
        right = min(end, block.location.end_offset)
        if left < right:
            spans.append(
                ChunkSpan(
                    index,
                    BlockLocation(
                        left,
                        right,
                        bisect_right(line_starts, left),
                        bisect_right(line_starts, right - 1),
                        page_number=block.location.page_number,
                    ),
                )
            )
    return tuple(spans)
