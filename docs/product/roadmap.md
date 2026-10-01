# Context Engine — Development Roadmap

**Version:** 0.1
**Status:** Active
**Project:** Context Engine
**Last Updated:** 2026-10-01

---

# 1. Roadmap Overview

The Context Engine roadmap is structured around a series of progressive milestones.

Each milestone should:

1. Deliver a meaningful piece of functionality.
2. Introduce or deepen an important engineering concept.
3. Produce measurable results where applicable.
4. Leave the codebase in a usable state.
5. Be documented well enough for another developer or AI agent to understand.

The initial roadmap is planned as approximately **16 weeks of development**. The exact duration of individual milestones may change as implementation progresses.

---

# 2. Development Philosophy

Context Engine should be developed incrementally. Complexity should be introduced progressively:

```text
Foundation
    ↓
Agent Runtime
    ↓
Tools & Deterministic Execution
    ↓
Embeddings & Vector Search
    ↓
Modern RAG
    ↓
Context Engine
    ↓
Local Inference
    ↓
Context-Aware DJ
    ↓
Evaluation & MLOps
    ↓
v1.0
```

---

# 3. Milestone Overview

| Milestone | Focus | Approx. Duration |
| --- | --- | ---: |
| M1 | Foundation | Week 1 |
| M2 | Agent Runtime | Weeks 2–3 |
| M3 | Deterministic Tool Use | Week 4 |
| M4 | Embeddings & Vector Search | Weeks 5–6 |
| M5 | Modern RAG | Weeks 7–8 |
| M6 | Context Engine | Weeks 9–10 |
| M7 | Local LLM Inference | Week 11 |
| M8 | Context-Aware DJ | Weeks 12–13 |
| M9 | Evaluation & MLOps | Week 14 |
| M10 | Hardening & v1.0 | Weeks 15–16 |

**Next milestone:** M5 — Modern RAG

**Completed milestones:** M1, M2, M3, M4

---

# 4. M1 — Foundation

**Target:** Week 1

## Objective

Establish a clean software engineering foundation before implementing AI functionality.

## Deliverables

* Repository structure
* `AGENTS.md`
* Product requirements
* Roadmap
* Initial architecture documentation
* Python project configuration
* Development environment
* Dependency management
* Basic test framework
* Linting
* Type checking
* GitHub Actions CI
* Development documentation

## Learning Focus

* Python project architecture
* Git workflows
* CI/CD fundamentals
* AI-assisted software development
* Repository conventions

## Exit Criteria

* Project installs locally.
* Tests execute successfully.
* Linting passes.
* Type checking passes.
* CI runs automatically on pull requests.
* A new AI agent can understand the repository from its documentation.

**Status:** Complete.

---

# 5. M2 — Agent Runtime

**Target:** Weeks 2–3

## Objective

Build the first minimal agent runtime supporting a controlled multi-step reasoning workflow.

## Deliverables

* Model abstraction
* Agent abstraction
* Agent execution loop
* Structured model output
* Basic agent state
* Error handling
* Execution metadata
* Initial agent tests

## Learning Focus

* Agentic AI
* LLM APIs
* Structured outputs
* State management
* Agent execution loops

## Exit Criteria

A user can provide a request and have the agent execute a controlled multi-step reasoning workflow. No external side effects are required yet.

**Status:** Complete.

---

# 6. M3 — Deterministic Tool Use

**Target:** Week 4

## Objective

Introduce controlled, deterministic tool execution between model proposals and external side effects.

## Implemented Architecture

```text
LLM
 ↓
Tool Proposal
 ↓
Schema Validation
 ↓
Policy
 ├── ALLOW ───────────────┐
 ├── DENY                 │
 └── REQUIRE_APPROVAL     │
          ↓               │
       Approval            │
       ├── APPROVED ──────┘
       └── REJECTED
                ↓
          Tool Execution
                ↓
            ToolResult
                ↓
        ToolExecutionTrace
                ↓
               LLM
```

## Deliverables

* Tool interface
* Tool registry
* Tool schemas
* Argument validation
* Tool execution engine
* Policy layer
* Permission model
* Tool errors
* Tool execution tracing
* Human approval mechanism for selected tools

## Implementation Sequence

* **#29** — End-to-end calculator agent integration
* **#32** — Tool policy enforcement
* **#34** — Deterministic tool execution tracing
* **#36** — Human approval for selected tool calls

The calculator and local Ollama integration provide the current end-to-end demonstration. The model can propose a calculator call, while the runtime owns validation, policy, approval, execution, result propagation, and tracing.

## Learning Focus

