# Context Engine

> A local-first context-aware agent runtime for building intelligent, controllable AI applications.

## Overview

Context Engine is a local-first AI platform for building context-aware and agentic applications. The runtime is designed around a strict separation between probabilistic model behavior and deterministic application behavior: models propose actions, while the runtime validates, authorizes, executes, and records them.

## Current Status

**Milestone:** M4 — Embeddings & Vector Search

**Completed:** M1 Foundation, M2 Agent Runtime, M3 Deterministic Tool Use

M3 established the deterministic tool execution boundary, including:

- typed tool registration and lookup
- input schema validation
- policy-controlled execution
- structured tool errors
- execution tracing
- human approval for selected tools
- provider-independent model/tool integration
- local Ollama end-to-end tool calling verification

The current end-to-end demonstration uses a calculator tool with a local Ollama model. The model can propose the calculator call, but the runtime remains responsible for validation, policy, approval, execution, and returning the result to the model.

## Goals

- Agentic AI
- Deterministic tool use
- Embeddings and vector search
- Modern RAG
- Local LLM inference
- MLOps
- Evaluation

## Architecture

The core execution boundary is:

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

The model never directly executes a tool or controls runtime state. Provider-specific model behavior is isolated behind the Model Gateway, while tools are controlled by the Tool Runtime.

See the [Architecture Overview](docs/architecture/overview.md) and [Tool Runtime Architecture](docs/architecture/tool-runtime.md) for the current system design and the [Development Roadmap](docs/product/roadmap.md) for milestone status.

## Example Application

**Context-Aware DJ** is the planned reference application demonstrating context-aware retrieval, agent orchestration, controlled tool use, and user-facing execution visibility.

## Documentation

- [Product Requirements](docs/product/prd.md)
- [Project Context](docs/product/PROJECT_CONTEXT.md)
- [Roadmap](docs/product/roadmap.md)
- [Architecture](docs/architecture/overview.md)
- [Tool Runtime Architecture](docs/architecture/tool-runtime.md)
- [Architecture Decisions](docs/architecture/decisions/)

## Development

The project uses automated formatting, linting, type checking, tests, and GitHub Actions CI. Development generally follows:

```text
Issue
 ↓
Feature Branch
 ↓
Implementation
 ↓
Tests
 ↓
Pull Request
 ↓
Review
 ↓
Merge
```

## Local Ollama Verification (Optional)

You can verify the provider-independent model/tool boundary with a local Ollama instance.

1. Install and run Ollama locally.
2. Pull a local model, for example: `ollama pull llama3.2`.
3. Set the integration environment variables.
4. Run the optional integration test:

```bash
CONTEXT_ENGINE_RUN_OLLAMA_INTEGRATION=1 \
CONTEXT_ENGINE_OLLAMA_MODEL=llama3.2 \
pytest tests/integration/test_ollama_runtime_integration.py
```

Optional environment variables:

- `CONTEXT_ENGINE_OLLAMA_BASE_URL` (default: `http://localhost:11434`)
- `CONTEXT_ENGINE_OLLAMA_TIMEOUT_SECONDS` (default: `30`)

The integration test verifies that the model receives the registered calculator tool, requests it, the runtime executes it, the result is returned to the model, and a final response is produced. The test is opt-in and does not run as part of the normal test suite unless explicitly enabled.

## License

...