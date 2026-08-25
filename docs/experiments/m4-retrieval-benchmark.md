# M4 Retrieval Benchmark

## Purpose

This experiment compares the candidate local embedding models from ADR-005 using one fixed,
model-independent retrieval task. It evaluates retrieval rather than generated-answer quality.

## Fixed evaluation definition

- Dataset: `benchmarks/data/retrieval/m4-retrieval-dataset-v1.json`
- Relevance: binary, hand-curated judgments stored with the dataset
- Distance metric: cosine similarity
- K values: 1, 5, and 10
- Quality metrics: mean Recall@K, mean reciprocal rank, and mean NDCG@K
- Retrieval path: `EmbeddingProvider` → `Ingestor` → `VectorStore` → `Retriever`

Every model uses the same documents, query text, relevance judgments, in-memory cosine store, and
K values. Model-specific prefixes and trusted-code requirements are explicit configuration rather
than changes to the evaluation definition.

## Candidate configuration

| Model ID | Model reference | Query/document handling |
| --- | --- | --- |
| `bge-m3` | `BAAI/bge-m3` | No prefix |
| `qwen3-embedding-0.6b` | `Qwen/Qwen3-Embedding-0.6B` | Shared retrieval-task query instruction |
| `qwen3-embedding-8b` | `Qwen/Qwen3-Embedding-8B` | Shared retrieval-task query instruction |
| `nomic-embed-text` | `nomic-ai/nomic-embed-text-v1.5` | `search_query:` / `search_document:` prefixes; trusted model code enabled |
| `all-minilm-l6-v2` | `sentence-transformers/all-MiniLM-L6-v2` | No prefix |

All models use normalized embeddings and batched document inference. Qwen3-Embedding-8B uses a
smaller batch to reduce peak local memory demand. Enabling trusted model code for Nomic is an
explicit opt-in consequence of choosing that candidate model reference.

## Measurements

The benchmark records:

- Recall at each fixed K, MRR, and NDCG at each fixed K;
- model initialization time;
- document embedding time and throughput;
- per-query embedding latency;
- vector-search latency;
- vector dimensionality;
- measured in-memory parameter bytes when exposed by the backend;
- process resident memory before and after model load on supported platforms; and
- operating-system, Python, processor, and dataset identity information.

Process RSS is currently measured only on Linux through `/proc`. A missing value means the platform
did not expose a reliable measurement through the dependency-free benchmark implementation; it is
not treated as zero.

## Run the benchmark

Real inference is opt-in and is not part of normal CI:

```bash
python -m pip install -e ".[benchmark]"
python -m benchmarks.benchmark_embedding_models \
  --models bge-m3 qwen3-embedding-0.6b nomic-embed-text all-minilm-l6-v2 \
  --hardware-excluded-models qwen3-embedding-8b
```

`--models` is deliberately required so an 8B model is never loaded accidentally. A machine capable
of running every candidate should include `qwen3-embedding-8b` in that list and omit its hardware
exclusion.

Run a resource-appropriate subset with:

```bash
python -m benchmarks.benchmark_embedding_models \
  --models all-minilm-l6-v2 qwen3-embedding-0.6b \
  --hardware-excluded-models qwen3-embedding-8b
```

The canonical outputs are:

- `benchmarks/results/m4-retrieval-results.json` — machine-readable configuration, rankings,
  measurements, failures, and selection;
- `docs/experiments/m4-embedding-model-comparison.md` — generated human-readable comparison.

A failed model is retained as a structured result. Selection is marked `provisional` whenever any
requested candidate fails, including an out-of-memory failure. No missing result is fabricated.

## Selection policy

The default is selected quality-first. The runner successively keeps models within 0.01 of the best
NDCG@10, MRR, and Recall@10, then prefers lower parameter footprint and mean query latency. This
avoids selecting a disproportionately large model for a marginal quality difference. A provisional
result must not be adopted as the architectural default until failed or unevaluated candidates and
local hardware constraints have been reviewed. A candidate may be explicitly recorded as a hardware
exclusion; this is distinct from an unexplained failure or omission.

The measured comparison and current decision are recorded in
`docs/experiments/m4-embedding-model-comparison.md` after a benchmark run.
