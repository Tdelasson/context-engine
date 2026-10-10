# M5 paired lexical and dense retrieval experiment

Recorded 2026-10-10 for #66 on the frozen #64 evidence corpus. Raw output:
`results/m5-lexical-dense-128-16.json`.

Both strategies searched the same 33 committed chunks in one Qdrant 1.16.3
collection, with identical source revisions, canonical provenance, no metadata
filter, and source lifecycle visibility. Dense inference used local cached
MiniLM-L6-v2 revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` on CPU. Exact model
tokenizer chunk limit 128 / overlap 16; normalized embeddings. BM25 used the fixed
ADR-011 word/English Snowball configuration (k=1.2, b=0.75, average length 128,
empty stopwords). Qdrant client 1.16.2. Configuration identities and corpus hash
are recorded in raw output. The corpus and configuration were fixed before this
run; no held-out tuning was performed.

| Partition | Strategy | Evidence recall@1 | Evidence recall@5 | Evidence recall@10 |
| --- | --- | --- | --- | --- |
| Development (3 supported) | Dense | 0.667 | 1.000 | 1.000 |
| Development (3 supported) | BM25 | 0.667 | 1.000 | 1.000 |
| Held out (4 supported) | Dense | 0.500 | 1.000 | 1.000 |
| Held out (4 supported) | BM25 | 0.625 | 1.000 | 1.000 |

The two unsupported questions retain raw rankings but have no supported-evidence
recall denominator. These metrics measure complete coverage of labeled spans;
retrieving one chunk of a multipart answer gives partial evidence recall.

The technical identifier development question has first support rank 1 for both
strategies. On the held-out recovery question, BM25 top 1 covers both evidence
items, while dense top 1 covers one; both complete coverage by top 5. Both strategies
place the first safety evidence at rank 3 and require multiple chunks for the
compound cross-source question. The held-out offline paraphrase has support
rank 1 for both, so this corpus does not establish a semantic paraphrase advantage
for dense retrieval. BM25 is not required to win; these nine queries are too few
for a broad superiority claim or parameter selection.

Additional real native tokenizer tests expose identifier failures: Approval does
not retrieve ToolApprovalRequiredError, cafe does not retrieve café, and
punctuation-only queries return empty. Full technical names are case-insensitive;
underscores, hyphens and path delimiters split words. Therefore BM25 does not
implement exact identifier matching or automatic camelcase query expansion.

Median sequential query latency across nine questions: dense 26.9 ms, lexical 12.8 ms.
Dense includes query embedding plus database/manifest roundtrips; lexical includes
native encoding plus those roundtrips. These are single-pass warm local samples,
not repeat-run confidence estimates. Dense always runs first per query, so order
and cache effects remain uncontrolled. Combined ingestion took 2.987 s, including
processing, exact chunking, dense inference, native BM25 encoding and acknowledged
journal/point writes. BM25's incremental encoding cost and durable index bytes
were not separately measured; combined indexing cost cannot establish lexical-only
indexing speed or storage savings. No cloud inference or model downloads occurred
in this run.

Reproduce with a local native Qdrant server and the cached model snapshot:

```bash
HF_HUB_OFFLINE=1 python -m benchmarks.benchmark_lexical_retrieval \
  --model-reference /path/to/cached/minilm/snapshot \
  --qdrant-url http://localhost:6333 \
  --output docs/experiments/results/m5-lexical-dense-128-16.json
```

The runner creates a unique collection and removes it in a final cleanup. Default
CI uses controlled fixtures; recorded measurements are separate real execution.
