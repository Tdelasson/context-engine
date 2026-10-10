from hashlib import sha256

import pytest

from context_engine.knowledge.processing import (
    BlockKind,
    DiagnosticCode,
    ProcessingError,
    ProcessingErrorCode,
    ProcessingLimits,
    SourceFormat,
    SourceInput,
    process_source,
    to_document,
)


def _source(content: bytes, format: SourceFormat = SourceFormat.TEXT) -> SourceInput:
    return SourceInput("logical-id", "notes", content, format, "test")


def test_text_is_lossless_deterministic_and_has_byte_provenance() -> None:
    content = "  Øresund 🐍\r\n\tsecond\n\n".encode()
    source = _source(content)
    result = process_source(source)
    assert process_source(source) == result
    assert result.text == content.decode()
    assert result.diagnostics == ()
    assert result.provenance.source_id == "logical-id"
    assert result.provenance.source_name == "notes"
    assert result.provenance.source_kind == "test"
    assert result.provenance.content_sha256 == sha256(content).hexdigest()
    assert result.provenance.byte_length == len(content)
    assert result.blocks[0].kind == BlockKind.TEXT
    assert result.blocks[0].location.end_offset == len(result.text)
    assert result.blocks[0].location.end_line == 3


def test_revision_changes_do_not_change_logical_identity_or_document_id() -> None:
    first = process_source(_source(b"first"))
    second = process_source(_source(b"second"))
    assert first.provenance.source_id == second.provenance.source_id
    assert first.provenance.content_sha256 != second.provenance.content_sha256
    document = to_document(second)
    assert document.document_id == to_document(first).document_id == "logical-id"
    assert document.content == "second"
    assert document.metadata_as_mapping() == {
        "source_id": "logical-id",
        "source_name": "notes",
        "source_kind": "test",
        "source_format": "text",
        "content_sha256": sha256(b"second").hexdigest(),
        "source_byte_length": 6,
        "source_encoding": "utf-8",
        "text_representation": "extracted_text",
    }
    other = SourceInput("other-id", "notes", b"second", SourceFormat.TEXT)
    assert process_source(other).provenance.source_id != second.provenance.source_id


def test_bom_removal_and_unicode_character_offsets() -> None:
    source = _source(b"\xef\xbb\xbf" + "# Ø🐍\r\n\r\nword".encode(), SourceFormat.MARKDOWN)
    result = process_source(source)
    assert result.text == "# Ø🐍\r\n\r\nword"
    assert result.diagnostics[0].code == DiagnosticCode.BOM_REMOVED
    assert result.blocks[0].location.end_offset == 6
    assert result.provenance.content_sha256 == sha256(source.content).hexdigest()


def test_markdown_headings_code_and_exact_block_locations() -> None:
    text = (
        "# Heading\n\nParagraph  \nnext line\n\nTitle\n=====\n"
        "~~~python\n# code\n~~~\n    indented\n"
    )
    result = process_source(_source(text.encode(), SourceFormat.MARKDOWN))
    assert result.text == text
    assert [block.kind for block in result.blocks] == [
        BlockKind.HEADING,
        BlockKind.WHITESPACE,
        BlockKind.TEXT,
        BlockKind.WHITESPACE,
        BlockKind.HEADING,
        BlockKind.CODE,
        BlockKind.CODE,
    ]
    assert [block.heading_level for block in result.blocks if block.kind == BlockKind.HEADING] == [
        1,
        1,
    ]
    assert result.blocks[2].text == "Paragraph  \nnext line\n"
    assert result.blocks[5].text == "~~~python\n# code\n~~~\n"
    assert result.blocks[5].location.start_line == 8
    assert result.blocks[5].location.end_line == 10
    assert "".join(block.text for block in result.blocks) == text
    for index, block in enumerate(result.blocks):
        span = block.location
        assert span.representation == "extracted_text"
        assert text[span.start_offset : span.end_offset] == block.text
        if index:
            assert span.start_offset == result.blocks[index - 1].location.end_offset
    assert result.diagnostics == ()


