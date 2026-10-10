# M5 chunked dense evidence benchmark

Recorded 2026-10-10 for issue #64. This experiment measures retrieved evidence,
not generated answers. M4 whole-document corpus/results are unchanged.

## Corpus and methodology

`benchmarks/data/retrieval/m5/dataset.json` pins four controlled longer sources:
UTF-8 Markdown/text with routine distractors, and a locally generated two-page
text PDF. Four development queries include an exact identifier, paraphrased
approval, cross-block transition steps, and one unsupported question. Five held-out
queries include sensor failure, recovery phases, multi-page safety, a compound
Markdown/PDF question, and one unsupported question. There are three supported
development queries and four supported held-out queries. Source files remain
available to every ranking; query labels are never indexed.

The dataset pins source-byte SHA-256, processing limits/version, and SHA-256 of
actual extracted Unicode text. The loader validates exact revisions and half-open
character offsets before inference. Changing extraction requires a reviewed dataset
revision, not silently moving labels. Stable evidence IDs are independent of chunk
IDs/settings. The PDF safety item's spans are separated by hundreds of tokens,
requiring several chunks; the compound question needs different sources.

For each evidence item, union labeled characters form its denominator. Retrieved
contributing block/page spans from matching source/revision cover those characters
cumulatively at K=1,5,10. Overlapping chunks and labels are counted once. Complete
support requires 100% coverage; fractional coverage is reported but does not count
as recalled evidence. The first support rank is the first result prefix completing
any item, including joint completion across chunks. It is null when none completes.

Each supported query contributes equally to macro evidence recall. Macro character
coverage first averages items within each query. All-required rate counts supported
queries whose every item completes. Unsupported questions have no recall, support
rank or all-required denominator; their returned results are retained for analysis.
Top-K retrieval alone cannot establish abstention. MRR/NDCG are deliberately not
reported because these labels do not define binary relevance for individual chunks.

The bounded chunk grid was fixed before recorded comparisons: 96/0, 160/0 and
160/24 (maximum embedding input tokens / overlap), heading context enabled.
MiniLM-L6 is held fixed for this grid. L6 and L12 are compared at compatible 96/0.
The 160/24 Qdrant verification setting is a controlled integration configuration,
not a default selected from held-out outcomes. No runtime default is changed.

## Recorded results

| Model/backend | Tokens/overlap | Chunks | Dev recall@5 | Held-out recall@5 | Held-out all-required@5 | Held-out recall@10 | Ingestion s | Mean query embedding ms | Mean search ms | Mean retrieved tokens@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MiniLM-L6 / in-memory cosine | 96/0 | 35 | 1.000 | 1.000 | 1.000 | 1.000 | 0.821 | 17.54 | 1.68 | 822.0 |
| MiniLM-L6 / in-memory cosine | 160/0 | 24 | 1.000 | 0.625 | 0.500 | 0.875 | 0.901 | 17.67 | 1.11 | 1268.8 |
| MiniLM-L6 / in-memory cosine | 160/24 | 27 | 1.000 | 1.000 | 1.000 | 1.000 | 3.256 | 16.93 | 1.28 | 1261.2 |
| MiniLM-L12 / in-memory cosine | 96/0 | 35 | 1.000 | 1.000 | 1.000 | 1.000 | 1.413 | 27.65 | 1.66 | 781.9 |
| MiniLM-L6 / Qdrant server | 160/24 | 27 | 1.000 | 1.000 | 1.000 | 1.000 | 3.202 | 20.55 | 13.84 | 1261.2 |

Token volume is the sum of independently tokenized retrieved passage content,
including per-passage special tokens, with the identified embedding tokenizer.
It is not an estimate of a serialized prompt envelope. Mean timing/token values
include all nine queries; quality denominators exclude unsupported questions.
Ingestion includes processing, chunking, embedding, and source lifecycle writes.
Query embedding and vector search are measured separately through their interfaces.
The in-memory timing is not Qdrant latency. Qdrant search includes manifest checks.

The searchable float32 dense-vector estimates are 53,760 bytes for 35 chunks,
36,864 for 24, and 41,472 for 27 (384 dimensions). They exclude payloads,
source manifests, Python objects, and index overhead. Reliable persisted index bytes
were unavailable and are explicitly null. Model parameter footprints measured from
loaded tensors were 90,852,864 bytes for L6 and 133,440,000 for L12; these are not
peak process RAM or downloaded model sizes. Peak process RAM/VRAM were not measured.

