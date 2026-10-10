# M5 dense, lexical and hybrid comparison

Recorded 2026-10-10 for issue #67. Equal-weight RRF is optional; **dense remains
unchanged as the default**. This small experiment finds no quality reason to adopt
hybrid automatically.

## Fixed method

Use #64's frozen source-hash/evidence-span dataset: four sources, nine queries,
three supported development queries plus one unsupported, four supported held-out
queries plus one unsupported. Process/chunk identically at 128 input tokens and
16 overlap with all-MiniLM-L6-v2. The same 33 committed chunk points contain named
dense and native BM25 representations, written once by SourceIngestionCoordinator.
English word/Snowball BM25 configuration and identities are recorded in JSON.

Preselected budgets: dense 20, lexical 20; hybrid combines both with smoothing60.
Evaluate returned evidence at final K=1,5,10 for every strategy. Save all returned
candidates (up to20 for standalone, up to40 for hybrid) to separate union candidate
coverage from final ranking. Hybrid costs two searches and one query embedding;
standalone costs one search, and lexical requires no query embedding. Configuration
was fixed before reading held-out results; no held-out tuning occurred.

Coverage uses cumulative union of extracted-text source spans, including multi-page
PDF facts. Unsupported queries have null recall/all-required/first-support values
and still return candidates; this is not an abstention policy or answer correctness
measurement. Token volume counts each selected chunk's content with the embedding
tokenizer and special tokens, before tool clipping and without model prompt overhead.

## Results

| Supported split | Strategy | Mean evidence recall@1 | Recall@5/@10 | All required@1 |
| --- | --- | --- | --- | --- |
| Development (3) | Dense | 0.667 | 1.000 | 0.667 |
| Development (3) | Lexical | 0.667 | 1.000 | 0.667 |
| Development (3) | Hybrid | 0.667 | 1.000 | 0.667 |
| Held-out (4) | Dense | 0.500 | 1.000 | 0.250 |
| Held-out (4) | Lexical | 0.625 | 1.000 | 0.500 |
| Held-out (4) | Hybrid | 0.500 | 1.000 | 0.250 |

All supported queries have complete required evidence in the full candidate union.
Hybrid unions contain24–30 distinct chunks, compared with20 each from standalone.
Overlap creates no extra evidence credit. No evidence is recovered beyond the union;
all strategies already achieve complete final evidence coverage at K5.

Representative regression: the held-out compound question has two required facts;
lexical's first chunk covers both, while hybrid promotes the dense-favored first
chunk covering one. Equal rank weighting loses that lexical advantage. The separated
PDF safety evidence first becomes complete at rank3 for all three strategies.
The development transition evidence reaches support at rank2 for all. No win in
final evidence quality was observed. Saved per-query spans/ranks allow these cases
to be inspected without relying on generated answers.

| Strategy | Median end-to-end query ms (9 queries) | Mean returned token volume@10 |
| --- | --- | --- |
| Dense | 30.7 | 1016.4 |
| Lexical | 12.7 | 1018.4 |
| Hybrid | 57.2 | 1052.2 |

Hybrid includes sequential branches and extra before/between/after lifecycle scans;
branch/fusion timings are recorded separately in result diagnostics. No operation
failed in this run. The JSON explicitly records an empty failure list. A failed
runner operation exits nonzero instead of reporting a successful partial comparison.

## Environment and limits

Local AMD Ryzen7 5700U CPU, cached all-MiniLM-L6-v2 revision
1110a243fdf4706b3f48f1d95db1a4f5529b4d41, Python3.14.8, torch2.14.1cpu,
SentenceTransformers6.1.0, Transformers5.19.0, local Qdrant1.16.3.
The benchmark used qdrant-client1.19.1 and emitted its compatibility warning;
independent native lifecycle checks used the verified client1.16.2 with server1.16.3.
This single warm CPU pass overlaps other local verification work, so timing is
illustrative, not a statistical performance claim. Nine hand-written queries do
not establish general superiority. No RSS estimate or separate BM25 ingestion
encoding timing is claimed; combined ingestion duration and model/index identities
are recorded. Backend boundary ties may choose different equal-score candidates.

## Reproduce and inspect

```bash
PYTHONPATH=src:. HF_HUB_OFFLINE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  TOKENIZERS_PARALLELISM=false python benchmarks/benchmark_hybrid_retrieval.py \
  --model-reference /path/to/cached/all-MiniLM-L6-v2 \
  --qdrant-url http://localhost:6336 \
  --output benchmarks/results/m5-hybrid-128-16.json
```

The runner creates an isolated collection and deletes it after measurement. Raw
results: [m5-hybrid-128-16.json](../../benchmarks/results/m5-hybrid-128-16.json).
A deterministic replay test reconstructs canonical saved chunks and recomputes the
frozen evidence metrics. Native tests verify replacement/deletion and detect a
completed source update between dense and lexical searches. ADR-013 describes the
observed consistency guarantee and remaining post-observation staleness limit.
