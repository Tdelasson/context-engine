# ADR-003: Provider-Independent Embedding Abstraction

- **Status:** Accepted
- **Date:** 2026-08-19
- **Decision Type:** Architecture
- **Related Milestone:** M4 — Embeddings & Vector Search

## Context

Context Engine needs semantic representations of documents and queries so that retrieval can compare meaning rather than relying only on lexical matches. Embeddings are model-dependent and different embedding models have different dimensions, quality, language support, inference costs, and recommended query/document encoding procedures.

The project is local-first and should be able to run embedding inference locally without requiring a hosted embedding API or an external inference service such as Ollama.

At the same time, the rest of Context Engine should not become coupled to a particular embedding model, library, or inference runtime.

## Decision

Context Engine will define a provider-independent `EmbeddingProvider` abstraction.

The initial implementation will be a `LocalEmbeddingProvider` that performs direct local model inference inside the application process.

The interface will distinguish document and query embedding:

```python
embed_documents(documents: Sequence[Document]) -> Sequence[Embedding]
embed_query(query: str) -> Embedding
```

The abstraction must support batch document embedding because ingestion should be able to process multiple documents efficiently.

The initial implementation will evaluate these candidate local embedding models:

- BGE-M3
- Qwen3-Embedding-0.6B
- Qwen3-Embedding-8B
- nomic-embed-text
- all-MiniLM-L6-v2

The final default model will be selected from benchmark results rather than being fixed architecturally in advance.

## Embedding Representation

An `Embedding` is a structured representation of a vector and its generation metadata. At minimum, metadata should identify:

- embedding model
- vector dimensionality

The representation may be extended with additional model metadata when useful for reproducibility or validation.

Vectors produced by different embedding models are treated as different embedding spaces. They must not be mixed within the same vector-store collection.

## Query vs Document Embedding

The provider exposes separate operations because some embedding models recommend different encoding instructions or processing for queries and documents.

The provider implementation is responsible for applying model-specific recommendations while preserving a stable Context Engine API.

## Local Inference

Direct local inference means that the embedding model is loaded and executed by the local Python/application environment rather than being accessed through Ollama or a hosted API.

Ollama remains a possible future provider/runtime integration, but it is not a dependency of the initial embedding implementation.

```text
Context Engine
      │
      ▼
EmbeddingProvider
      │
      ▼
LocalEmbeddingProvider
      │
      ▼
Local embedding model
      │
      ▼
Embedding
```

## Rationale

This design preserves the project's provider-independence and local-first principles while allowing M4 to explore multiple real embedding models.

The abstraction prevents model-specific details from leaking into ingestion, vector storage, retrieval, or the Agent Runtime.

Supporting one concrete implementation initially is sufficient. The abstraction exists to protect the architecture from provider/model coupling, not because multiple providers are required immediately.

## Alternatives Considered

### Ollama as the required embedding runtime

Rejected for the initial implementation. Ollama is useful as a local model runtime, but requiring it would add an unnecessary runtime dependency and hide part of the embedding inference pipeline that M4 is intended to explore.

### Hosted embedding API as the initial implementation

Rejected because it conflicts with the local-first development goal and introduces external cost, availability, and privacy dependencies.

### A single hard-coded embedding model

Rejected because it would prevent a meaningful comparison of retrieval quality and inference cost and would couple the architecture to one model choice prematurely.

### One generic `embed()` operation

Rejected because query and document encoding can have different model-specific requirements.

## Consequences

### Positive

- Embedding inference remains provider-independent.
- Local execution works without Ollama or a hosted API.
- Multiple candidate models can be benchmarked through the same interface.
- Batch ingestion is supported naturally.
- Model-specific query/document behavior remains encapsulated.

### Negative

- The abstraction adds a small amount of API surface.
- Different models may require model-specific configuration behind the same interface.
- Embedding models with different dimensions cannot share a vector-store collection.

## Related Documentation

- `docs/architecture/embedding-and-retrieval.md`
- `docs/architecture/decisions/ADR-004-vector-store-and-retrieval-architecture.md`
- `docs/architecture/decisions/ADR-005-retrieval-evaluation-strategy.md`
- `docs/product/roadmap.md`
