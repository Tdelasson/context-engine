# ADR-004: Vector Store and Retrieval Architecture

- **Status:** Accepted
- **Date:** 2026-08-19
- **Decision Type:** Architecture
- **Related Milestone:** M4 — Embeddings & Vector Search

## Context

Context Engine needs a deterministic retrieval foundation that can store embeddings, perform semantic similarity search, apply metadata filters, and return structured results to higher-level retrieval logic.

The vector database must remain an implementation detail. The Agent Runtime, ingestion pipeline, and future RAG components should not depend directly on a specific vector database or client SDK.

M4 should provide a simple dense-retrieval foundation without prematurely implementing chunking, hybrid retrieval, reranking, or a complete document store.

## Decision

Context Engine will separate vector generation, vector storage, and retrieval orchestration into distinct responsibilities:

```text
Document
   │
   ▼
EmbeddingProvider
   │
   ▼
Embedding
   │
   ▼
VectorStore
   │
   ▼
Retriever
   │
   ▼
SearchResult[]
```

The responsibilities are:

### EmbeddingProvider

Creates vectors from documents and queries. It does not store or search vectors.

### VectorStore

Stores embeddings and associated document records, searches vectors, applies metadata filters, and deletes records. It does not generate embeddings.

### Retriever

Coordinates query embedding and vector-store search and provides the application-facing retrieval abstraction. It is deliberately separate from `VectorStore` so future retrieval strategies can be introduced without coupling callers to database operations.

## Vector Store Implementation

The first concrete implementation will use **Qdrant**, run locally through Docker during development.

```text
VectorStore
     │
     ▼
QdrantVectorStore
     │
     ▼
Qdrant
```

Qdrant is selected because it provides a local, practical vector-search system with similarity search, payload/metadata filtering, persistence, and a path toward larger deployments without requiring a different architectural model.

The `VectorStore` interface must not expose Qdrant-specific request/response types. Context Engine defines its own domain types such as `SearchResult` and filter representations.

## Embedding Space Isolation

One embedding model/configuration defines one vector space for a vector-store collection.

Vectors from different embedding models must not be mixed within the same collection because their dimensions and semantic spaces may differ.

A collection therefore has a fixed embedding configuration, including at minimum:

- embedding model identity
- vector dimensionality
- similarity metric

The initial similarity metric is cosine similarity. The design permits a different metric when required by the selected embedding model.

## Search Results

Vector search returns provider-independent structured results rather than database-specific objects.

Conceptually:

```python
SearchResult(
    document=Document(...),
    score=0.91,
)
```

The result contains the matched document and its similarity score. Additional retrieval metadata may be added later without exposing Qdrant types.

## Metadata Filtering

Documents have structured metadata and the vector store supports filtering alongside semantic search.

Conceptually:

```text
Query vector
     │
     ├── similarity search
     │
     └── metadata filters
              │
              ▼
           Qdrant
              │
              ▼
        SearchResult[]
```

Context Engine owns the filter abstraction; Qdrant payload filters remain an implementation detail.

## Document Ownership in M4

For M4, vector-store records will contain the document content, document ID, metadata, and embedding.

This intentionally keeps the initial retrieval foundation self-contained:

```text
Qdrant record
├── document_id
├── content
├── metadata
└── vector
```

A separate document store is deferred until a concrete requirement makes it worthwhile. The `VectorStore` abstraction should avoid making callers depend on Qdrant's storage representation, so a future document-store split remains possible.

### Why not a separate document store yet?

A separate document store would provide stronger separation between source-data persistence and vector indexing, and could become preferable for large documents or more complex storage requirements. However, it would also add another persistence system and retrieval hop before M4 needs either.

M4 prioritizes a small, understandable, locally runnable semantic retrieval foundation.

## Retrieval Boundary

Callers should depend on `Retriever`, not on Qdrant or direct vector-store operations when requesting semantic retrieval.

This allows future evolution from:

```text
Retriever
   ↓
Dense Vector Search
```

to:

```text
Retriever
   ├── Dense Retrieval
   ├── Sparse Retrieval
   ├── Hybrid Fusion
   └── Reranking
```

without changing the higher-level retrieval contract.

## Simple Ingestion

M4 will provide a deliberately simple ingestion path:

```text
Documents
   │
   ▼
EmbeddingProvider
   │
   ▼
Embeddings
   │
   ▼
VectorStore
```

Batch document embedding is supported by the provider interface. Advanced parsing, chunking, asynchronous ingestion, and metadata extraction are deferred to later milestones, particularly M5.

## Rationale

The architecture follows a strict separation of concerns:

> **EmbeddingProvider creates vectors. VectorStore stores and searches vectors. Retriever coordinates retrieval.**

This keeps the retrieval foundation testable, provider-independent, and compatible with the project's local-first philosophy.

## Alternatives Considered

### Direct Qdrant usage throughout the application

Rejected because it would couple domain code to a specific database SDK and make future vector-store changes unnecessarily invasive.

### VectorStore generates embeddings internally

Rejected because it mixes embedding inference and storage responsibilities and makes it harder to benchmark or replace embedding providers independently.

### No Retriever abstraction

Rejected because direct VectorStore access would make future hybrid retrieval and reranking harder to introduce without changing callers.

### Separate document store in M4

Deferred. The additional infrastructure is not currently justified by the M4 requirements.

### FAISS or an in-process-only index as the initial store

Not selected because Qdrant better matches the project's intended progression toward a persistent, locally deployable vector service while remaining straightforward to run during development.

## Consequences

### Positive

- Clean separation between embedding, storage, and retrieval.
- Qdrant remains replaceable.
- Metadata filtering is available from the beginning.
- M4 remains small enough to understand and test.
- M5 can add modern RAG techniques above the Retriever boundary.
- Local Docker deployment preserves the local-first workflow.

### Negative

- Qdrant becomes an M4 development dependency.
- A Retriever abstraction adds another layer even though initial retrieval is simple.
- Storing content in the vector store may need to be revisited if document storage requirements grow.

## Related Documentation

- `docs/architecture/embedding-and-retrieval.md`
- `docs/architecture/decisions/ADR-003-embedding-provider-abstraction.md`
- `docs/architecture/decisions/ADR-005-retrieval-evaluation-strategy.md`
- `docs/product/roadmap.md`