Environment: Linux x86-64, Python 3.14.8, CPU inference with OMP/MKL threads capped
at two, sentence-transformers 6.1.0. Exact platform/dependency/tokenizer identities
and configuration hashes are in each JSON artifact. Snapshots were loaded offline:
L6 `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, L12
`a50ef00143b4d5391434df20ae11632588ac25be`. The isolated local Qdrant server was
1.16.3 on port 6336; qdrant-client 1.19.1 warned about version compatibility.
The verification passed without suppressing that warning, but future runs should
align supported versions. Single runs occurred during parallel development; the
latencies have no confidence intervals or throughput/capacity interpretation.

## Failures, trade-offs and limits

L12's saved runtime limit is **128 tokens**, while L6's is 256. The attempted
160/24 L12 comparison failed explicitly with `ChunkingError` before ingestion;
its failure artifact is retained. The compatible model comparison uses **96/0
for both models**, with no silent truncation or runtime-limit override. Exact
counting may warn while inspecting oversized provisional candidates; final chunks
are budget-checked before inference. Larger M4 candidates were not attempted in
this bounded two-model CPU experiment; no hardware impossibility claim is made.

For the 160/0 L6 setting, the safety evidence completes only at rank 10 and the
compound question misses its limiter item even at K=10. Larger passages contain
more routine distractor text. At 160/24, overlap recovers these facts but raises
chunking/ingestion cost and token volume. At 96/0, complete safety support arrives
at rank 3 even though the first result covers only 45.3% of the item. Treating any
intersection as relevant would incorrectly count that first result as full support.
The compound question cannot complete at K=1 because its facts reside in different
sources. Unsupported questions still receive results; no rejection threshold is
configured or evaluated.

On development quality, all three chunk settings tie. The held-out differences are
reported for diagnosis and **do not select defaults**. The smaller 96/0 setting has
more chunks but lower returned token volume and lower ingestion duration in this
run; it is a useful controlled comparison for later lexical/reranking work. L12
provides no quality gain on this tiny corpus while using more parameter memory and
query time. This does not establish universal model or chunking superiority.

Repeated distractors, a synthetic text PDF, four supported held-out queries, and
ceiling scores at K=5 limit external validity. Real PDFs with OCR, complex layouts,
large corpora, multilingual retrieval and answer correctness remain untested.
Broader development data and repeated measurement are needed before changing
workbench defaults. ADR-010 documents the evaluation contract.

## Reproduction and artifacts

Install existing optional `benchmark`, `pdf`, `qdrant`, and `dev` dependencies.
Run from the configured project environment with offline pinned local snapshots
when available:

```bash
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false \
python -m benchmarks.benchmark_chunked_retrieval \
  --model-reference /path/to/pinned/all-MiniLM-L6-v2 \
  --chunk-settings 96:0,160:0,160:24 \
  --output benchmarks/results/m5-minilm-l6-chunk-comparison.json

python -m benchmarks.benchmark_chunked_retrieval \
  --model-id all-minilm-l12-v2 \
  --model-reference /path/to/pinned/all-MiniLM-L12-v2 \
  --chunk-settings 96:0 \
  --output benchmarks/results/m5-minilm-l12-compatible-comparison.json

python -m benchmarks.benchmark_chunked_retrieval \
  --model-reference /path/to/pinned/all-MiniLM-L6-v2 \
  --chunk-settings 160:24 --backend qdrant-server \
  --qdrant-url http://localhost:6336 \
  --output benchmarks/results/m5-qdrant-dense-verification.json
```

Each run creates an isolated collection. Sources are deleted after measurement;
Qdrant collections and active tombstones remain and should be removed using
Qdrant's collection-management API when finished. Failed cleanup is reported rather
than masking a primary pipeline failure. Normal unit tests need no model download
or service. Opt-in tests in `test_m5_evidence_benchmark_integration.py` require
`CONTEXT_ENGINE_RUN_LOCAL_EMBEDDING_INTEGRATION=1`, and additionally
`CONTEXT_ENGINE_RUN_QDRANT_INTEGRATION=1` for the deployed backend. Set
`CONTEXT_ENGINE_EMBEDDING_MODEL_REFERENCE` and `CONTEXT_ENGINE_QDRANT_URL` to local
resources. Both real integration cases passed on the recorded environment.

Machine artifacts under `benchmarks/results/`:

- `m5-minilm-l6-chunk-comparison.json`: fixed-model chunk grid.
- `m5-minilm-l12-compatible-comparison.json`: compatible fixed-chunk model comparison.
- `m5-minilm-l12-model-comparison.json`: explicit incompatible 160/24 candidate failure.
- `m5-qdrant-dense-verification.json`: actual server lifecycle/retrieval path.
