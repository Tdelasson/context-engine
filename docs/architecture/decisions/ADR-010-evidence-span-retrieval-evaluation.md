# ADR-010: Source evidence spans for chunked retrieval evaluation

- **Status:** Accepted
- **Date:** 2026-10-10
- **Related issue:** #64

## Context

M4 document relevance cannot distinguish a supporting passage from an irrelevant
passage in the same source. Chunk IDs change with chunk settings. Evidence may
cross blocks/pages or require passages from several sources.

## Decision

Keep M4 artifacts unchanged. Add a focused M5 corpus with development and held-out
queries. Pin source-byte SHA-256, processing version/limits, and SHA-256 of canonical
processed Unicode text. Validate labels against actual processing before inference.

An `EvidenceItem` has a stable ID and one or more `EvidenceSpan` values in the
existing `extracted_text` representation. Each span binds source logical identity,
byte revision, and half-open Unicode character offsets. Multiple spans describe
one complete fact; multiple items describe separately required facts. They never
refer to chunk IDs. Repeated or overlapping label intervals use a union denominator.

Map the contributing `spans` of retrieved `DocumentChunk.to_document()` provenance
to labels with matching source identity and revision. Count union-covered labeled
characters cumulatively across the top K results. Default support requires 100%
coverage. Incidental overlap remains partial coverage. Duplicate/overlapping chunks
cannot add characters twice, but still occupy their actual ranking positions.

Report per-item fractional coverage, item recall, all-required coverage, and the
first prefix that completely covers any item. Macro query recall gives each
supported query equal weight; character coverage first averages its items, then
queries. All-required rate averages supported queries. Unsupported queries have
no recall/rank denominator and retain returned results and token measurements.
Retrieval alone makes no abstention or answer-correctness claim. Do not reuse M4
MRR/NDCG with ambiguous binary chunk relevance.

The runner uses the actual processing, exact-token chunking, source lifecycle,
embedding and Retriever interfaces. In-memory cosine isolates ranking; a separate
opt-in deployed Qdrant path verifies storage and provenance. Timing names identify
the backend. Estimate only searchable float32 dense-vector bytes; persisted index
bytes remain explicitly unavailable. Count independently tokenized passage content
using the identified embedding tokenizer, including its per-passage special tokens.
This does not promise the size of a future serialized prompt or context envelope.

## Alternatives

- Source-level relevance: rejected because irrelevant chunks would count as hits.
- Chunk-ID labels: rejected because different chunk settings need relabeling.
- Any overlap is relevant: rejected because a few incidental characters do not
  establish supporting evidence.
- General experiment tracking: deferred to M9; local JSON artifacts suffice here.

## Consequences

Labels remain reusable across chunk configurations and ranking methods. Strict
processed-text hashes intentionally fail if extraction changes. Full coverage is
conservative and may penalize passages that convey a fact through paraphrase.
A tiny controlled corpus is a diagnostic workload, not a production performance
claim. Defaults require broader development evidence; held-out outcomes cannot tune
them. Exact-token compatibility failures are recorded instead of truncating inputs.
