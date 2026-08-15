# Context Engine

> A local-first context-aware agent runtime for building
> intelligent, controllable AI applications.

## Overview

Context Engine is a local-first AI platform for building
context-aware and agentic applications.

...

## Goals

- Agentic AI
- Deterministic tool use
- Modern RAG
- Vector search
- Embeddings
- Local LLM inference
- MLOps
- Evaluation

## Architecture

[Architecture diagram]

## Example Application

Context-Aware DJ

...

## Project Status

🚧 Early development

## Documentation

- [Product Requirements](docs/product/prd.md)
- [Roadmap](docs/product/roadmap.md)
- [Architecture](docs/architecture/overview.md)

## Development

...

## Local Ollama Verification (Optional)

You can verify the runtime/provider boundary with a local Ollama instance.

1. Install and run Ollama locally.
2. Pull a local model, for example: `ollama pull llama3.2`.
3. Run the optional integration test:

```bash
CONTEXT_ENGINE_RUN_OLLAMA_INTEGRATION=1 \
CONTEXT_ENGINE_OLLAMA_MODEL=llama3.2 \
pytest tests/integration/test_ollama_runtime_integration.py
```

Optional environment variables:

- `CONTEXT_ENGINE_OLLAMA_BASE_URL` (default: `http://localhost:11434`)
- `CONTEXT_ENGINE_OLLAMA_TIMEOUT_SECONDS` (default: `30`)

## License

...