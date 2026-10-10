"""Controlled tokenizer fixtures test lossless chunking without model downloads."""

from dataclasses import replace
from typing import Any

import pytest

from context_engine.knowledge.chunking import (
    ChunkingConfig,
    ChunkingError,
    ChunkingErrorCode,
    DocumentChunk,
    StructureAwareChunker,
)
from context_engine.knowledge.processing import SourceFormat, SourceInput, process_source
from context_engine.knowledge.processing.contracts import (
    BlockKind,
    BlockLocation,
    ExtractedBlock,
    ProcessedSource,
)
from context_engine.knowledge.token_counting import TokenizerTokenCounter


class CharacterTokenizer:
    """Deliberately controlled tokenizer: one Unicode character per token plus BOS/EOS."""

    def encode(
        self, text: str, *, add_special_tokens: bool, truncation: bool, padding: bool
    ) -> list[int]:
        assert truncation is False
        assert padding is False
        return [ord(c) for c in text] + ([1, 2] if add_special_tokens else [])


def counter(limit: int = 100) -> TokenizerTokenCounter:
    return TokenizerTokenCounter(
        CharacterTokenizer(),
        model_id="fixture",
        tokenizer_id="character-v1",
        max_input_tokens=limit,
        strip_text=False,
    )


def source(text: str, *, markdown: bool = False) -> ProcessedSource:
    return process_source(
        SourceInput(
            "source",
            "notes.md",
            text.encode(),
            SourceFormat.MARKDOWN if markdown else SourceFormat.TEXT,
        )
    )


def chunker(limit: int, overlap: int = 0, **kwargs: Any) -> StructureAwareChunker:
    return StructureAwareChunker(ChunkingConfig("fixture", limit, overlap, **kwargs), counter())


def assert_coverage(processed: ProcessedSource, chunks: tuple[DocumentChunk, ...]) -> None:
    end = 0
    for chunk in chunks:
        assert chunk.source_text == processed.text[chunk.start_offset : chunk.end_offset]
        assert chunk.start_offset <= end < chunk.end_offset
        if chunk.start_offset < end:
            assert (chunk.overlap_start_offset, chunk.overlap_end_offset) == (
                chunk.start_offset,
                end,
            )
        else:
            assert chunk.overlap_start_offset is chunk.overlap_end_offset is None
        assert chunk.token_count <= chunk.config.max_input_tokens
        assert (
            "".join(
                processed.text[s.location.start_offset : s.location.end_offset] for s in chunk.spans
            )
            == chunk.source_text
        )
        end = chunk.end_offset
    assert end == len(processed.text)


@pytest.mark.parametrize(
    "text",
    [
        "short",
        "abcdefghijk",
        "🙂漢字é\u0301🚀abcdef",
        "x" * 90,
        "A very long sentence without a stop " * 3,
        "First. Second. Third. Fourth.",
        "```py\n" + "print('🙂')\n" * 8 + "```\n",
    ],
)
def test_fallback_covers_unicode_and_code(text: str) -> None:
    processed = source(text, markdown=True)
    chunks = chunker(16).chunk(processed)
    assert_coverage(processed, chunks)
    assert all(c.token_count == len(c.content) + 2 for c in chunks)


def test_exact_boundary_prefix_and_specials() -> None:
    processed = source("abcdef")
    chunks = chunker(10, document_prefix="P:").chunk(processed)
    assert len(chunks) == 1
    assert chunks[0].token_count == 10
    assert chunks[0].to_document().content == "abcdef"
    assert_coverage(processed, chunker(9, document_prefix="P:").chunk(processed))


def test_headings_sections_and_paragraphs() -> None:
    processed = source(
        "# One\n\nFirst paragraph.\n\nSecond paragraph.\n\n# Two\n\nLast.\n", markdown=True
    )
    chunks = chunker(35).chunk(processed)
    assert_coverage(processed, chunks)
    assert chunks[0].source_text.endswith("First paragraph.\n\n")
    assert chunks[1].heading_context == "# One\n\n"
    assert chunks[1].section_headings == ("# One",)
    assert chunks[2].source_text.startswith("# Two")
    assert chunks[2].heading_context == ""
    assert chunks[2].section_headings == ("# Two",)


