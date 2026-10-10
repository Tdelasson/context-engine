# ADR-009: Persisted source lifecycle and recoverable chunk replacement

- **Status:** Accepted
- **Date:** 2026-10-10
- **Related issue:** #62

## Context

Chunk IDs change with source revisions. Upserting alone leaves obsolete passages.
Session-only catalogs cannot delete or recover sources after restart. Qdrant does
not offer a transaction spanning chunk writes, deletes, and a source manifest.

## Decision

Use a provider-independent source lifecycle store contract alongside VectorStore.
Qdrant stores one non-searchable control point per logical source in the same
collection. It persists the previous and proposed revisions, chunk IDs, source
labels/diagnostics, operation ID, and phase. No second database is required.

Processing, exact-token chunking, and embedding finish before a mutation begins.
Replacement writes a `staging` manifest, upserts all new chunks, writes `ready`,
deletes obsolete IDs, then writes `active`. A staging failure leaves old chunks
untouched. Recovery discards staging chunks and restores the previous revision;
ready recovery finishes deletion and publishes the complete new revision. Delete
uses a ready manifest with no target; recovery repeats deletion idempotently.
Active tombstones retain the last operation identity for repeat deletion.

All lifecycle writes are acknowledged. An ambiguous/partial storage failure is
reported as failed with recovery required; it never masquerades as a committed
replacement. Search checks all manifests before and after the vector query. It
fails closed for pending operations or changed operation snapshots, and excludes
control points. This trades collection availability for simple recovery.

This is **not atomic visibility or a distributed transaction**. The supported
deployment has one writer per collection and a local Qdrant server. Coordinators
serialize mutations across sessions within a process; independent processes must not write concurrently.
External adapter mutations are outside this lifecycle. Do not bypass the coordinator.

M5 collections declare `m5-chunks-v1` and an effective indexing identity including
chunking/tokenizer identity and embedding configuration. M4 collections remain
usable by M4 consumers and are rejected by M5 consumers. Configuration changes
require explicitly selecting a new collection and reingesting original sources.

Workbench preloads use package-relative names in a preloaded namespace. Uploads
use exact validated filenames in one collection-wide upload namespace. Same-name
uploads replace that logical source; independent same-name sources need distinct
caller-supplied IDs or separate collections. Byte hashes identify revisions only.
Source reports and deletion use persisted manifests, including after restart.

## Alternatives and consequences

A separate SQLite journal adds a second durability boundary and can diverge from
remote Qdrant. Collection-per-revision aliases offer stronger switch semantics but
are disproportionate for independent sources in this local workbench. In-place
deletion followed by embedding loses data on inference failure and is rejected.

Control-point scans add query overhead; this approach targets a small local corpus.
Tombstones grow with distinct source IDs. Staging recovery preserves old revisions;
ready recovery completes the requested replacement/deletion. Recovery is explicit
and observable, requires no original bytes or model inference, and may itself fail.
Store snapshots and originals are still needed for recovery from database loss.
