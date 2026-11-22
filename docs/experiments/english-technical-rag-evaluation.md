# Staged English technical-workbench RAG evaluation

**Historical v1 report.** The 2026-10-12 evidence review corrected these draft
labels. Consult the [review findings and v2 rescored results](technical-evidence-review.md)
for current measurements; the original labels/artifacts below remain preserved.
No retrieval settings were retuned. The runner now defaults to v2, so reproducing
this report requires explicitly selecting the original v1 manifest.

Recorded for #77–#79 on 2026-10-10. This extends quality evaluation; #80's runtime
latency, memory, capacity and load measurements remain deferred.

## Dataset and interpretation boundary

The pinned technical-v1 manifest contains 29 sources and 124 questions: 24 original
CPython 3.14.0 documentation snapshots, four fictional Markdown stress documents,
and one simple two-page PDF derivative. There are 57 supported/6 unsupported
development questions and 55 supported/6 unsupported held-out questions. Connected
source/topic groups keep compound/alternative evidence in one split. Only seven
development and six held-out groups remain: intervals are explicitly exploratory.
See the [dataset guide](../../benchmarks/data/retrieval/technical-v1/README.md) and
[concrete annotation review packet](technical-v1-annotation-review.md).

All 124 annotations are authored drafts awaiting independent review. Hashes,
coordinates and fixtures pass integrity checks; that does not establish semantic
label correctness. Results below are provisional observations on this defined
public-document workload. Residual generic API similarity, pretraining overlap,
fictional unsupported questions, raw reStructuredText markup, no OCR/complex
layouts and missing private-document/task coverage limit transfer to production.

## Controlled plan

MiniLM-L6: 96/0 versus 128/16 chunks, with fixed embeddings. MiniLM-L6 versus L12:
compatible fixed 96/0 chunks. At 128/16 use dense, lexical, hybrid RRF and reranked
hybrid on the same isolated Qdrant store, 20 bounded candidates, equal branch RRF
weights and smoothing 60. Existing local MS MARCO MiniLM-L6 reranks 20 candidates.
Memory dense is separately identified and serves as a backend check, not a lexical
or capacity comparison. Each path freezes its own candidates once per query.

For selection, predeclared raw Qwen JSON budgets are 2048/4096, thresholds disabled
or 0.8, five whole results, 2000 characters per result, and ranking diagnostics
included or omitted. Omission keeps all source/citation metadata, content and native
scores; runtime selected-stage diagnostics remain in UI/traces. It is not a claim
that remaining provenance is a minimal possible envelope. Choose on development by
recall, all-required rate, mean tokens, then smaller budget/disabled-overlap/omitted
ranking diagnostics to break ties. Held-out evaluates the frozen choice and paired
baseline variants at that same budget. No held-out tuning or default change occurs.

Coverage is measured at candidates@20, ranked@5 and final selected evidence. A fact
completes when one complete support alternative is covered; missing candidates and
selection exclusions are separated. Repeated source characters and per-candidate
exclusions remain in raw artifacts. Sequential marginal accounting recounts entire
nested envelopes for envelope, passage content, citations/metadata and diagnostics;
those marginals sum to the complete rendered count, without assuming independent
fragment token additivity. Raw-tokenizer evidence budgeting remains distinct from
complete provider-context fit.

Cluster percentile-bootstrap intervals and paired differences use fixed seed 77,
1000 replicates and source/topic groups. Six held-out groups are too few to support
precise population conclusions. Repeated inference on the same questions does not
increase quality sample size. The original #64 dataset and its historical artifacts
remain unchanged and have a separate real four-path regression artifact.

Raw candidates/results use deterministic gzip JSON to avoid repeated text bloating
Git. Read with benchmarks.evaluation_artifacts.read_artifact or gzip. Replay verifies
selected IDs and exact full-output counts; the initial dense-128 artifact is replayed
with connected grouping corrected, without changing its development choice. A runner
fix ensures the predeclared 0.8 held-out baseline is actually tested even when disabled
overlap wins development. No new threshold or tuning criterion was introduced.

## Recorded retrieval findings

The main held-out denominator is 55 supported questions over six connected topics;
its six unsupported questions have no fabricated recall score. Development categories
are 24 exact-API, 24 paraphrase, six multi-source, two revision, one hard distractor
and six unsupported questions. Held-out categories are 24 exact-API, 24 paraphrase,
six multi-source, one two-page PDF and six unsupported questions. Category labels
are drafts; a question count does not compensate for narrow topic diversity.