* Function calling
* Tool use
* Schema validation
* Agent safety
* Deterministic execution
* Human-in-the-loop systems

## Exit Criteria

The LLM cannot directly execute a tool. Every tool execution must pass through:

```text
Validation
    ↓
Policy
    ↓
Approval when required
    ↓
Execution
```

**Status:** Complete.

---

# 7. M4 — Embeddings & Vector Search

**Target:** Weeks 5–6

## Objective

Build the provider-independent foundation for dense semantic retrieval. M4 should establish a correct, measurable, locally runnable retrieval primitive without prematurely implementing the full Modern RAG pipeline planned for M5.

## Architecture

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

The architectural boundary is:

> **EmbeddingProvider creates vectors. VectorStore stores and searches vectors. Retriever coordinates retrieval.**

## Deliverables

* Structured `Document` representation with ID, content, and metadata.
* Structured `Embedding` representation including model and dimensionality metadata.
* Provider-independent `EmbeddingProvider` abstraction.
* Direct local inference through `LocalEmbeddingProvider`.
* Batch document embedding.
* Separate document and query embedding operations.
* Provider-independent `VectorStore` abstraction.
* `QdrantVectorStore` implementation with local Docker deployment.
* One embedding model/configuration per vector-store collection.
* Cosine similarity as the initial metric, with support for model-appropriate alternatives.
* Metadata filtering through a provider-independent filter abstraction.
* Structured `SearchResult` values.
* Dedicated `Retriever` abstraction.
* Simple document ingestion pipeline.
* Initial hand-curated retrieval benchmark.

## Candidate Embedding Models

The initial local-model experiment will compare:

* BGE-M3
* Qwen3-Embedding-0.6B
* Qwen3-Embedding-8B
* nomic-embed-text
* all-MiniLM-L6-v2

The final default embedding model will be selected from benchmark results rather than fixed in the architecture beforehand.

Ollama is not required for embedding inference. A future Ollama-backed provider remains possible.

## Document Storage

For M4, vector-store records will contain document content, document ID, metadata, and the embedding. A separate document store is intentionally deferred until a concrete requirement justifies the additional infrastructure.

## Evaluation

M4 will use a small hand-curated dataset containing documents, queries, and explicit relevance judgments. The benchmark will be model-independent: every candidate model uses the same dataset and retrieval configuration.

Quality metrics:

* Recall@K
* MRR
* NDCG@K

Performance measurements:

* document embedding throughput
* query embedding latency
* vector-search latency
* memory usage
* model size
* vector dimensionality

The benchmark is an M4 experiment, not the full evaluation framework. It will not run as part of normal CI. M9 will introduce the broader evaluation and MLOps infrastructure and can build on the M4 dataset and metrics.

## Explicitly Deferred to M5+

* document chunking
* advanced document parsing
* metadata extraction pipelines
* sparse retrieval
* hybrid retrieval
* reranking
* context selection
* query transformation
* large-scale/asynchronous ingestion
* full evaluation framework

## Learning Focus

* Embeddings
* Vector databases
* Similarity search
* Indexing
* Metadata filtering
* Retrieval engineering
* Local model inference
* Retrieval evaluation

## Exit Criteria

A dataset can be:

```text
Ingested
   ↓
Embedded
   ↓
Stored
   ↓
Queried
   ↓
Retrieved
```

and retrieval quality/performance can be measured reproducibly across the candidate embedding models.

