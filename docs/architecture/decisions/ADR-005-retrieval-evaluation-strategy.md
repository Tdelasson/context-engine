# ADR-005: Retrieval Evaluation Strategy

- **Status:** Accepted
- **Date:** 2026-08-19
- **Decision Type:** Architecture
- **Related Milestone:** M4 — Embeddings & Vector Search

## Context

M4 is intended to establish a semantic retrieval foundation, not merely demonstrate that a vector database can return results. Different embedding models can make different trade-offs between retrieval quality, inference cost, memory use, and latency.

Context Engine therefore needs a small, reproducible experiment that can compare candidate embedding models using the same data and retrieval task.

A full evaluation framework is already planned for M9. M4 should establish a useful baseline without prematurely building that larger system.

## Decision

M4 will include a small, hand-curated retrieval dataset and a model-independent benchmark.

The dataset will contain:

- a modest collection of representative documents;
- a set of natural-language retrieval queries; and
- explicit relevance judgments identifying which documents are relevant to each query.

The exact dataset size may evolve during implementation, but it should remain small enough to inspect and maintain manually.

Every candidate embedding model must be evaluated against the same dataset, queries, relevance judgments, vector-store configuration, and top-k settings.

## Candidate Models

The initial experiment will compare:

- BGE-M3
- Qwen3-Embedding-0.6B
- Qwen3-Embedding-8B
- nomic-embed-text
- all-MiniLM-L6-v2

The benchmark determines the eventual default model rather than the architecture hard-coding one in advance.

## Quality Metrics

The M4 benchmark will measure retrieval quality using:

- Recall@K
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (NDCG@K)

These metrics provide complementary views of whether relevant documents are retrieved and how highly they are ranked.

The benchmark should use fixed K values appropriate to the small dataset, such as 1, 5, and 10 where meaningful.

## Performance Metrics

The benchmark will also record engineering characteristics relevant to local-first deployment:

- document embedding throughput;
- query embedding latency;
- vector-search latency;
- memory usage;
- model size; and
- vector dimensionality.

These measurements are intended to expose quality/performance trade-offs rather than establish production capacity guarantees.

## Reproducibility

Benchmark inputs and relevance judgments are version-controlled with the project. Results should record the model identity and relevant configuration so that comparisons can be repeated after implementation changes.

The benchmark is an experiment and should not be required for every normal CI run. Embedding-model inference and Qdrant-backed benchmark execution are too heavyweight for the project's ordinary unit-test path.

## Relationship to M9 Evaluation

M4 establishes a focused retrieval experiment and baseline. It does not attempt to build the complete evaluation infrastructure.

M9 will introduce the broader evaluation and MLOps layer, which may reuse the M4 dataset and benchmark concepts and extend them to:

- retrieval regression testing;
- agent evaluation;
- tool-call evaluation;
- model benchmarks;
- experiment tracking;
- performance monitoring; and
- broader AI execution metrics.

The M4 benchmark should therefore remain simple and portable enough to be incorporated into the M9 evaluation system later.

## Rationale

A small hand-curated dataset makes relevance judgments explicit and inspectable. Using the same benchmark for every model makes the comparison fair. Measuring both quality and local inference cost prevents selecting a model solely because it achieves the highest retrieval score.

This approach also gives M4 a measurable exit criterion without prematurely expanding the scope into a general-purpose evaluation platform.

## Alternatives Considered

### Evaluate only by manual inspection

Rejected because subjective inspection does not provide reproducible quantitative comparisons.

### Build the full evaluation framework in M4

Rejected because evaluation infrastructure is explicitly a later milestone and would distract from the retrieval foundation.

### Run the benchmark in normal CI

Rejected because model inference and Qdrant introduce substantial runtime and environment requirements that are inappropriate for the default test suite.

### Use a synthetic/randomly generated dataset

Rejected for the initial benchmark because a small hand-curated dataset provides clearer relevance judgments and is easier to reason about when diagnosing retrieval failures.

## Consequences

### Positive

- Embedding model selection becomes evidence-based.
- Retrieval quality has a measurable baseline.
- Local performance trade-offs are visible.
- The benchmark remains understandable and reproducible.
- M9 can build on the same dataset and metrics.

### Negative

- The dataset requires manual maintenance.
- Small datasets cannot fully represent production retrieval behavior.
- Local performance measurements vary with hardware and runtime configuration.

## Related Documentation

- `docs/architecture/embedding-and-retrieval.md`
- `docs/architecture/decisions/ADR-003-embedding-provider-abstraction.md`
- `docs/architecture/decisions/ADR-004-vector-store-and-retrieval-architecture.md`
- `docs/product/roadmap.md`