All four Qdrant paths selected the development policy of 4096 raw evidence tokens,
overlap disabled and upstream ranking diagnostics omitted. The five-result and
2000-character limits stay fixed. All recorded ingestion/retrieval runs completed
without query failures. Percentages below are mean complete-fact recall, not answer
accuracy or proportional character coverage.

| Qdrant path, 128/16 L6 | Candidates@20 | Ranked@5 / selected | Selected all-required | Exploratory selected-recall 95% interval | Mean selected tokens, all 61 queries |
| --- | ---: | ---: | ---: | --- | ---: |
| Dense | 71.8% | 39.1% | 38.2% | 31.5–45.6% | 3751 |
| Lexical | 73.6% | 53.6% | 49.1% | 42.6–64.3% | 3797 |
| Hybrid RRF | 75.5% | 57.3% | 54.5% | 42.0–73.1% | 3830 |
| Reranked hybrid | 75.5% | 64.5% | 61.8% | 47.3–80.9% | 3830 |

At the selected policy, five results fit every query. Remaining complete-fact losses
split into candidate absence and exclusions after candidate retrieval: dense 19/20,
lexical 17/12, hybrid 16/11 and reranked 16/6. These are fact counts, not question
counts. Ranked@5 exposes the ranking/result-limit loss; the selector actually sees
all 20 ranked candidates and can skip oversized/overlapping results. The raw
per-candidate reasons distinguish result, character, budget and overlap limits.
Do not interpret ranked@5 as an additional hard prune before selection.

On identical frozen candidates at equal 4096-token budgets, omitting diagnostics
improved selected recall by 0.0 percentage points for dense, 3.6 for lexical,
19.1 for hybrid (paired exploratory interval 7.4–32.7) and 13.6 for reranked
(7.3–20.9). This isolates serialization overhead from ranking. The envelope still
retains substantial metadata: reranked averages about 27 envelope tokens, 534 content
and 3268 citation/metadata tokens under sequential marginal attribution. This is
not a minimal provenance schema or proof that every metadata field is necessary.

Overlap threshold 0.8 changed no main held-out recall. That negative result does
not establish universal safety. The separate fixed-ranking, authored
`selection-overlap-stress.json` diagnostic shows an exact duplicate can be removed
without coverage loss (425 to 230 tokens), while a 90% overlapping passage with a
new required fact loses complete-fact recall from 1.0 to 0.5 (428 to 230 tokens).
Complementary spans remain unchanged (390 tokens). These three correlated cases
are mechanism tests, not estimated production frequencies; their candidate spans
are deliberately constructed, rather than embedding-generated chunks.

At fixed L6, 128/16 improves selected held-out recall over 96/0 from 23.6% to 39.1%
(+15.5 points, paired exploratory interval 3.7–26.8). This changes both size and
overlap, so it does not identify which caused the gain. At fixed 96/0, L12 reaches
20.0% versus L6's 23.6%; there is insufficient evidence to prefer the larger model.
Reranking improves hybrid by 7.3 points (0.9–14.8) on this corpus, with a recorded
regression on `fractions-as_integer_ratio`. See the chunk/model/path comparison
artifacts for identities and every paired regression. Memory dense matches Qdrant's
39.1% selected recall; this is a quality check, not a capacity comparison.

The original nine-question diagnostic suite remains separately reproducible. Its
four supported held-out questions reach complete coverage on all four paths with
the development-selected envelope. Equal-budget omission gains 25 points for hybrid
and 75 for reranked; these are tiny, correlated diagnostics, not four independent
topic samples. The replay explicitly groups this suite together.

## Published PDF diagnostic

A separate `technical-pdf-v1` suite adds 12 draft questions and two published Python
3.11.0 PDF fixtures, preserving original pages, fonts and code-box layouts. The
[guide](../../benchmarks/data/retrieval/technical-pdf-v1/README.md) pins the official
archive, member hashes and original page indices; the
[review packet](technical-pdf-v1-annotation-review.md) lists every fact/span.
Development has six virtual-environment questions; held-out has six argparse
questions, including multi-span facts. This suite is not pooled with technical-v1.

Selected held-out recall is 22.2% dense, 0.0% lexical, 16.7% hybrid and 33.3%
reranked. Extraction joins some words and separates code tokens differently from
visible pages. These results expose a realistic parser/retrieval gap without adding
a parser or asserting that PDF layout is understood. Each split has only one topic:
bootstrap intervals cannot establish population uncertainty. Scans/OCR, complex
tables and multi-column layouts remain outside this workload.

