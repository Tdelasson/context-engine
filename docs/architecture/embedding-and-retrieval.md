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

### Tool-mediated retrieval

Applications can expose the `Retriever` through the read-only `search_documents` tool:

```text
Agent Runtime
    │
    ▼
Tool Runtime
    │
    ▼
search_documents
    │
    ▼
Retriever
    │
    ▼
SearchResult[]
    │
    ▼
bounded structured ToolResult
```

The tool depends only on the provider-independent `Retriever` contract. It does not
access an embedding provider, vector store, or Qdrant directly. The application owns
the `top_k` and model-visible content limits, so the model cannot request an unbounded
number or size of results.

Tool-mediated retrieval is model-selected: the model proposes when to call
`search_documents`, and the Tool Runtime validates, authorizes, executes, and traces
that proposal. It is not automatic context retrieval, context assembly, query
transformation, or advanced RAG; those remain later M5/M6 concerns.

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

## M5 processing and chunking

Knowledge now owns source interpretation and searchable passage construction:

```text
SourceInput (supplied bytes, stable identity, explicit format)
   ↓
process_source (UTF-8 text/Markdown or optional PDF text-layer extraction)
   ↓
ProcessedSource (text, located blocks/pages, revision, diagnostics)
   ├── to_document ────────────────────────────┐
   ↓                                          │
StructureAwareChunker + model-compatible       │
token counter                                 │
   ↓                                          │
DocumentChunk.to_document                     │
   └──────────────────────────────────────────┘
   ↓
Ingestor → EmbeddingProvider → VectorStore
   ↓
Retriever → search_documents → Tool Runtime → Agent
```

Applications acquire bytes and assign stable logical source IDs. Knowledge processing
validates formats and byte/text/page limits, preserves source revision and locations,
and reports extraction diagnostics. PDF extraction uses original one-based page numbers;
empty pages are explicit and partial extraction is reported. Offsets reference the
combined extracted Unicode text, not PDF byte or visual coordinates.

Chunking prefers sections, paragraphs, and sentence boundaries, with a Unicode-safe
fallback. It records exact source spans, page references, heading context, actual overlap,
and deterministic identities tied to source revision and configuration. The full embedding
input is counted with the configured model's tokenizer, including document prefix,
special tokens, and supplemental heading context. Chunk size and overlap are explicit
experiment settings; retrieval-quality defaults have not been selected by a benchmark.

Knowledge does not embed, persist, or retrieve. The existing `Ingestor` accepts mapped
chunk `Document` values as an explicit composition path. The workbench continues its
whole-document catalog pending ingestion-lifecycle integration; replacing/deleting sets
of chunks and migrating an index are separate work. The existing tool validation, policy,
execution, and tracing boundary applies to either document representation.

See [processing API](../api/document-processing.md),
[PDF API](../api/pdf-processing.md), [chunking API](../api/document-chunking.md),
[ADR-006](decisions/ADR-006-knowledge-document-processing.md),
[ADR-007](decisions/ADR-007-pdf-text-extraction.md), and
[ADR-008](decisions/ADR-008-structure-aware-document-chunking.md).

## M5 source indexing lifecycle

M5 workbench ingestion processes supplied text/Markdown/PDF sources, chunks with the
loaded embedding tokenizer, and uses `SourceIngestionCoordinator` for durable source
replacement/deletion. `SourceLifecycleStore` persists source manifests alongside chunk
records; Qdrant excludes manifests from retrieval and fails closed for pending mutations.
M4 whole-document `Ingestor` and benchmark artifacts remain available separately.
See [ADR-009](decisions/ADR-009-source-index-lifecycle.md) and the
[source ingestion API](../api/source-ingestion.md) for recovery, single-writer limits,
index version compatibility, and rebuild instructions.

## M5 evidence-level benchmark

The chunked dense benchmark labels supporting spans in canonical processed source
text, binding source identity and revision rather than chunk IDs. Overlapping chunk
copies and multi-page spans use cumulative union coverage. Development and held-out
queries have separate aggregate denominators; unsupported queries record results
without undefined recall or inferred abstention. See [ADR-010](decisions/ADR-010-evidence-span-retrieval-evaluation.md)
and the [recorded dense experiment](../experiments/m5-chunked-dense-benchmark.md).
M4 document-level results remain historical artifacts.
