# M5 deterministic evidence selection benchmark

Recorded 2026-10-10 for #69. This evaluates evidence packaging, not generated-answer accuracy.
Raw artifacts: [dense](../../benchmarks/results/m5-evidence-selection-dense.json) and
[hybrid/reranked](../../benchmarks/results/m5-evidence-selection-hybrid-reranked.json).

## Method and accounting

Use #64's pinned four-source/nine-query evidence-span corpus, unchanged: three supported
and one unsupported development queries, four supported and one unsupported held-out queries.
Real local MiniLM-L6 embeddings, 128/16 chunks, 33 committed chunks. Dense uses the in-memory
cosine backend. The separate native Qdrant path uses BM25/dense equal-weight RRF (20 per
branch, smoothing 60, 20 outputs) and local MS MARCO MiniLM-L6 cross-encoder reranking
(20 candidates/outputs, batch 8). Freeze 20 ranked candidates once per query and replay the
identical lists through each selection configuration. Save content, provenance, scores and
upstream diagnostics for independent inspection. No evidence label enters runtime selection.

Predeclared grid: evidence JSON budgets 2,048 / 4,096 / 8,192; overlap suppression disabled
(the rank-order budget-fitting baseline), or thresholds 0.5 / 0.8 / 1.0. At most five whole
passages, each at most 2,000 characters; exceeding these resource limits excludes rather
than clips. Recount the entire model-visible JSON, including query, citation/source metadata,
escaping, separators and original ranking diagnostics, with the official answering tokenizer
Qwen/Qwen2.5-0.5B-Instruct revision 7ae557604adf67be50417f59c2c2f167def9a775. No answering
weights or answering inference are used. Counter identity is persisted in the artifacts.

Token counts are exact for this pinned raw tokenizer encoding (no added special tokens).
Ollama/GGUF parity is unverified; these are not verified full answering-request context
limits. Provider tool envelope, chat template, history, instructions, definitions, other
calls and answer reserve remain the request owner's responsibility. Runtime-only selection
reports stay in traces/UI and are excluded from model history. Original upstream ranking
diagnostics are model-visible and counted. See ADR-014 for the complete boundary.

Metrics use #64's complete union evidence coverage. A selected prefix completes an item
only when all its labeled characters are covered. Recall is macro-averaged over supported
queries; all-required rate requires every item. Token/cost means include unsupported queries,
whose recall/all-required/rank remain null. No retrieval/selection abstention claim is made.
Repeated source characters are summed comparable candidate unions minus the same-source/revision
union of all selected locations; missing provenance is counted separately, never fabricated.

## Results

The following uses overlap threshold 0.8. At these settings the equal-budget baseline has
identical selected IDs, evidence coverage, token usage and repeated-source coverage.

| Candidate path | JSON budget | Dev evidence recall | Held-out evidence recall | Held-out all-required | Mean dev/held-out tokens | Mean dev/held-out selection ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Dense / in-memory | 2,048 | 0.667 | 1.000 | 1.000 | 1,661 / 1,727 | 87.7 / 92.4 |
| Dense / in-memory | 4,096 | 1.000 | 1.000 | 1.000 | 3,782 / 3,840 | 129.0 / 120.2 |
| Dense / in-memory | 8,192 | 1.000 | 1.000 | 1.000 | 5,128 / 4,663 | 21.9 / 19.1 |
| Native hybrid + reranking | 2,048 | 0.333 | 0.250 | 0.000 | 1,936 / 1,844 | 150.3 / 144.6 |
| Native hybrid + reranking | 4,096 | 1.000 | 0.875 | 0.750 | 3,158 / 3,757 | 174.3 / 180.7 |
| Native hybrid + reranking | 8,192 | 1.000 | 1.000 | 1.000 | 7,459 / 7,730 | 255.7 / 259.4 |

