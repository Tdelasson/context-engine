# M5 local cross-encoder reranking — 2026-10-10

Optional reranking works locally and preserves source evidence. This small controlled
comparison does **not** justify enabling it by default: all supported queries already
have full Recall@5 with dense retrieval. A development query improves at rank one,
but held-out Recall@1 and Recall@5 do not improve. Issue #68 remains open for #67's
integrated hybrid candidates; these results cover dense candidate replay only.

## Method

Use #64's frozen four-source, nine-query evidence-span corpus with canonical source
revision/offset labels, including PDF evidence and two no-support queries. Dataset SHA-256:
`aee2874a927a676d9709438a1de57225e760546747f2d326894c8c37d75c6f14`.
Four queries are development (three supported), five held-out (four supported).

Processing and lifecycle ingestion use 128-token chunks/16 overlap, exact loaded embedding
token accounting, normalized `sentence-transformers/all-MiniLM-L6-v2` embeddings and
in-memory cosine retrieval. Save each query's top 20 candidate identities, scores and full
evidence records once. For each budget, both before/after use the same saved candidate
list; no query embedding or upstream search occurs during measured reranking. Evaluate
native upstream order and reranked order at K=1,3,5; candidate-set coverage is measured
separately at the candidate budget. The JSON includes deduplicated original documents,
all per-query metrics, rankings, scores, token volumes, failures and configuration identities.

Initial model: Apache-2.0 English MS-MARCO
`cross-encoder/ms-marco-MiniLM-L6-v2`, prepared revision
`233902d25c440f23af6f7d6e94d2946bac0bee0a`. Embedding snapshot revision:
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Reranker tokenizer/config/weights digest:
`6e30ec504be07702451383ab48c76fb485e38e0647ba5d38e3d289cc51e4e51e`.
Inference returns raw single-output logits with no activation. Higher is better; scores
are not probabilities. Pair text is the unchanged query and original passage, with empty
prefixes and no added headings. Strict cap: 512 combined tokens including special tokens.

CPU: AMD Ryzen 7 5700U, 16 logical CPUs available, two OMP/MKL threads, no GPU.
Linux, Python 3.14.8, Sentence Transformers 6.1.0, Transformers 5.19.0,
PyTorch 2.14.1+cpu. Tokenizer parallelism disabled. Each batch configuration loads once,
warms once on an unmeasured development query, then records one warm pass per query.
These single-pass timings are illustrative, with concurrent local work and no confidence
intervals. They include pair validation, scoring and wrapper ordering, exclude model
construction and upstream search. The same initialization measurement is reused for its
two candidate budgets; do not add it twice.

## Recorded results

| Candidates | Batch | Dev added seconds/query | Held-out added seconds/query | Dev pairs/second | Held-out pairs/second |
| --- | --- | --- | --- | --- | --- |
| 10 | 4 | 0.292 | 0.319 | 34.22 | 31.37 |
| 20 | 4 | 0.590 | 0.601 | 33.91 | 33.26 |
| 10 | 8 | 0.296 | 0.304 | 33.77 | 32.91 |
| 20 | 8 | 0.652 | 0.697 | 30.66 | 28.71 |

All four configurations yield supported Recall@5=1.0 before and after, with complete
candidate-set evidence coverage. No corpus query fails or exceeds the pair limit. Every
no-support query still returns ranked candidates; the reranker offers no abstention claim.
No-support queries remain in latency and token means but are excluded from evidence
recall by the #64 evaluator's explicit unsupported semantics.

Development Recall@1 improves from 0.667 to 1.0 in all configurations:
`dev-transition` first support moves from rank 2 to rank 1. Held-out Recall@1 remains
0.5. At candidate budget 20, `test-safety` first support moves from rank 3 to rank 2;
at budget 10 it remains rank 3. Supported Recall@3 remains 1.0 throughout. There are no
coverage regressions at K=1,3,5, but unchanged aggregate recall does not mean identical
rankings. Full original/reranked ID lists are retained for inspecting ordering differences.

For budget 10, mean top-five passage token volume increases from 467.5 to 493.0 on dev
and 481.6 to 535.6 held-out. For budget 20 it changes to 463.5 and 501.2 respectively.
These use the embedding tokenizer with special tokens on each passage; they are a
consistent passage-volume metric, not a generator context or cross-encoder pair count.
Candidate budgets double scoring volume and roughly double measured latency.

Initialization, including runtime identity hashing, is 0.165 seconds for batch 4 and
0.168 seconds for batch 8 with warm Python imports. First process import time is excluded.
Weights occupy 90,854,404 parameter bytes (86.65 MiB); process peak RSS, GPU memory,
activation peaks and total application memory were not reliably measured. Parameter bytes
alone are not a deployment memory budget.

Two explicit incompatibility probes (one per batch configuration) supply a 604-token pair
and both raise `RerankerInputCompatibilityError` before inference. They are recorded
separately rather than silently excluded from success latency averages. The default unit
suite also verifies exact boundaries, prefixes, Unicode, missing/duplicate/unknown/nonfinite
outputs and that a later incompatible candidate prevents scoring earlier candidates.
The opt-in real local test confirms a relevant passage outranks an irrelevant one and
that oversize text fails explicitly; it is not a retrieval-quality measurement.

## Decision and limits

Development results would select 10 candidates/batch 4 for this corpus: the same observed
development quality at lower cost. Evaluating that configuration on held-out queries
shows no Recall@1/5 gain and about 0.319 seconds of extra latency. This is insufficient
for default adoption. All four predeclared configurations are reported, including held-out
results; settings were not chosen to maximize held-out performance. Operational workbench
bounds remain 20 candidates/batch 8 until a broader evaluated application decision.

The initial small English model is a workable optional CPU adapter, but English MS-MARCO
fit cannot establish quality for multilingual sources or the application's full domain.
This corpus is small and partially synthetic. No broader model comparison, Qdrant-backed
reranking benchmark, hybrid candidate integration, answer generation, factual verification,
window scoring or context selection is claimed. #67 remains required for the issue's
hybrid acceptance criterion. The draft PR must not close #68 prematurely.

## Reproduce

Prepare both snapshots explicitly, then run from the activated project environment:

```bash
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false \
python benchmarks/benchmark_reranking.py \
  --embedding-reference /absolute/path/to/embedding/snapshot \
  --reranking-reference /absolute/path/to/reranker/snapshot \
  --output benchmarks/results/m5-reranking-local.json
```

Recorded artifact: [machine-readable comparison](../../benchmarks/results/m5-reranking-local.json).
See [ADR-012](../architecture/decisions/ADR-012-local-cross-encoder-reranking.md),
[model card](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2),
[score semantics](https://sbert.net/docs/cross_encoder/usage/usage.html) and
[tokenizer truncation controls](https://huggingface.co/docs/transformers/main/pad_truncation).
