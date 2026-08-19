# Context Engine — Project Context

## Project

Context Engine is a local-first context-aware agent runtime for building intelligent, controllable AI applications.

The first reference application will be Context-Aware DJ.

## Current milestone

M4 — Embeddings & Vector Search

## Development workflow

Issue
→ GitHub AI Agent
→ Feature Branch
→ PR
→ CI
→ Human review
→ Merge

Cursor is used as the primary local AI IDE.

GitHub AI Agents are used for issue-driven implementation.

## Source of truth

- Product requirements: `docs/product/prd.md`
- Roadmap: `docs/product/roadmap.md`
- Architecture: `docs/architecture/overview.md`
- Embedding & Retrieval architecture: `docs/architecture/embedding-and-retrieval.md`
- Tool Runtime architecture: `docs/architecture/tool-runtime.md`
- Architecture decisions: `docs/architecture/decisions/`
- AI agent rules: `AGENTS.md`

## Core architecture decisions

- Agent Runtime owns execution state and state transitions.
- State transitions are explicit and deterministic.
- AgentExecutionState is immutable.
- Applications may register tools, but tools must pass through runtime validation and policy before execution.
- Tool policy can allow, deny, or require human approval.
- Human approval is resolved through a provider-independent runtime abstraction.
- Tool execution produces structured ToolResults and execution traces.
- Model access is provider-independent.
- Embedding generation is provider-independent through `EmbeddingProvider`.
- Initial embedding inference uses direct local execution through `LocalEmbeddingProvider`; Ollama is not required.
- `EmbeddingProvider` distinguishes document and query embedding and supports batch document embedding.
- One embedding model/configuration is used per vector-store collection.
- `VectorStore` stores and searches vectors; it does not generate embeddings.
- Qdrant is the initial vector-store implementation and runs locally through Docker.
- Cosine similarity is the initial metric, subject to embedding-model recommendations.
- Retrieval is exposed through a dedicated `Retriever` abstraction.
- M4 uses simple document ingestion and stores document content alongside vector-store records.
- Context is logically separated from knowledge and retrieval.
- Security boundaries must prevent model-generated actions and tools from bypassing runtime policy.

## Current implementation

### M1 Foundation

Complete:
- repository structure and documentation
- Python project configuration
- pytest, ruff, mypy, and pre-commit
- GitHub Actions CI

### M2 Agent Runtime

Complete:
- explicit AgentExecutionState and transition map
- deterministic AgentRuntime execution loop
- provider-independent ModelGateway
- structured model/tool-call contracts
- Ollama gateway integration

### M3 Deterministic Tool Use

Complete:
- typed tool interface and registry
- input schema validation
- deterministic ToolRuntime execution
- ALLOW / DENY / REQUIRE_APPROVAL policy decisions
- structured tool errors
- ToolExecutionTrace
- provider-independent human approval resolver
- end-to-end local Ollama calculator tool-calling integration

Implementation sequence:
- #29 End-to-end calculator agent integration
- #32 Tool policy enforcement
- #34 Deterministic tool execution tracing
- #36 Human approval for selected tool calls

## Current work

M4 — Embeddings & Vector Search.

Architecture is documented before implementation. The immediate implementation focus is the embedding contracts and local provider, followed by Qdrant-backed storage, simple ingestion, retrieval, and the model-independent benchmark.

## M4 Candidate Models

- BGE-M3
- Qwen3-Embedding-0.6B
- Qwen3-Embedding-8B
- nomic-embed-text
- all-MiniLM-L6-v2

The final default model will be selected based on benchmark results rather than being predetermined.

## M4 Evaluation

M4 uses a small hand-curated, model-independent retrieval dataset. It measures Recall@K, MRR, NDCG@K, embedding throughput/latency, vector-search latency, memory usage, model size, and vector dimensionality.

This focused benchmark establishes an M4 baseline. The broader evaluation and MLOps framework remains a later M9 concern.

## Roadmap

M1 Foundation
↓
M2 Agent Runtime
↓
M3 Deterministic Tool Use
↓
M4 Embeddings & Vector Search
↓
M5 Modern RAG
↓
M6 Context Engine
↓
M7 Local LLM Inference
↓
M8 Context-Aware DJ
↓
M9 Evaluation & MLOps
↓
M10 Hardening & v1.0