Every row's actual serialized count is within its stated budget. Both raw failure lists
are empty. At 4,096 tokens/0.8, mean repeated source characters are 64.5/51.6 (dense
development/held-out) and 0/33.2 (hybrid/reranked). Thresholds 0.5 and 1.0 likewise do not
improve quality/token totals on this corpus: some exclusions occur only after candidates
that would not have fitted anyway. Controlled unit tests establish suppression behavior;
these real experiments do not establish its practical benefit.

Select settings using development only: maximize evidence recall/all-required rate, then
minimize returned tokens and budget; remaining threshold ties choose the smaller threshold.
Both paths select 4,096/0.5, tied in outcomes with 0.8 and 1.0. Held-out outcomes are reported
once for diagnosis, not used to increase the chosen budget. The hybrid held-out regression
is retained rather than retrospectively choosing 8,192. This tiny grid does not justify
turning selection on by default or claiming a generally optimal overlap threshold.

## Failure analysis and limits

Dense `dev-transition` loses the required passage at 2,048, while a later fitting passage
still survives. Dense `test-offline` can include original rank 14 after oversized earlier
candidates are skipped. Hybrid `test-compound` at 4,096 selects original ranks 1 and 3;
its other required fact is excluded by remaining budget. Full evidence recall falls to 0.5
for that query, giving 0.875 macro held-out recall and 0.750 all-required rate. Source metadata
and hybrid/upstream/reranking diagnostics increase the full serialization cost; passage-only
counts would hide this regression. More than one location may contribute to one evidence item.

The larger dense budget can be faster: it reaches the five-result resource ceiling earlier,
while tight budgets repeatedly render and count later fitting possibilities. Hybrid diagnostics
are much larger, increasing recounting cost. Times measure selection alone, not query inference,
retrieval, reranking or answer generation. Results are single warm CPU passes without confidence
intervals, on four small controlled sources. No peak memory/production scaling claim is made.
Selection cannot establish factual correctness, answerability or total-request fit.

Linux x86-64 / Python 3.14.8, OMP/MKL threads 2; dependency versions and effective model/tokenizer
identities are in each artifact. MiniLM embedding snapshot 1110a243fdf4706b3f48f1d95db1a4f5529b4d41;
cross-encoder snapshot 233902d25c440f23af6f7d6e94d2946bac0bee0a. Qdrant server 1.16.3/client
1.19.1 emitted a compatibility warning which was not suppressed. Use matching supported
versions for deployment. The benchmark removes its isolated Qdrant collection after each run.

## Reproduce

Install the existing benchmark/workbench optional dependencies. Prepare the two official
Qwen tokenizer files at the pinned revision, and cached embedding/cross-encoder snapshots.
The runtime never automatically downloads tokenizer files or answering weights.

```bash
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 \
python -m benchmarks.benchmark_evidence_selection \
  --embedding-reference /local/all-MiniLM-L6-v2 \
  --tokenizer-directory /local/pinned-qwen-tokenizer \
  --output benchmarks/results/m5-evidence-selection-dense.json

# Same setup, with local Qdrant and the existing local cross-encoder:
python -m benchmarks.benchmark_evidence_selection \
  --embedding-reference /local/all-MiniLM-L6-v2 \
  --tokenizer-directory /local/pinned-qwen-tokenizer \
  --strategy hybrid-reranked-qdrant --qdrant-url http://localhost:6333 \
  --reranking-reference /local/ms-marco-MiniLM-L6-v2 \
  --output benchmarks/results/m5-evidence-selection-hybrid-reranked.json
```

Unit tests require no inference, downloads or services. Opt-in tests require
CONTEXT_ENGINE_RUN_EVIDENCE_SELECTION_INTEGRATION=1 plus local tokenizer/embedding references;
native hybrid/reranked additionally requires CONTEXT_ENGINE_RUN_QDRANT_LEXICAL_INTEGRATION=1,
CONTEXT_ENGINE_QDRANT_URL and CONTEXT_ENGINE_RERANKING_INTEGRATION_MODEL.
