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

The next implementation focus is the provider-independent embedding abstraction and the foundations for vector storage, ingestion, similarity search, filtering, and retrieval evaluation.

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