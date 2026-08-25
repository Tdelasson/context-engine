# Embedding & Retrieval Architecture

**Status:** M4 architecture foundation  
**Last updated:** 2026-08-19

This document describes the M4 embedding and semantic retrieval foundation. It intentionally does not define the full Modern RAG architecture planned for M5.

## 1. Purpose

Embeddings provide a numerical representation of the semantic content of documents and queries. Vector search can then retrieve information that is similar in meaning rather than requiring exact keyword matches.

M4 establishes the following pipeline:

```text
Document
   │
   ▼
LocalEmbeddingProvider
   │
   ▼
Embedding
   │
   ▼
QdrantVectorStore
   │
   ▼
Retriever
   │
   ▼
SearchResult[]
```

The core boundary is:

> **EmbeddingProvider creates vectors. VectorStore stores and searches vectors. Retriever coordinates retrieval.**

## 2. Domain Concepts

### Document

A document is the unit of information ingested and retrieved in M4.

Conceptually:

```text
Document
├── id
├── content
└── metadata
```

M4 deliberately operates on complete documents. Chunking is deferred to M5.

### Embedding

An embedding is a vector generated from a document or query together with metadata describing the embedding configuration.

At minimum, the metadata identifies:

```text
Embedding
├── vector
├── model
└── dimensions
```

Vectors from different embedding models are different embedding spaces and must not be mixed within the same vector-store collection.

### SearchResult

A search result is provider-independent retrieval output:

```text
SearchResult
├── document
└── score
```

The score represents the similarity/ranking score returned by the configured vector-search strategy.

## 3. Embedding Provider

The `EmbeddingProvider` abstraction isolates embedding generation from the rest of Context Engine.

The initial concrete implementation is `LocalEmbeddingProvider`.

```text
EmbeddingProvider
        │
        ▼
LocalEmbeddingProvider
        │
        ▼
Local embedding model
```

Direct local inference means the model is executed locally by the application environment. Ollama is not required for embeddings. An Ollama-backed provider can be added later if useful.

### Query and document embedding

The provider exposes separate operations conceptually equivalent to:

```python
embed_documents(documents)
embed_query(query)
```

Some embedding models use different instructions or encoding behavior for queries and documents. Those model-specific details remain inside the provider.

### Batch embedding

Document embedding supports batches so ingestion can process multiple documents efficiently:

```text
Documents
   ↓
Batch
   ↓
EmbeddingProvider
   ↓
Embeddings
```

## 4. Candidate Embedding Models

M4 will benchmark:

- BGE-M3
- Qwen3-Embedding-0.6B
- Qwen3-Embedding-8B
- nomic-embed-text
- all-MiniLM-L6-v2

The architecture did not select one of these models in advance. The completed M4 benchmark selected
`sentence-transformers/all-MiniLM-L6-v2` as the initial default for the recorded local CPU
environment. It achieved NDCG@10 of 0.9210, MRR of 0.9125, and Recall@10 of 1.0 while providing the
smallest measured parameter footprint and the strongest local latency/throughput results among the
quality-equivalent candidates. Qwen3-Embedding-8B was recorded as a hardware exclusion and remains a
future re-evaluation candidate.

## 5. Vector Store

The `VectorStore` abstraction owns vector persistence and similarity search. It does not generate embeddings.

The first implementation is `QdrantVectorStore`, backed by a local Qdrant instance running through Docker during development.

```text
VectorStore
     │
     ▼
QdrantVectorStore
     │
     ▼
Qdrant
```

### Responsibilities

The vector-store boundary covers:

- inserting/upserting embeddings;
- deleting records;
- similarity search;
- metadata filtering; and
- returning provider-independent search results.

Qdrant-specific request/response types must not leak into the domain API.

### Embedding-space isolation

A vector-store collection uses one embedding model/configuration. The collection has a fixed vector dimensionality and similarity metric.

