import importlib
from dataclasses import replace
from hashlib import sha256
from types import ModuleType

import pytest

from context_engine.knowledge.processing import (
    DiagnosticCode,
    ProcessingError,
    ProcessingErrorCode,
    ProcessingLimits,
    SourceFormat,
    SourceInput,
    process_pdf,
    process_source,
    to_document,
)
from tests.pdf_fixtures import make_pdf


def _source(content: bytes) -> SourceInput:
    return SourceInput("pdf-source", "facts.pdf", content, SourceFormat.PDF)


def test_pdf_pages_provenance_and_unicode() -> None:
    content = make_pdf(("First page: øresund", "Second: COBALT-742"))
    result = process_source(_source(content))
    pages = [block for block in result.blocks if block.location.page_number]
    assert [block.location.page_number for block in pages] == [1, 2]
    assert result.text == "First page: øresund\n\nSecond: COBALT-742"
    assert "".join(block.text for block in result.blocks) == result.text
    for block in result.blocks:
        assert result.text[block.location.start_offset : block.location.end_offset] == block.text
    assert result.provenance.content_sha256 == sha256(content).hexdigest()
    assert result.provenance.encoding is None
    metadata = to_document(result).metadata_as_mapping()
    assert metadata["page_numbers"] == [1, 2]
    assert metadata["source_page_count"] == 2
    locations = metadata["source_locations"]
    assert isinstance(locations, list)
    second_page = locations[1]
    assert isinstance(second_page, dict)
    assert second_page["page_number"] == 2


def test_blank_pages_report_partial_extraction_and_keep_original_numbers() -> None:
    result = process_pdf(_source(make_pdf((None, "Useful text", None))))
    assert [
        block.location.page_number for block in result.blocks if block.location.page_number
    ] == [1, 2, 3]
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        DiagnosticCode.EMPTY_PAGE,
        DiagnosticCode.EMPTY_PAGE,
        DiagnosticCode.PARTIAL_EXTRACTION,
    ]
    assert [
        diagnostic.location.page_number for diagnostic in result.diagnostics if diagnostic.location
    ] == [1, 3]
    assert "Partial extraction" not in result.text


@pytest.mark.parametrize(
    ("content", "code"),
    [
        (b"not a PDF", ProcessingErrorCode.MALFORMED_PDF),
        (make_pdf((None,)), ProcessingErrorCode.EMPTY_CONTENT),
        (make_pdf(("Secret",), encrypted=True), ProcessingErrorCode.ENCRYPTED_PDF),
    ],
)
def test_pdf_failures_are_typed(content: bytes, code: ProcessingErrorCode) -> None:
    with pytest.raises(ProcessingError) as exc:
        process_source(_source(content))
    assert exc.value.code is code


def test_pdf_exact_limit_boundaries() -> None:
    source = _source(make_pdf(("abc", "def")))
    limits = ProcessingLimits(max_bytes=len(source.content), max_text_characters=8, max_pages=2)
    assert process_pdf(source, limits).text == "abc\n\ndef"
    for limit, code in [
        (replace(limits, max_bytes=len(source.content) - 1), ProcessingErrorCode.BYTE_LIMIT),
        (replace(limits, max_text_characters=7), ProcessingErrorCode.TEXT_LIMIT),
        (replace(limits, max_pages=1), ProcessingErrorCode.PAGE_LIMIT),
    ]:
        with pytest.raises(ProcessingError) as exc:
            process_pdf(source, limit)
        assert exc.value.code is code


def test_missing_optional_pdf_dependency_is_actionable(monkeypatch: pytest.MonkeyPatch) -> None:
    original = importlib.import_module

    def missing(name: str) -> ModuleType:
        if name == "pypdf":
            raise ModuleNotFoundError(name)
        return original(name)

    monkeypatch.setattr(importlib, "import_module", missing)
    with pytest.raises(ProcessingError, match="context-engine\\[pdf\\]") as exc:
        process_pdf(_source(b"%PDF"))
    assert exc.value.code is ProcessingErrorCode.MISSING_DEPENDENCY


def test_pdf_rejects_wrong_format() -> None:
    with pytest.raises(ProcessingError) as exc:
        process_pdf(SourceInput("text", "text", b"text", SourceFormat.TEXT))
    assert exc.value.code is ProcessingErrorCode.UNSUPPORTED_FORMAT


def test_real_image_only_pdf_has_explicit_no_text_outcome() -> None:
    from tests.pdf_fixtures import make_image_pdf

    with pytest.raises(ProcessingError, match="no usable extracted text") as exc:
        process_pdf(_source(make_image_pdf()))
    assert exc.value.code is ProcessingErrorCode.EMPTY_CONTENT


@pytest.mark.parametrize(
    "page_text", ["first\r\nsecond\r\n", "first\u2028second\u2028", "", "first"]
)
def test_locations_follow_extracted_splitlines_with_empty_pages(
    monkeypatch: pytest.MonkeyPatch,
    page_text: str,
) -> None:
    from types import SimpleNamespace

    texts = (page_text, "", "last")
    reader = SimpleNamespace(
        is_encrypted=False,
        pages=[SimpleNamespace(extract_text=lambda text=text: text) for text in texts],
    )
    monkeypatch.setattr(
        importlib, "import_module", lambda _: SimpleNamespace(PdfReader=lambda *a, **k: reader)
    )
    result = process_pdf(_source(b"fixture"))
    for block in result.blocks:
        start = block.location.start_offset
        assert block.location.start_line == len(result.text[:start].splitlines()) + (
            1
            if not result.text[:start] or result.text[:start].endswith(("\n", "\r", "\u2028"))
            else 0
        )


def test_pdf_line_spans_use_final_combined_text_across_crlf_page_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    texts = ("first\r", "second\u2028third\n", "", "last\r\n")
    reader = SimpleNamespace(
        is_encrypted=False,
        pages=[SimpleNamespace(extract_text=lambda text=text: text) for text in texts],
    )
    monkeypatch.setattr(
        importlib, "import_module", lambda _: SimpleNamespace(PdfReader=lambda *a, **k: reader)
    )
    result = process_pdf(_source(b"fixture"))
    assert result.text == "\n\n".join(texts)
    expected = [(1, 1), (1, 2), (3, 4), (5, 6), (7, 7), (7, 8), (9, 9)]
    assert [
        (block.location.start_line, block.location.end_line) for block in result.blocks
    ] == expected
    assert result.diagnostics[0].location == result.blocks[4].location
    for block in result.blocks:
        assert result.text[block.location.start_offset : block.location.end_offset] == block.text
