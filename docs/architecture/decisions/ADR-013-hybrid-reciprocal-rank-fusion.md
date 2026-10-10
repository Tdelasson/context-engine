# ADR-013: Sequential hybrid fusion and observed source consistency

- Status: Accepted
- Date: 2026-10-10
- Issue: #67

## Context

Dense similarity and BM25 use incompatible scores. Retriever is synchronous and
adapter thread safety is not guaranteed. Independent searches can observe a
completed source replacement between calls even with identical filters and one
physical collection. Source lifecycle checks around each individual search do
not establish a common snapshot across two searches.

## Decision

Compose two injected Retriever dependencies in HybridRetriever, executing dense
then lexical sequentially. Separate budgets default to 20 each; final maximum
is 20, and request.top_k must not exceed that ceiling. Limits are integers in
[1,1000]; smoothing is an integer in [0,10000], initially 60. Configuration is
application-owned and hashed. The model continues proposing only a search query
through the existing search_documents tool, registry, policy and trace boundary.
Dense remains the workbench default.

Fuse in Python with equal-weight RRF: each branch contributes 1/(smoothing+rank),
with one-based ranks. Missing candidates contribute zero. Collapse identical
repeated records within a branch before assigning ranks; inconsistent repeats
fail. Deduplicate canonical document IDs across branches; identical text from
different IDs remains distinct. Canonical content and the entire metadata map
must agree, including provenance and source revision. Diagnostics remain separate.
Different observed source hashes for one source or different indexing generation
identities fail, including disjoint candidate lists. Sort equal fused scores by
chunk ID. Pure fusion returns the complete union; orchestration applies final K.
Fused scores are ranking values, not cosine similarities or probabilities.

Invalid records, filters, excessive candidates, nonfinite scores or branch
exceptions fail the entire operation with a typed branch identity. Empty
successful branches are valid. No degraded fallback is returned. Bounded iterator
consumption prevents an excessive dependency stream being silently accepted.
Diagnostics preserve upstream stages and expose original branch scores/ranks,
RRF contributions, candidate counts, configuration identity, and branch/fusion
timing. Native score kind comes from upstream diagnostics when supplied and is
otherwise explicitly unspecified; injected retrievers need not use cosine/BM25.

Add a minimal optional provider-independent visibility reader returning collection
index identity plus typed source manifests. Workbench binds it to the same combined
BM25 chunk store used by both branches. Read manifests before dense, between the
branches, and after lexical; pending operations, changed operation IDs/manifests,
wrong generations or candidates outside active revisions fail closed. Lifecycle
operation identities persist across completed replacements/deletions, so a
completed mutation between searches remains detectable. Tests exercise it against
actual Qdrant source replacement and deletion.

This observes consistency, **not atomic visibility or a database snapshot**.
A mutation after the final observation can make results stale, and out-of-band
writes bypassing the lifecycle cannot be detected reliably. The supported deployment
retains ADR-009's single-writer requirement. Without a reader, portable fixture or
immutable replay callers get only identifiable returned-record conflict checks;
they must supply a stable eligible corpus themselves and cannot claim common
snapshot guarantees. Do not combine independent mutable stores without a reader
that establishes their common generation/visibility.

## Alternatives and consequences

Adding BM25 and cosine scores assumes comparable scales; normalized or learned
weights add tuning and calibration outside this issue. Native Qdrant fusion would
couple orchestration to a provider. Concurrent calls might reduce latency but
introduce thread safety and timeout coordination without strengthening visibility.
Sequential calls have additive latency plus manifest scans; recorded benchmarks
quantify this cost. No new dependency, async runtime, write coordinator, or
atomic snapshot service is introduced.
