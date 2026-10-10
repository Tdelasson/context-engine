# ADR-006: Knowledge Document Processing Boundary

- **Status:** Accepted
- **Date:** 2026-10-10
- **Related issue:** #59

## Context

The workbench currently owns UTF-8 decoding and upload validation. M5 needs reusable
source processing before chunking without moving parsing into retrieval or model providers.

## Decision

`knowledge/processing` accepts supplied bytes with caller-assigned stable source IDs,
names, kinds, and explicit formats. It validates resource limits and UTF-8, extracts
unchanged text (except a leading BOM), and identifies structural blocks deterministically.
It never acquires files, calls models, or writes an index.

Provenance separates logical source identity from a full SHA-256 revision of the input
bytes. Block offsets are zero-based, end-exclusive Python Unicode character offsets
in `ProcessedSource.text`, after BOM removal; line numbers are one-based and inclusive,
using Python `str.splitlines()` boundaries.
Markdown syntax, line endings, whitespace, and code remain in that representation.
The reader recognizes ATX/setext headings and fenced/indented code. Other Markdown
is preserved as text; this is a structural reader, not a full CommonMark renderer.

An explicit conversion produces one retrieval `Document`, carrying provenance in
metadata and using the stable source ID as its document ID. `Ingestor` continues to
embed and upsert whole documents. Knowledge owns source interpretation; retrieval
owns embedding, indexing, and search. Chunking and indexing lifecycle remain separate.

The workbench owns acquisition, filename validation, upload-count limits, and UI error
reporting. Its upload namespace derives stable IDs from filenames, so re-uploading
changed bytes under the same name replaces the corresponding whole-document record.
Names distinguish uploads within the current catalog; they are not global source IDs.
Preloaded IDs remain unchanged. Existing persisted content-derived upload IDs are not
migrated automatically; old sessions should clear their uploads before using this version.

## Alternatives

- Keep parsing in the workbench: rejected because other ingestion clients need it.
- Parse in `Ingestor` or embedding providers: rejected because it mixes responsibilities.
- Render Markdown to plain text with a new parser dependency: deferred because preserving
  source syntax gives exact citation locations and avoids introducing a second representation.
- Add a document database or chunking now: deferred to their own requirements.

## Consequences

Processing is local, deterministic, independently testable, and requires no new dependency.
Applications must explicitly assign logical source identities. Structural blocks supply
locations for later chunking, but impose no chunk sizes or retrieval strategy. Whole-document
text and the existing tool-mediated retrieval path remain intact.