## Actual-runtime answer pilot and context boundary

The opt-in answer runner exercises AgentRuntime, native Ollama ModelGateway and the
ordinary allowlisted search_documents ToolRuntime, including argument validation,
policy, actual retrieval/selection, model-visible output and execution traces.
Reference facts stay exclusively in evaluation artifacts. The
[human rubric](rag-answer-review-rubric.md) requires separate fact, correctness,
claim/citation support and abstention decisions from an identified reviewer.

The exploratory model is Qwen2.5 0.5B Instruct, GGUF Q4_K_M, Ollama 0.12.5, digest
`a8b0c51577010a279d933d14c2a8ab4b268079d44c5c8830c0a93900f1827c67`.
Generation uses temperature 0, seed 79, two CPU threads, configured context 16384,
answer reserve 256, at most four iterations, dense 128/16 and the frozen 4096-token,
no-overlap/no-ranking-diagnostics policy. This is an explicit small-model probe;
the workbench deployment default remains Llama3.2:1b and was not validated here.
The supplied native counter is pinned Qwen. Another Ollama answering model can be
explicitly evaluated with `--allow-tokenizer-proxy`: the wrapper records a distinct
identity and cross-model-proxy method, without claiming target-tokenizer compatibility.
Without that declaration, mismatched models are rejected. A verified deployment
context guarantee still needs its own compatible counter and provider verification.

The planned 124-primary-question run was interrupted after 21 primary observations
(13 development, eight held-out) plus one repeat. It is an incomplete exploratory
pilot, not a completed fresh held-out answer-quality evaluation. All 103 unrun IDs
remain explicit and full-plan scoring rejects the incomplete artifact. No answer
accuracy, correctness, abstention, citation-support or task-success percentage is
published. Every human answer review remains pending.

| Observed primary subset | Responded | Runtime failed | Iteration limit | Total |
| --- | ---: | ---: | ---: | ---: |
| Development, exact API/paraphrase only | 6 | 4 | 3 | 13 |
| Held-out, exact API/paraphrase only | 2 | 5 | 1 | 8 |

Eight returned answers made no native search call. Two other questions executed a
successful search, but both failed on the subsequent answering request with a
connection/timeout error. For `json-JSONDecoder` and `pickle-loads`, retrieved
candidates covered the fact but selected evidence did not; their final-answer
failure additionally prevents attributing an answer-quality failure to selection
alone. Four primary executions reached the iteration limit without a tool result.
Raw interaction errors distinguish invalid model/tool-call behavior from provider
errors; neither fluent text nor advertised tools capability proves tool use.
The `json-dumps` repeat was identical with no tool call. The planned fnmatch repeat
was not reached; one repeated observation does not establish deterministic generation.

Actual serialized provider requests, typed responses/errors and exposed provider
input/output counts are retained (36 requests across the 22 saved observations).
The first request reports 234 provider input tokens against 250 raw-payload proxy
tokens. This difference demonstrates that raw JSON tokenization is not chat-template
parity. Tool definitions, system/user history, results and reserve are included in
recorded native requests, but hidden template/truncation behavior remains unknown;
there is no verified complete-request fit guarantee. The first pilot predates raw
native response-body capture and run-status metadata; status/planned IDs were
backfilled after interruption, without changing answers or observed outcomes.

A separately recorded original-suite long-history boundary uses real user/assistant
history, context 1024 and reserve 128. Its raw request proxy is 3583 tokens and the
model request timed out; no provider input count was returned. That is an observed
connection/timeout failure, not proof of context overflow or truncation. Repeated
actual tool calls/history preservation are additionally covered by controlled
runtime tests. A completed live repeated-call boundary and deployment-model
held-out answer evaluation remain unverified.

## Recommendation and completion boundary

Retain current defaults. The provisional corpus supports further investigation of
128/16, lexical/hybrid retrieval, reranking and diagnostic-envelope omission. It
provides no general overlap-suppression benefit, larger-embedding preference or
production-readiness guarantee. Provider/tool-use failures and unreviewed labels
prevent an end-to-end quality recommendation. Broadening difficult unsupported
questions, parser-heavy documents and private deployment tasks remains necessary
before application-wide conclusions.

The tooling for #77–#79 is implemented. Their evaluation acceptance remains pending
where it explicitly requires independent annotation/rubric review, reviewed answer
scoring and completed intended-deployment held-out/boundary runs. Keep those issues
open; do not equate successful tests or this exploratory pilot with reviewed labels.
Runtime latency, memory, throughput and load measurements remain deferred to #80.