def test_huge_heading_kept_in_source_and_metadata_without_overflow() -> None:
    processed = source("# " + "h" * 40 + "\n\nbody content\n", markdown=True)
    chunks = chunker(12).chunk(processed)
    assert_coverage(processed, chunks)
    assert chunks[-1].section_headings == ("# " + "h" * 40,)
    assert chunks[-1].heading_context == ""


def test_overlap_is_explicit_and_never_stalls() -> None:
    processed = source("abcdefghijklmno")
    chunks = chunker(8, overlap=5, document_prefix="P").chunk(processed)
    assert_coverage(processed, chunks)
    assert len(chunks) > 1
    assert all(len(c.source_text) <= 5 for c in chunks)
    assert any(c.overlap_start_offset is not None for c in chunks)


def test_stability_and_configuration_and_revision_identity() -> None:
    processed = source("abcdefghijklmno")
    original = chunker(8).chunk(processed)
    assert original == chunker(8).chunk(processed)
    variants = [
        chunker(9).chunk(processed),
        chunker(8, overlap=1).chunk(processed),
        chunker(8, document_prefix="P").chunk(processed),
        chunker(8).chunk(
            replace(processed, provenance=replace(processed.provenance, source_id="other"))
        ),
        chunker(8).chunk(source("abcdefghijklmnp")),
    ]
    assert all(original[0].chunk_id != variant[0].chunk_id for variant in variants)
    other_tokenizer = TokenizerTokenCounter(
        CharacterTokenizer(), model_id="fixture", tokenizer_id="v2", max_input_tokens=100
    )
    assert (
        StructureAwareChunker(original[0].config, other_tokenizer).chunk(processed)[0].chunk_id
        != original[0].chunk_id
    )


def test_multiple_blocks_and_pages_and_empty_page() -> None:
    processed = source("first\n\n\n\nlast")
    processed = replace(
        processed,
        blocks=(
            ExtractedBlock(BlockKind.TEXT, "first", BlockLocation(0, 5, 1, 1, page_number=1)),
            ExtractedBlock(BlockKind.WHITESPACE, "\n\n", BlockLocation(5, 7, 1, 2)),
            ExtractedBlock(BlockKind.TEXT, "", BlockLocation(7, 7, 3, 3, page_number=2)),
            ExtractedBlock(BlockKind.WHITESPACE, "\n\n", BlockLocation(7, 9, 3, 4)),
            ExtractedBlock(BlockKind.TEXT, "last", BlockLocation(9, 13, 5, 5, page_number=3)),
        ),
    )
    chunks = chunker(30).chunk(processed)
    assert_coverage(processed, chunks)
    assert chunks[0].page_numbers == (1, 3)
    assert len(chunks[0].spans) == 4
    metadata = chunks[0].to_document().metadata_as_mapping()
    assert metadata["page_numbers"] == [1, 3]
    assert metadata["text_representation"] == "extracted_text"
    assert metadata["source_id"] == "source"
    configuration = metadata["chunk_configuration"]
    assert isinstance(configuration, dict)
    assert configuration["strategy_version"] == "structure-aware-v1"


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(max_input_tokens=0),
        dict(max_input_tokens=True),
        dict(overlap_tokens=-1),
        dict(overlap_tokens=8),
        dict(overlap_tokens=True),
        dict(model_id=""),
        dict(strategy_version="unknown"),
    ],
)
def test_invalid_configuration(kwargs: dict[str, Any]) -> None:
    config: dict[str, Any] = dict(model_id="fixture", max_input_tokens=8, overlap_tokens=0)
    config.update(kwargs)
    with pytest.raises(ChunkingError) as error:
        ChunkingConfig(**config)
    assert error.value.code == ChunkingErrorCode.INVALID_CONFIGURATION


def test_empty_and_inconsistent_processed_sources() -> None:
    processed = source("abcdef")
    bad = [
        replace(processed, blocks=()),
        replace(processed, blocks=(replace(processed.blocks[0], text="wrong"),)),
        replace(
            processed, blocks=(replace(processed.blocks[0], location=BlockLocation(1, 6, 1, 1)),)
        ),
    ]
    for invalid in bad:
        with pytest.raises(ChunkingError) as error:
            chunker(8).chunk(invalid)
        assert error.value.code == ChunkingErrorCode.INVALID_SOURCE
    with pytest.raises(ChunkingError) as error:
        chunker(8).chunk(replace(processed, text=""))
    assert error.value.code == ChunkingErrorCode.EMPTY_CONTENT


