# Document chunking

Issue #61 adds a reusable `context_engine.knowledge.chunking` boundary:

```text
supplied bytes → processing → ProcessedSource → StructureAwareChunker
              → DocumentChunk[] → Document[] → Ingestor → embedding/vector store
```

Chunking performs no acquisition, inference, persistence, or UI operations. The
workbench continues to ingest whole documents. Replacement, stale-chunk deletion,
and collection migration require a separate ingestion lifecycle implementation.

## Usage and tokenizer compatibility

```python
from context_engine.knowledge.chunking import ChunkingConfig, StructureAwareChunker
from context_engine.knowledge.token_counting import TokenizerTokenCounter

# Obtain this already-loaded tokenizer from the configured embedding model.
# Its revision and preprocessing must match that model exactly.
counter = TokenizerTokenCounter(
    embedding_tokenizer,
    model_id="my-model",
    tokenizer_id="my-model-tokenizer@immutable-revision",
    max_input_tokens=embedding_runtime_limit,
    strip_text=True,
    lowercase=False,
)
config = ChunkingConfig(
    model_id="my-model",
    max_input_tokens=chosen_benchmark_limit,
    overlap_tokens=chosen_benchmark_overlap,
    document_prefix="",  # identical to LocalEmbeddingProviderConfig.document_prefix
    include_heading_context=True,
)
chunks = StructureAwareChunker(config, counter).chunk(processed_source)
documents = tuple(chunk.to_document() for chunk in chunks)
# Explicit caller-controlled ingestion, when its lifecycle is available:
# ingestor.ingest_documents(documents)
```

`TokenCounter` is a protocol for exact counts, including special tokens by default.
`TokenizerTokenCounter` calls an injected Hugging Face compatible tokenizer's
`encode(..., truncation=False, padding=False)`. It downloads nothing and loads no
model. SentenceTransformer's standard Transformer module strips text; match its
`do_lower_case` setting with `lowercase`. Other embedding preprocessing requires a
matching custom `TokenCounter`. Adapter identity includes these preprocessing flags.

Use the embedding runtime's actual limit. For SentenceTransformer, its configured
`max_seq_length` can be smaller than the underlying tokenizer's
`model_max_length`; the latter may also be a sentinel rather than a usable window.
The caller must bind the tokenizer, immutable revision, prefix, preprocessing, and
runtime limit to the same embedding configuration. Matching the model ID alone
cannot prove this binding. Models with custom tokenization need their own adapter.
No approximate character counter is provided as a production tokenizer.

There are no defaults for the token budget or overlap: set both explicitly and
record them for the later M5 retrieval benchmark. The configured limit must be
positive and no larger than the counter's actual runtime limit. Overlap must be
an integer from zero through `max_input_tokens - 1`.

Every `token_count` counts `document_prefix + chunk.content` with special tokens.
`to_document()` keeps the prefix out of `Document.content`: the existing embedding
provider adds it once. Heading context is already part of that content and budget.
The adapter does not authorize the provider to silently truncate chunks.

## Structure, fallback, and overlap

The versioned strategy is `structure-aware-v1`. Heading starts bound sections;
chunks combine blocks within a section and prefer paragraph endings, then sentence
endings when a whole section does not fit. The initial sentence rule recognizes
`.`, `!`, or `?` followed by whitespace; it is deterministic, not language-aware.
Markdown syntax, code, and whitespace remain unchanged in `source_text`.
Oversized code and unbroken text fall back to Python Unicode character boundaries.
Tokens are never decoded after slicing, so multibyte characters are not corrupted.
Combining sequences may span chunks; the exact original Unicode string is retained.

Exponential probing and bisection are sizing heuristics, and each candidate is
counted exactly. Tokenization need not be monotonic. The algorithm guarantees a
verified fitting prefix, rather than a globally longest prefix. It checks up to
16 nearby boundaries at each preferred structural level. If no initial probe
fits, an ascending search can find a longer prefix whose tokens merge more cheaply.
That rare fallback can be expensive for pathological tokenizers/impossible inputs;
processing resource limits remain important. A failure to fit raises a typed error.

A chunk's section metadata retains the complete heading hierarchy. Supplemental
heading context includes complete trailing headings that leave room for source
text; complete oldest headings are removed when the budget requires it. The
actual included `heading_context` is recorded explicitly. Source heading text is
always covered. Context is not repeated while splitting the heading itself.

Overlap takes a suffix of the previous chunk whose token count (without special
tokens or model prefix) is at most `overlap_tokens`. It is a maximum, not a target.
Overlap shrinks as necessary to allow new source text under the full input budget.
Section boundaries reset overlap. Every chunk advances the covered source end;
`overlap_start_offset` and `overlap_end_offset` record the actual repeated range.
All source characters, including whitespace and page separators, are covered.
Very long whitespace can therefore produce a whitespace passage with a tokenizer
that assigns tokens to it; source coverage takes precedence over dropping characters.

## Identity, locations, and Document mapping

`DocumentChunk` separates:

- `source.source_id`: caller-assigned logical identity;
- `source.content_sha256`: source-byte revision;
- `configuration_id`: hash of strategy/settings and tokenizer identity;
- `chunk_id`: SHA-256 of source identity/revision, configuration, index, offsets,
  and actual embedded content.

Repeat calls with the same source, configuration, and deterministic counter return
identical immutable chunks. Source revision, model/prefix/tokenizer settings, and
chunking settings affect the IDs. IDs do not create a source replacement policy.

`source_text` is exactly `ProcessedSource.text[start_offset:end_offset]`, using
zero-based, end-exclusive Python character offsets in `extracted_text`. `content`
adds the recorded heading context to this source slice. Supplemental headings
are distinguishable from source locations.

`spans` records every contributing block index and its clipped location, including
inclusive one-based lines and optional PDF `page_number`. PDF page separators are
represented by page-less whitespace spans; empty pages contribute no text span.
`page_numbers` lists all contributing nonempty pages, sorted and unique. Chunks
can span pages: page boundaries are not treated as semantic section boundaries.
`to_document()` uses `chunk_id` as the document ID and `content` as content, and
copies source identity/revision, configuration, spans, pages, sections, actual
context, counts, overlap, and source processing diagnostics into JSON-compatible metadata.
Partial PDF extraction warnings remain attached to every mapped chunk.

`ChunkingError.code` reports `invalid_configuration`, `invalid_source`,
`empty_content`, `incompatible_tokenizer`, `token_count_failed`, or `input_budget`.
The chunker rejects missing/inconsistent source coverage and malformed provenance.

## Validation and evaluation

Unit tests use a controlled Unicode-character tokenizer with explicit special
tokens. They cover exact limits, prefix accounting, headings/paragraphs, sentence
and code fallbacks, Unicode, long unbroken input, explicit overlap, stable and
changed IDs, malformed sources/configuration, counter failures, non-monotonic
counts, and multi-block/multi-page spans. A 50,000-character fixture bounds ordinary
probe work. No model downloads or inference are needed for these tests.

These tests establish mechanical correctness, not retrieval quality. Chunk size,
overlap, tokenizer/model, and `strategy_version` are exposed for the later M5
benchmark; no quality-selected defaults or quality improvement claims are made.
