# ADR-008: Deterministic Structure-Aware Document Chunking

- **Status:** Accepted
- **Date:** 2026-10-10
- **Related issues:** #59, #60, #61

## Context

Source processing already produces extracted text, structural blocks, and source
provenance. Searchable passages may combine or split those blocks, while embedding
models impose limits after prefixes, heading context, and special tokens are added.
PDF pages supply citation locations but are not reliable semantic sections.

## Decision

`knowledge/chunking.py` owns immutable chunk/configuration contracts and deterministic
structure-aware splitting. Processing precedes chunking; embedding and indexing follow
it explicitly. Chunking never calls models or persistence. Whole-document ingestion
remains available until a separate ingestion lifecycle supports chunk replacement,
deletion, and migration.

Require explicit token budget and overlap. Inject an exact model-compatible counter;
the optional tokenizer adapter uses an already-loaded tokenizer without truncation,
including the configured embedding preprocessing. Count the complete prefix, included
heading context, passage, and special tokens. Reject mismatched model IDs/runtime limits
and malformed count results; the caller binds actual tokenizer revision and embedding
settings. Do not infer the SentenceTransformer runtime limit from an HF sentinel.

Prefer headings, paragraphs, and sentences; oversized text/code uses unchanged Unicode
source slices. Exponential/bisection sizing is a heuristic, with exact validation of
all selected candidates and a rare ascending fallback. Token counts need not be
monotonic, and finding the globally longest valid prefix is unnecessary. Bound ordinary
structural candidate work. Retain full heading metadata, and record the supplemental
heading context actually included within the input budget.

Preserve exact extracted-text offsets, clipped contributing block/line/page locations,
and explicit actual overlap spans. Combine PDF pages when the budget permits, without
inventing headings. Chunk IDs hash source logical identity, source-byte revision,
versioned settings/tokenizer identity, position, and embedded content. Provide an
explicit `DocumentChunk.to_document()` mapping without adding the provider prefix twice.

## Alternatives

- Fixed characters or an approximate tokenizer: rejected because model input limits
  would remain unverified.
- Token slicing followed by decoding: rejected because it may corrupt Unicode or
  change the exact source representation needed for citations.
- Exhaustively find the longest fitting prefix: rejected for ordinary operation
  because repeated counting across large pages can become prohibitively expensive.
- Assume pages are sections: rejected because paragraph flow can cross PDF pages.
- LLM or semantic-model chunking: excluded from the initial deterministic strategy.
- Integrate chunk ingestion into the workbench immediately: deferred because stale
  revision deletion and collection migration are separate lifecycle responsibilities.

## Consequences

Chunk correctness is independently testable without inference or downloads. Consumers
must supply a genuinely compatible tokenizer/runtime configuration and preserve its
identity. A pathological tokenizer or impossible input may trigger an expensive rare
fallback before a typed failure; existing processing limits bound supplied input.

Settings and strategy version are observable for later M5 benchmarking. Unit tests
prove budget/coverage/provenance invariants, not improved retrieval quality. The first
strategy uses simple punctuation rules and can split combining sequences while
preserving all Unicode characters. Its deterministic passage IDs do not replace an
ingestion lifecycle policy.
