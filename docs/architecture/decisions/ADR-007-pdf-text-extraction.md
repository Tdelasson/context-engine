# ADR-007: Optional PDF Text Extraction and Page Provenance

- **Status:** Accepted
- **Date:** 2026-10-10
- **Related issue:** #60

## Context

ADR-006 established reusable processing for text and Markdown. Initial M5 scope also
needs PDF text-layer extraction without flattening page provenance or claiming that
image content was interpreted.

## Decision

Add a PDF adapter behind the same source-processing contracts, using optional pypdf.
Append an optional page number to block locations, allow unspecified source encoding,
and add a configurable page limit. Preserve one block per original page, including
empty pages, with explicit separator whitespace blocks and extracted-text offsets.
Return page-empty and partial-extraction diagnostics separately from text. Reject
no-text, encrypted, malformed, missing-dependency, and limit-exceeding input explicitly.

Keep PDF parsing types and exceptions in the adapter. Use pypdf's default text extraction
with strict parsing; do not promise reading order or reconstruct tables. Byte/page/text
limits constrain accepted input and output but cannot guarantee parser memory or CPU
bounds. Configure larger PDF limits separately in the workbench. Preserve diagnostics
in catalog state and page locations in retrieval metadata.

## Alternatives

- Implement a PDF parser: rejected because font encodings and stream parsing are complex.
- Use OCR or layout models: deferred beyond initial text-layer scope.
- Flatten all pages: rejected because later chunks need original page provenance.
- Add subprocess isolation now: deferred; current limits are explicitly not hard quotas.

## Consequences

pypdf's BSD-3-Clause license and pure Python distribution provide a modest dependency
with useful extraction capability. Runtime installation is optional; development
installs include it for deterministic real-PDF tests. Text/Markdown callers retain
existing defaults and positional contracts. Extraction-empty pages are reported without
assuming every such page is a scan. Applications can distinguish partial extraction.
