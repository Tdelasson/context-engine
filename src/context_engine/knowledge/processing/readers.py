"""Lossless UTF-8 text and structural Markdown readers. No filesystem or inference access."""

import re
from hashlib import sha256

from context_engine.knowledge.processing.contracts import (
    BlockKind,
    BlockLocation,
    DiagnosticCode,
    ExtractedBlock,
    ProcessedSource,
    ProcessingDiagnostic,
    ProcessingError,
    ProcessingErrorCode,
    ProcessingLimits,
    SourceFormat,
    SourceInput,
    SourceProvenance,
)

_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+|$)")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")


def process_source(source: SourceInput, limits: ProcessingLimits | None = None) -> ProcessedSource:
    """Validate and process supplied bytes without changing source syntax or whitespace."""
    limits = limits or ProcessingLimits()
    if len(source.content) > limits.max_bytes:
        raise ProcessingError(
            ProcessingErrorCode.BYTE_LIMIT,
            f"Source '{source.source_name}' exceeds {limits.max_bytes} bytes.",
        )
    if source.format == SourceFormat.PDF:
        from context_engine.knowledge.processing.pdf import process_pdf

        return process_pdf(source, limits)
    try:
        text = source.content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ProcessingError(
            ProcessingErrorCode.INVALID_ENCODING,
            f"Source '{source.source_name}' must contain valid UTF-8 text.",
        ) from exc
    if len(text) > limits.max_text_characters:
        raise ProcessingError(
            ProcessingErrorCode.TEXT_LIMIT,
            f"Source '{source.source_name}' exceeds "
            f"{limits.max_text_characters} extracted characters.",
        )
    if not text.strip():
        raise ProcessingError(
            ProcessingErrorCode.EMPTY_CONTENT,
            f"Source '{source.source_name}' is empty or contains only whitespace.",
        )
    diagnostics: list[ProcessingDiagnostic] = []
    if source.content.startswith(b"\xef\xbb\xbf"):
        diagnostics.append(
            ProcessingDiagnostic(DiagnosticCode.BOM_REMOVED, "Leading UTF-8 BOM removed.")
        )
    if source.format == SourceFormat.MARKDOWN:
        blocks, markdown_diagnostics = _markdown_blocks(text)
        diagnostics.extend(markdown_diagnostics)
    else:
        blocks = (ExtractedBlock(BlockKind.TEXT, text, _location(text)),)
    return ProcessedSource(
        text=text,
        blocks=blocks,
        provenance=SourceProvenance(
            source.source_id,
            source.source_name,
            source.source_kind,
            source.format,
            sha256(source.content).hexdigest(),
            len(source.content),
        ),
        diagnostics=tuple(diagnostics),
    )


def _location(text: str) -> BlockLocation:
    return BlockLocation(0, len(text), 1, len(text.splitlines()) or 1)


def _markdown_blocks(
    text: str,
) -> tuple[tuple[ExtractedBlock, ...], tuple[ProcessingDiagnostic, ...]]:
    lines = text.splitlines(keepends=True)
    blocks: list[ExtractedBlock] = []
    diagnostics: list[ProcessingDiagnostic] = []
    index = 0
    offset = 0
    while index < len(lines):
        start = index
        line = lines[index].rstrip("\r\n")
        heading = _HEADING.match(line)
        fence = _FENCE.match(line)
        if fence and fence[1][0] == "`" and "`" in fence[2]:
            fence = None
        level = None
        unclosed = False
        if fence:
            kind = BlockKind.CODE
            marker = fence[1]
            closing = re.compile(
                r"^ {0,3}" + re.escape(marker[0]) + "{" + str(len(marker)) + r",}[ \t]*$"
            )
            index += 1
            while index < len(lines) and not closing.fullmatch(lines[index].rstrip("\r\n")):
                index += 1
            unclosed = index == len(lines)
            if not unclosed:
                index += 1
        elif heading:
            kind = BlockKind.HEADING
            level = len(heading[1])
            index += 1
        elif (
            line.strip()
            and not line.startswith(("    ", "\t"))
            and index + 1 < len(lines)
            and (underline := _SETEXT.fullmatch(lines[index + 1].rstrip("\r\n")))
        ):
            kind = BlockKind.HEADING
            level = 1 if underline[1][0] == "=" else 2
            index += 2
        else:
            kind = (
                BlockKind.WHITESPACE
                if not line.strip()
                else BlockKind.CODE
                if line.startswith(("    ", "\t"))
                else BlockKind.TEXT
            )
            # Coalesce adjacent lines of the same non-heading/non-fenced kind.
            index += 1
            while index < len(lines):
                next_line = lines[index].rstrip("\r\n")
                if kind == BlockKind.WHITESPACE and not next_line.strip():
                    index += 1
                elif kind == BlockKind.CODE and next_line.startswith(("    ", "\t")):
                    index += 1
                elif (
                    kind == BlockKind.TEXT
                    and next_line.strip()
                    and not (
                        next_line.startswith(("    ", "\t"))
                        or _HEADING.match(next_line)
                        or _FENCE.match(next_line)
                        or (
                            index + 1 < len(lines)
                            and _SETEXT.fullmatch(lines[index + 1].rstrip("\r\n"))
                        )
                    )
                ):
                    index += 1
                else:
                    break
        block_text = "".join(lines[start:index])
        location = BlockLocation(offset, offset + len(block_text), start + 1, index)
        blocks.append(ExtractedBlock(kind, block_text, location, level))
        if unclosed:
            diagnostics.append(
                ProcessingDiagnostic(
                    DiagnosticCode.UNCLOSED_CODE_FENCE,
                    "Code fence extends to end of source.",
                    location,
                )
            )
        offset += len(block_text)
    return tuple(blocks), tuple(diagnostics)