**Status:** Complete. Core deliverables are merged; the integrated agent workbench (#53) remains an open demonstration task.

## Completed Implementation

* [#39](https://github.com/Tdelasson/context-engine/issues/39) — Embedding domain models and provider abstraction (PR #45).
* [#40](https://github.com/Tdelasson/context-engine/issues/40) — LocalEmbeddingProvider (PR #46).
* [#41](https://github.com/Tdelasson/context-engine/issues/41) — VectorStore abstraction, Qdrant backend, and filtering (PR #47).
* [#42](https://github.com/Tdelasson/context-engine/issues/42) — Retriever abstraction (PR #48).
* [#43](https://github.com/Tdelasson/context-engine/issues/43) — Simple document ingestion (PR #49).
* [#50](https://github.com/Tdelasson/context-engine/issues/50) — Hand-curated benchmark dataset (PR #51).
* [#44](https://github.com/Tdelasson/context-engine/issues/44) — Model-independent benchmark and default model selection (PR #52).
* [#54](https://github.com/Tdelasson/context-engine/issues/54) — Retriever-backed search_documents tool through the existing validation, policy, execution, and tracing boundary (PR #55).

The recorded benchmark compares four models on 34 documents and 20 queries. It selected
`sentence-transformers/all-MiniLM-L6-v2` as the initial local CPU default, with Recall@10 of
1.0000, MRR of 0.9125, and NDCG@10 of 0.9210. Qwen3-Embedding-8B was explicitly excluded
for local hardware constraints. These results establish a focused M4 baseline rather than a
production-scale evaluation. See the [model comparison](../experiments/m4-embedding-model-comparison.md)
and [benchmark methodology](../experiments/m4-retrieval-benchmark.md).

---

# 8. M5 — Modern RAG

**Target:** Weeks 7–8

## Objective

Build a production-oriented retrieval pipeline rather than a basic vector search implementation.

## Deliverables

* Document processing
* Chunking strategies
* Metadata extraction
* Dense retrieval
* Sparse retrieval
* Hybrid retrieval
* Reranking
* Context selection
* Query transformation where useful
* Retrieval evaluation framework

## Exit Criteria

The project has measurable retrieval benchmarks and can demonstrate why one retrieval strategy performs better than another.

**Status:** Planned — next milestone. Chunking, sparse/hybrid retrieval, reranking, and context selection remain unimplemented in the merged M4 foundation.

---

# 9. M6 — Context Engine

**Target:** Weeks 9–10

## Objective

Combine context, knowledge, retrieval, agents, and tools into the first actual Context Engine runtime.

## Deliverables

* Context model
* Context sources
* Context assembly
* Context prioritization
* Context metadata
* Context lifecycle
* Agent/context integration
* Knowledge/context integration
* Context-aware tool selection

## Exit Criteria

The runtime can combine current context, historical context, retrieved knowledge, and user intent to produce an agent workflow.

---

# 10. M7 — Local LLM Inference

**Target:** Week 11

## Objective

Introduce local model serving and inference optimization.

## Deliverables

* Local model runtime
* Model serving interface
* Model configuration
* Local embedding inference
* Model loading
* Quantization experiments
* Performance benchmarks
* Resource monitoring

## Benchmark Metrics

* time to first token
* tokens per second
* total latency
* RAM usage
* VRAM usage
* CPU utilization
* GPU utilization

---

# 11. M8 — Context-Aware DJ

**Target:** Weeks 12–13

## Objective

Build the first complete end-to-end application using Context Engine.

## System Flow

```text
User Request
     ↓
Context Analysis
     ↓
Historical Listening Retrieval
     ↓
Music Knowledge Retrieval
     ↓
Candidate Generation
     ↓
Ranking
     ↓
Agent Decision
     ↓
Tool Validation
     ↓
Permission Check
     ↓
Playlist Creation
     ↓
Result
```

## Deliverables

* Music data ingestion
* Listening history processing
* Music metadata integration
* Music embeddings
* Contextual recommendation
* Candidate ranking
* Playlist generation
* External music service integration
* Permission flow
* User interface
* Execution visualization

---

# 12. M9 — Evaluation & MLOps

**Target:** Week 14

## Objective

Turn the project from an engineering prototype into a measurable AI system.

## Deliverables

* Evaluation datasets
* Retrieval benchmarks
* Agent evaluation
* Tool-call evaluation
* Model benchmarks
* Experiment tracking
* Regression tests
* Performance monitoring
* Error tracking
* AI execution traces

## Metrics

### Retrieval

* Recall@K
* MRR
* NDCG

### Agent

* Task success rate
* Tool selection accuracy
* Argument accuracy
* Invalid tool calls
* Average execution steps

### Inference

* TTFT
* Tokens/sec
* Latency
* RAM
* VRAM

---

# 13. M10 — Hardening & v1.0

**Target:** Weeks 15–16

## Objective

Turn the accumulated prototype into a coherent, documented, demonstrable first release.

## Deliverables

* Architecture review
* Security review
* Performance review
* Dependency review
* Test coverage improvements
* Error handling improvements
* UI polish
* Documentation
* Setup instructions
* Demo workflow
* Example configurations
* Deployment documentation
* Release notes
* v1.0 tag

## Exit Criteria

A technically capable developer should be able to clone the repository, follow the documentation, run Context Engine locally, and understand its architecture.

---

# 14. Cross-Cutting Work

Testing, documentation, AI-assisted development, and the GitHub issue → branch → PR → review → merge workflow span all milestones.

Documentation should be updated whenever architecture or behavior changes.

---

# 15. Learning Map

| Learning Goal | Primary Milestone |
| --- | --- |
| Agentic AI | M2 |
| Deterministic Tool Use | M3 |
| Embeddings | M4 |
| Vector Databases | M4 |
| Modern RAG | M5 |
| Context Engineering | M6 |
| Local LLM Serving | M7 |
| Inference Optimization | M7 |
| External AI Integrations | M8 |
| MLOps | M9 |
| AI Evaluation | M9 |
| Observability | M9 |
| Production Engineering | M10 |

---

# 16. Milestone Completion Rule

A milestone is not complete merely because the implementation exists.

A milestone should produce:

```text
Working Feature
+
Tests
+
Documentation
+
Evaluation
+
Demonstrable Result
```

M4 satisfies this rule through merged embedding, vector-store, ingestion, and retrieval implementations, deterministic tests and opt-in local integration coverage, architecture documentation, and the recorded model-independent benchmark. The integrated workbench remains separate open demonstration work under #53.

M3 satisfies this rule through its deterministic tool runtime implementation, automated unit/runtime coverage, architecture documentation, and local Ollama end-to-end calculator demonstration. Quantitative retrieval or model-quality evaluation begins in M4 through the focused embedding/retrieval benchmark and will be expanded into the broader evaluation framework in M9.

---

# 17. Roadmap Changes

The roadmap is allowed to evolve when experiments, technical dependencies, milestone scope, learning opportunities, or architectural constraints justify reprioritization. Major changes should be documented in Git history and, where appropriate, an ADR.

---

# 18. Initial Definition of Done

Context Engine v1.0 should demonstrate:

* [ ] Context-aware agent execution
* [x] Deterministic tool execution
* [x] Schema validation
* [x] Policy-controlled actions
* [x] Embedding generation
* [x] Vector search
* [ ] Modern RAG
* [ ] Hybrid retrieval
* [ ] Reranking
* [ ] Local LLM inference
* [ ] Inference benchmarking
* [ ] Agent evaluation
* [x] Retrieval evaluation (focused M4 baseline; broader framework remains M9)
* [ ] Observability
* [x] Human-in-the-loop actions
* [ ] Context-Aware DJ reference application
* [ ] Polished user interface
* [ ] Complete developer documentation
* [x] Automated CI
* [x] Reproducible local setup

---

# 19. Current Status

**Next milestone:** M5 — Modern RAG

**Project phase:** Semantic retrieval foundation complete; integrated demonstration work remains open before broader Modern RAG development.

**Completed milestones:**

* [x] M1 — Foundation
* [x] M2 — Agent Runtime
* [x] M3 — Deterministic Tool Use
* [x] M4 — Embeddings & Vector Search

**M3 implementation sequence:**

* [x] #29 — End-to-end calculator agent integration
* [x] #32 — Tool policy enforcement
* [x] #34 — Deterministic tool execution tracing
* [x] #36 — Human approval for selected tool calls

**M4 architecture decisions:**

* [x] Provider-independent `EmbeddingProvider` with direct local inference.
* [x] `LocalEmbeddingProvider` with separate query/document embedding operations and batch document embedding.
* [x] Structured embeddings with model/dimensionality metadata.
* [x] One embedding model/configuration per vector-store collection.
* [x] Provider-independent `VectorStore` abstraction with Qdrant as the first implementation.
* [x] Cosine similarity as the initial metric, subject to model recommendations.
* [x] Metadata filtering through the vector-store boundary.
* [x] Dedicated `Retriever` abstraction.
* [x] Simple ingestion pipeline.
* [x] Small hand-curated, model-independent retrieval benchmark.

**Completed M4 deliverables:**

* [x] Implement the M4 embedding contracts and local provider.
* [x] Implement Qdrant-backed vector storage and filtering.
* [x] Add the Retriever and simple ingestion pipeline.
* [x] Build and run the embedding/retrieval benchmark.
* [x] Select `sentence-transformers/all-MiniLM-L6-v2` as the initial default based on benchmark results.
* [x] Expose Retriever-backed document search through the deterministic Tool Runtime (#54, PR #55).

**Open demonstration work:**

* [ ] [#53 — Integrated Context Engine agent workbench](https://github.com/Tdelasson/context-engine/issues/53): complete review, required validation, live local walkthrough, and merge. The workbench is an application demo of M3/M4, not completion of M5/M6 or the Context-Aware DJ.

**Next milestone:**

* [ ] Plan and implement M5 document processing and chunking using the existing retrieval contracts.
* [ ] Add and benchmark sparse/hybrid retrieval, reranking, and context selection against the M4 dense baseline.
* [ ] Keep automatic context assembly and lifecycle integration in M6 and the broader evaluation/MLOps framework in M9.