Cosine similarity is the initial default. The metric remains configurable so a model-specific recommendation can be adopted when appropriate.

### Document storage in M4

For the initial implementation, Qdrant records contain:

```text
vector
+
document ID
+
document content
+
metadata
```

This keeps M4 self-contained and avoids introducing a second persistence system before it is needed. A future dedicated document store remains possible behind the `VectorStore`/retrieval boundaries.

## 6. Metadata Filtering

Documents can carry structured metadata alongside their content.

Semantic search can therefore be combined with filtering:

```text
Query
 │
 ├── semantic similarity
 │
 └── metadata constraints
          │
          ▼
       VectorStore
          │
          ▼
     SearchResult[]
```

The Context Engine filter representation remains provider-independent. Qdrant payload filters are an implementation detail.

## 7. Retriever

The `Retriever` is the application-facing semantic retrieval abstraction.

For M4 it coordinates query embedding and vector-store search:

```text
User Query
    │
    ▼
EmbeddingProvider.embed_query()
    │
    ▼
Query Embedding
    │
    ▼
VectorStore.search()
    │
    ▼
SearchResult[]
```

The Retriever is intentionally separate from the VectorStore. This allows M5 to evolve retrieval without coupling higher-level components to database operations.

Future retrieval may become:

```text
Retriever
├── Dense Retrieval
├── Sparse Retrieval
├── Hybrid Fusion
└── Reranking
```

## 8. Simple Ingestion

M4 provides a small synchronous ingestion path:

```text
Documents
   │
   ▼
EmbeddingProvider.embed_documents()
   │
   ▼
Embeddings
   │
   ▼
VectorStore.upsert()
```

Advanced parsing, chunking, metadata extraction, asynchronous ingestion, and large-scale ingestion orchestration are deferred to later milestones.

## 9. M4 Evaluation

M4 includes a small hand-curated retrieval dataset consisting of documents, queries, and explicit relevance judgments.

The same dataset is used for every candidate model. This makes the benchmark model-independent.

### Quality metrics

- Recall@K
- MRR
- NDCG@K

### Performance measurements

- document embedding throughput;
- query embedding latency;
- vector-search latency;
- memory usage;
- model size; and
- vector dimensionality.

The benchmark is a focused M4 experiment. It is not part of the normal CI test suite and does not attempt to replace the full evaluation/MLOps framework planned for M9.

The implemented benchmark fixes K at 1, 5, and 10 and uses a portable in-memory cosine
`VectorStore` so every model follows the same `EmbeddingProvider` → `Ingestor` → `Retriever`
execution path without requiring Qdrant for the experiment. The runner records machine-readable
results, environment details, per-model failures, and a generated human-readable comparison.

The default-selection policy is quality-first. The runner successively keeps models within 0.01 of
the best NDCG@10, MRR, and Recall@10, followed by parameter footprint and mean query latency. A run
with failed or unexplained unevaluated candidates produces a provisional decision rather than
silently excluding them; deliberate local-hardware exclusions are recorded separately.

See `docs/experiments/m4-retrieval-benchmark.md` for the fixed methodology and
`docs/experiments/m4-embedding-model-comparison.md` for measured results after execution.

## 10. M4 vs M5

M4 establishes dense semantic retrieval:

```text
Documents
 ↓
Embeddings
 ↓
Vector Store
 ↓
Similarity Search
 ↓
Results
```

M5 will build the modern RAG layer on top of this foundation, including concerns such as:

- document processing;
- chunking;
- dense + sparse retrieval;
- hybrid retrieval;
- reranking;
- context selection; and
- query transformation where useful.

M4 should remain focused on making the underlying semantic retrieval primitive correct, measurable, and replaceable.

## Related ADRs

- `ADR-003-embedding-provider-abstraction.md`
- `ADR-004-vector-store-and-retrieval-architecture.md`
- `ADR-005-retrieval-evaluation-strategy.md`