def test_incompatible_counter_and_impossible_budget() -> None:
    with pytest.raises(ChunkingError) as error:
        StructureAwareChunker(ChunkingConfig("wrong", 10, 0), counter())
    assert error.value.code == ChunkingErrorCode.INCOMPATIBLE_TOKENIZER
    with pytest.raises(ChunkingError):
        StructureAwareChunker(ChunkingConfig("fixture", 11, 0), counter(10))
    with pytest.raises(ChunkingError) as error:
        chunker(3, document_prefix="prefix").chunk(source("a"))
    assert error.value.code == ChunkingErrorCode.INPUT_BUDGET


def test_counter_errors_are_typed() -> None:
    class BadCounter:
        model_id = "fixture"
        tokenizer_id = "bad"
        max_input_tokens = 100

        def count_tokens(self, text: str, *, add_special_tokens: bool = True) -> int:
            return -1

    with pytest.raises(ChunkingError) as error:
        StructureAwareChunker(ChunkingConfig("fixture", 8, 0), BadCounter()).chunk(source("a"))
    assert error.value.code == ChunkingErrorCode.TOKEN_COUNT_FAILED

    class RaisingCounter(BadCounter):
        def count_tokens(self, text: str, *, add_special_tokens: bool = True) -> int:
            raise RuntimeError("error")

    with pytest.raises(ChunkingError) as error:
        StructureAwareChunker(ChunkingConfig("fixture", 8, 0), RaisingCounter()).chunk(source("a"))
    assert error.value.code == ChunkingErrorCode.TOKEN_COUNT_FAILED


def test_non_monotonic_token_counts_do_not_assume_binary_search() -> None:
    class MergingCounter:
        model_id = "fixture"
        tokenizer_id = "nonmonotonic"
        max_input_tokens = 100

        def count_tokens(self, text: str, *, add_special_tokens: bool = True) -> int:
            return 3 if text == "abcdef" else len(text) + 2

    chunks = StructureAwareChunker(ChunkingConfig("fixture", 4, 0), MergingCounter()).chunk(
        source("abcdefgh")
    )
    assert all(c.token_count <= 4 for c in chunks)
    assert_coverage(source("abcdefgh"), chunks)


def test_tokenizer_preprocessing_is_explicit_and_identity_sensitive() -> None:
    tokenizer = CharacterTokenizer()
    count = TokenizerTokenCounter(
        tokenizer, model_id="fixture", tokenizer_id="v1", max_input_tokens=10, lowercase=True
    )
    assert count.count_tokens(" A ") == 3
    assert count.count_tokens(" A ", add_special_tokens=False) == 1
    assert "strip=true;lowercase=true" in count.tokenizer_id
    with pytest.raises(ChunkingError):
        TokenizerTokenCounter(tokenizer, model_id="fixture", tokenizer_id="v1", max_input_tokens=0)


def test_long_unbroken_text_uses_bounded_probes() -> None:
    class MeasuredCounter:
        model_id = "fixture"
        tokenizer_id = "measured"
        max_input_tokens = 100
        calls = 0
        characters = 0

        def count_tokens(self, text: str, *, add_special_tokens: bool = True) -> int:
            self.calls += 1
            self.characters += len(text)
            return len(text) + (2 if add_special_tokens else 0)

    tokenizer = MeasuredCounter()
    processed = source("x" * 50000)
    chunks = StructureAwareChunker(ChunkingConfig("fixture", 100, 0), tokenizer).chunk(processed)
    assert_coverage(processed, chunks)
    assert tokenizer.calls < len(chunks) * 20
    assert tokenizer.characters < len(processed.text) * 20


def test_longer_prefix_can_fit_when_first_character_does_not() -> None:
    class MergingCounter:
        model_id = "fixture"
        tokenizer_id = "first-character-expensive"
        max_input_tokens = 100

        def count_tokens(self, text: str, *, add_special_tokens: bool = True) -> int:
            return 20 if text == "a" else len(text) + 2

    processed = source("abcdefgh")
    chunks = StructureAwareChunker(ChunkingConfig("fixture", 4, 0), MergingCounter()).chunk(
        processed
    )
    assert chunks[0].source_text == "ab"
    assert_coverage(processed, chunks)