@pytest.mark.parametrize(
    "text",
    [
        "```python\nbody\n",
        "~~~~\n~~~\nstill code",
        "```\n~~~~\n",
        "```\n``` trailing\n",
    ],
)
def test_unclosed_code_fence_preserves_input_with_diagnostic(text: str) -> None:
    result = process_source(_source(text.encode(), SourceFormat.MARKDOWN))
    assert result.text == text
    assert len(result.blocks) == 1
    assert result.blocks[0].kind == BlockKind.CODE
    assert result.diagnostics[0].code == DiagnosticCode.UNCLOSED_CODE_FENCE
    assert result.diagnostics[0].location == result.blocks[0].location
    assert process_source(_source(text.encode(), SourceFormat.MARKDOWN)) == result


@pytest.mark.parametrize(
    ("text", "kind", "level"),
    [
        ("## Title", BlockKind.HEADING, 2),
        ("Title\n---", BlockKind.HEADING, 2),
        ("#not a heading", BlockKind.TEXT, None),
        ("####### Title", BlockKind.TEXT, None),
        ("    # code", BlockKind.CODE, None),
        ("```\nbody\n````\n", BlockKind.CODE, None),
        ("```bad`info\n", BlockKind.TEXT, None),
    ],
)
def test_markdown_structural_edges(text: str, kind: BlockKind, level: int | None) -> None:
    result = process_source(_source(text.encode(), SourceFormat.MARKDOWN))
    assert result.blocks[0].kind == kind
    assert result.blocks[0].heading_level == level
    assert "".join(block.text for block in result.blocks) == text


@pytest.mark.parametrize(
    ("content", "code"),
    [
        (b"", ProcessingErrorCode.EMPTY_CONTENT),
        (b" \t\r\n", ProcessingErrorCode.EMPTY_CONTENT),
        (b"\xef\xbb\xbf", ProcessingErrorCode.EMPTY_CONTENT),
        (b"\xff", ProcessingErrorCode.INVALID_ENCODING),
        (b"\xc3", ProcessingErrorCode.INVALID_ENCODING),
    ],
)
def test_invalid_content_has_typed_failure(content: bytes, code: ProcessingErrorCode) -> None:
    with pytest.raises(ProcessingError) as exc:
        process_source(_source(content))
    assert exc.value.code == code


def test_limits_are_inclusive_and_characters_are_distinct_from_bytes() -> None:
    source = _source("Ø🐍".encode())
    assert (
        process_source(source, ProcessingLimits(max_bytes=6, max_text_characters=2)).text == "Ø🐍"
    )
    for limits, code in [
        (ProcessingLimits(max_bytes=5), ProcessingErrorCode.BYTE_LIMIT),
        (ProcessingLimits(max_text_characters=1), ProcessingErrorCode.TEXT_LIMIT),
    ]:
        with pytest.raises(ProcessingError) as exc:
            process_source(source, limits)
        assert exc.value.code == code
    assert process_source(_source(b"\xef\xbb\xbfa"), ProcessingLimits(4, 1)).text == "a"


@pytest.mark.parametrize(("max_bytes", "max_text"), [(0, 1), (1, 0), (-1, 1), (1, -1)])
def test_invalid_limits_are_rejected(max_bytes: int, max_text: int) -> None:
    with pytest.raises(ProcessingError) as exc:
        ProcessingLimits(max_bytes, max_text)
    assert exc.value.code == ProcessingErrorCode.INVALID_CONFIGURATION


def test_unsupported_format_is_rejected() -> None:
    with pytest.raises(ProcessingError) as exc:
        SourceInput("id", "name", b"text", "pdf")  # type: ignore[arg-type]
    assert exc.value.code == ProcessingErrorCode.UNSUPPORTED_FORMAT


@pytest.mark.parametrize(
    ("source_id", "source_name", "source_kind"),
    [
        ("", "name", "supplied"),
        ("id", " ", "supplied"),
        ("id", "name", ""),
    ],
)
def test_invalid_source_identifiers_are_rejected(
    source_id: str,
    source_name: str,
    source_kind: str,
) -> None:
    with pytest.raises(ProcessingError) as exc:
        SourceInput(source_id, source_name, b"text", SourceFormat.TEXT, source_kind)
    assert exc.value.code == ProcessingErrorCode.INVALID_INPUT
