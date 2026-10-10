"""Optional local PDF text-layer extraction; parser types stay inside this adapter."""

import importlib
from bisect import bisect_right
from dataclasses import replace
from hashlib import sha256
from io import BytesIO

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


def process_pdf(source: SourceInput, limits: ProcessingLimits | None = None) -> ProcessedSource:
    """Extract page text; limits do not bound parser decompression, memory, or CPU time."""
    limits = limits or ProcessingLimits()
    if source.format is not SourceFormat.PDF:
        raise ProcessingError(ProcessingErrorCode.UNSUPPORTED_FORMAT, "PDF format is required.")
    if len(source.content) > limits.max_bytes:
        raise ProcessingError(
            ProcessingErrorCode.BYTE_LIMIT,
            f"Source '{source.source_name}' exceeds {limits.max_bytes} bytes.",
        )
    try:
        parser = importlib.import_module("pypdf")
    except ImportError as exc:
        raise ProcessingError(
            ProcessingErrorCode.MISSING_DEPENDENCY,
            'PDF processing requires pypdf. Install with: pip install "context-engine[pdf]".',
        ) from exc
    blocks: list[ExtractedBlock] = []
    diagnostics: list[ProcessingDiagnostic] = []
    parts: list[str] = []
    offset = 0
    empty_pages = 0
    try:
        reader = parser.PdfReader(BytesIO(source.content), strict=True)
        if reader.is_encrypted:
            raise ProcessingError(
                ProcessingErrorCode.ENCRYPTED_PDF,
                "Encrypted PDFs are unsupported; supply an unencrypted PDF.",
            )
        page_count = len(reader.pages)
        if page_count > limits.max_pages:
            raise ProcessingError(
                ProcessingErrorCode.PAGE_LIMIT, f"PDF exceeds {limits.max_pages} pages."
            )
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if offset + (2 if parts else 0) + len(page_text) > limits.max_text_characters:
                raise ProcessingError(
                    ProcessingErrorCode.TEXT_LIMIT,
                    f"PDF exceeds {limits.max_text_characters} extracted characters.",
                )
            if parts:
                separator = "\n\n"
                blocks.append(
                    ExtractedBlock(
                        BlockKind.WHITESPACE,
                        separator,
                        BlockLocation(offset, offset + 2, 1, 1),
                    )
                )
                parts.append(separator)
                offset += 2
            location = BlockLocation(
                offset,
                offset + len(page_text),
                1,
                1,
                page_number=page_number,
            )
            blocks.append(ExtractedBlock(BlockKind.TEXT, page_text, location))
            parts.append(page_text)
            offset += len(page_text)
            if not page_text.strip():
                empty_pages += 1
                diagnostics.append(
                    ProcessingDiagnostic(
                        DiagnosticCode.EMPTY_PAGE,
                        f"Page {page_number} has no usable extracted text; it may be blank "
                        "or contain content without a text layer. OCR is not performed.",
                        location,
                    )
                )
    except ProcessingError:
        raise
    except Exception as exc:
        # PDF libraries expose varied parse/stream/codec failures. Do not leak library
        # exceptions or raw parser details (which may contain document text) to callers.
        raise ProcessingError(
            ProcessingErrorCode.MALFORMED_PDF, "PDF could not be parsed or its text extracted."
        ) from exc
    text = "".join(parts)
    if not text.strip():
        raise ProcessingError(
            ProcessingErrorCode.EMPTY_CONTENT,
            "PDF has no usable extracted text. Supply a PDF with a text layer; "
            "OCR is not performed.",
        )
    # Compute lines in the final representation: a page-ending CR may combine
    # with the separator LF, so page-local counts cannot be added safely.
    line_starts = [0]
    cursor = 0
    for extracted_line in text.splitlines(keepends=True):
        cursor += len(extracted_line)
        if cursor < len(text) or extracted_line.endswith(
            ("\n", "\r", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029")
        ):
            line_starts.append(cursor)
    page_locations: dict[int, BlockLocation] = {}
    for index, block in enumerate(blocks):
        location = replace(
            block.location,
            start_line=bisect_right(line_starts, block.location.start_offset),
            end_line=bisect_right(
                line_starts, max(block.location.start_offset, block.location.end_offset - 1)
            ),
        )
        blocks[index] = replace(block, location=location)
        if location.page_number is not None:
            page_locations[location.page_number] = location
    diagnostics = [
        replace(diagnostic, location=page_locations[diagnostic.location.page_number])
        if diagnostic.location is not None and diagnostic.location.page_number is not None
        else diagnostic
        for diagnostic in diagnostics
    ]
    if empty_pages:
        diagnostics.append(
            ProcessingDiagnostic(
                DiagnosticCode.PARTIAL_EXTRACTION,
                f"Partial extraction: {empty_pages} of {page_count} pages have no usable text.",
            )
        )
    return ProcessedSource(
        text,
        tuple(blocks),
        SourceProvenance(
            source.source_id,
            source.source_name,
            source.source_kind,
            source.format,
            sha256(source.content).hexdigest(),
            len(source.content),
            encoding=None,
        ),
        tuple(diagnostics),
    )