## Reproduction and artifacts

Use the configured development environment with project optional local retrieval
packages. Recorded environment: Python 3.14.8, sentence-transformers 6.1.0, pypdf
6.20.0, Qdrant client 1.19.1 and server 1.16.3. The client warns about this minor-version
mismatch; it was not suppressed. Runs succeeded, but this is not a compatibility
certification. Use an explicitly compatible pair for deployment validation.

Pinned snapshots: MiniLM-L6 `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, MiniLM-L12
`a50ef00143b4d5391434df20ae11632588ac25be`, MS MARCO cross-encoder L6
`233902d25c440f23af6f7d6e94d2946bac0bee0a`. Evidence counting uses the existing
verified local Qwen tokenizer fixture; counter/index identities are in every artifact.
Set local snapshot directories and isolated server URLs explicitly:

```bash
export PYTHONPATH=src OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false
python -m benchmarks.benchmark_rag_ablation \
  --dataset benchmarks/data/retrieval/technical-v1/dataset.json \
  --embedding-reference "$L6_SNAPSHOT" --tokenizer-directory "$QWEN_TOKENIZER" \
  --qdrant-url "$EVALUATION_QDRANT_URL" --reranking-reference "$RERANKER_SNAPSHOT" \
  --output /tmp/technical-v1-qdrant.json.gz
python -m benchmarks.benchmark_rag_ablation \
  --dataset benchmarks/data/retrieval/technical-pdf-v1/dataset.json \
  --embedding-reference "$L6_SNAPSHOT" --tokenizer-directory "$QWEN_TOKENIZER" \
  --qdrant-url "$EVALUATION_QDRANT_URL" --reranking-reference "$RERANKER_SNAPSHOT" \
  --output /tmp/technical-pdf-v1-qdrant.json.gz
python -m benchmarks.benchmark_rag_ablation \
  --dataset benchmarks/data/retrieval/m5/dataset.json \
  --embedding-reference "$L6_SNAPSHOT" --tokenizer-directory "$QWEN_TOKENIZER" \
  --qdrant-url "$EVALUATION_QDRANT_URL" --reranking-reference "$RERANKER_SNAPSHOT" \
  --output /tmp/m5-rag-ablation-regression.json.gz
python -m benchmarks.benchmark_selection_stress \
  --tokenizer-directory "$QWEN_TOKENIZER" --output /tmp/selection-stress.json
python -m benchmarks.benchmark_rag_answers \
  --dataset benchmarks/data/retrieval/technical-v1/dataset.json \
  --embedding-reference "$L6_SNAPSHOT" --tokenizer-directory "$QWEN_TOKENIZER" \
  --ollama-url "$EVALUATION_OLLAMA_URL" --split all --budget 4096 --threshold none \
  --omit-ranking-diagnostics --answer-tokens 256 --max-iterations 4 \
  --repeat-ids json-dumps fnmatch-fnmatchcase --output /tmp/answers.json.gz
```

For memory chunk/model controls omit Qdrant/reranker and use `--chunk-tokens 96
--overlap 0`; use `--model-id sentence-transformers/all-MiniLM-L12-v2` with its
compatible snapshot. Never score the incomplete saved pilot as a completed run.
For history boundaries, `--history-file` takes a JSON array of real user/assistant
messages; tool-history fabrication is rejected. Review a completed artifact using
`--review-artifact` after independently recording every primary review.
To run the workbench model, explicitly supply `--model-id llama3.2:1b` and
`--allow-tokenizer-proxy` until a matching counter is available. The resulting budget
is identified as an estimate in Qwen units, not exact Llama token usage; provider
usage is recorded separately. This proxy mode has controlled tests, not a recorded
live Llama evaluation in this report.

Results are under `benchmarks/results/technical-v1-*`,
`technical-pdf-v1-qdrant.json.gz`, `m5-rag-ablation-regression.json.gz`,
`m5-answer-history-boundary.json.gz` and `selection-overlap-stress.json`.
`python -m benchmarks.replay_rag_ablation --artifact PATH --dataset MANIFEST
--tokenizer-directory TOKENIZER --output PATH` recounts frozen candidates and verifies
selected identities/token counts. `benchmarks.compare_rag_ablation` pairs stages,
requires matching corpus/query identities and records regressions. The annotation
packet generator and dataset guides describe version changes/disagreement resolution.
