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

M4 is now focused on the semantic retrieval foundation: provider-independent embeddings, local embedding inference, Qdrant-backed vector storage, metadata filtering, retrieval, and a small model-independent retrieval benchmark.

The M4 benchmark selected `sentence-transformers/all-MiniLM-L6-v2` as the initial default embedding
model for the recorded local CPU environment. See the generated
[model comparison](docs/experiments/m4-embedding-model-comparison.md) for measured results and the
documented Qwen3-Embedding-8B hardware exclusion.

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

The M4 retrieval foundation is separated into embedding generation, vector storage, and retrieval orchestration:

```text
Document
   ↓
LocalEmbeddingProvider
   ↓
Embedding
   ↓
QdrantVectorStore
   ↓
Retriever
   ↓
SearchResult[]
```

See the [Architecture Overview](docs/architecture/overview.md), [Embedding & Retrieval Architecture](docs/architecture/embedding-and-retrieval.md), and [Tool Runtime Architecture](docs/architecture/tool-runtime.md) for the current system design and the [Development Roadmap](docs/product/roadmap.md) for milestone status.

## Example Application

**Context-Aware DJ** is the planned reference application demonstrating context-aware retrieval, agent orchestration, controlled tool use, and user-facing execution visibility.

## Documentation

- [Product Requirements](docs/product/prd.md)
- [Project Context](docs/product/PROJECT_CONTEXT.md)
- [Roadmap](docs/product/roadmap.md)
- [Architecture](docs/architecture/overview.md)
- [Embedding & Retrieval Architecture](docs/architecture/embedding-and-retrieval.md)
- [Tool Runtime Architecture](docs/architecture/tool-runtime.md)
- [Architecture Decisions](docs/architecture/decisions/)

### M4 Architecture Decisions

- [ADR-003 — Embedding Provider Abstraction](docs/architecture/decisions/ADR-003-embedding-provider-abstraction.md)
- [ADR-004 — Vector Store and Retrieval Architecture](docs/architecture/decisions/ADR-004-vector-store-and-retrieval-architecture.md)
- [ADR-005 — Retrieval Evaluation Strategy](docs/architecture/decisions/ADR-005-retrieval-evaluation-strategy.md)

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

## Local Embedding Provider Verification (Optional)

You can verify local embedding inference with a real embedding model available on your machine.

1. Install a local embedding runtime dependency:
   - `pip install sentence-transformers`
2. Ensure a local embedding model is available (for example a Hugging Face model id or a local model path).
3. Set integration environment variables.
4. Run the optional integration test:

```bash
CONTEXT_ENGINE_RUN_LOCAL_EMBEDDING_INTEGRATION=1 \
CONTEXT_ENGINE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2 \
pytest tests/integration/test_local_embedding_provider_integration.py
```

Optional environment variables:

- `CONTEXT_ENGINE_EMBEDDING_MODEL_ID` (default: same as `CONTEXT_ENGINE_EMBEDDING_MODEL`)
- `CONTEXT_ENGINE_EMBEDDING_BATCH_SIZE` (default: `8`)
- `CONTEXT_ENGINE_EMBEDDING_NORMALIZE` (`1` enables normalized vectors, default: `0`)
- `CONTEXT_ENGINE_EMBEDDING_QUERY_PREFIX` (default: empty string)
- `CONTEXT_ENGINE_EMBEDDING_DOCUMENT_PREFIX` (default: empty string)

## Qdrant Vector Store Verification (Optional)

You can verify the `QdrantVectorStore` implementation with a local Qdrant instance.

1. Install optional dependency:
   - `pip install "qdrant-client>=1.16"`
2. Start Qdrant locally with Docker:

```bash
docker run --rm -p 6333:6333 qdrant/qdrant
```

3. Run the opt-in integration test:

```bash
CONTEXT_ENGINE_RUN_QDRANT_INTEGRATION=1 \
pytest tests/integration/test_qdrant_vector_store_integration.py
```

Optional environment variables:

- `CONTEXT_ENGINE_QDRANT_URL` (default: `http://localhost:6333`)
- `CONTEXT_ENGINE_QDRANT_API_KEY` (default: unset)
- `CONTEXT_ENGINE_QDRANT_TIMEOUT_SECONDS` (default: `5`)

## M4 Embedding Model Benchmark (Optional)

The M4 benchmark evaluates the candidate local embedding models against the same version-controlled
documents, queries, relevance judgments, cosine search configuration, and K values (1, 5, and 10).
It is intentionally opt-in because model downloads and local inference can be resource intensive.

```bash
python -m pip install -e ".[benchmark]"
python -m benchmarks.benchmark_embedding_models \
  --models bge-m3 qwen3-embedding-0.6b nomic-embed-text all-minilm-l6-v2 \
  --hardware-excluded-models qwen3-embedding-8b
```

Model selection is mandatory so the runner never loads Qwen3-Embedding-8B accidentally. On hardware
that can run every candidate, include `qwen3-embedding-8b` in `--models` and omit the hardware
exclusion.

To run a smaller development check:

```bash
python -m benchmarks.benchmark_embedding_models \
  --models all-minilm-l6-v2 qwen3-embedding-0.6b
```

The runner writes machine-readable results under `benchmarks/results/` and a human-readable model
comparison under `docs/experiments/`. See the
[M4 retrieval benchmark methodology](docs/experiments/m4-retrieval-benchmark.md) for configuration,
measurements, failure handling, and the quality-first default-selection policy.

## License

...
