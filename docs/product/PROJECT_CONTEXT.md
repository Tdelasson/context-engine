# Context Engine — Project Context

## Project

Context Engine is a local-first context-aware agent runtime for
building intelligent, controllable AI applications.

The first reference application will be Context-Aware DJ.

## Current milestone

M2 — Agent Runtime

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
- AI agent rules: `AGENTS.md

## Core architecture decisions

- Agent Runtime owns execution state.
- Agent Runtime owns state transitions.
- State transitions are explicit and deterministic.
- AgentExecutionState is immutable.
- Runtime transitions are defined in an explicit transition map.
- Runtime action/state types are controlled by the runtime.
- Applications may register Tools.
- Tools must pass through validation and policy before execution.
- Model access must be provider-independent.
- Context will eventually support both application context and agent/user context.
- Context storage is logically separated from retrieval and knowledge.
- Security boundaries must prevent malicious tools from bypassing runtime policy.

## Current implementation

### M1 Foundation

Completed:
- repository structure
- AGENTS.md
- README.md
- PRD
- roadmap
- architecture documentation
- pyproject.toml
- pytest
- ruff
- mypy
- pre-commit
- GitHub Actions CI

### M2 Agent Runtime

Completed:
- AgentExecutionStatus
- AgentExecutionState
- explicit transition map
- transition validation
- AgentRuntime skeleton

Current work:
- Model Gateway abstraction

## Current issue

Issue #4:
Define provider-independent Model Gateway abstraction.

Scope:
- model interface
- typed request/response boundary
- explicit model errors
- mockable interface

Out of scope:
- OpenAI
- Anthropic
- Ollama
- llama.cpp
- local inference
- embeddings
- RAG
- tool calling

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