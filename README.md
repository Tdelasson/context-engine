# Context Engine

> A local-first, context-aware agent runtime for building controllable AI applications.

Context Engine keeps probabilistic model behavior separate from deterministic application
behavior. The model proposes actions; the runtime validates, authorizes, executes, and
records them. Everything runs locally: Ollama for the language model, local embedding
inference, and Qdrant for search.

It is an engineering and learning project covering agentic AI, deterministic tool use,
modern RAG, local inference, and evaluation. The planned reference application is a
**Context-Aware DJ**.

## How it works

```text
User prompt
    ↓
LLM proposes a tool call
    ↓
Schema validation → Policy (allow / deny / require approval)
    ↓
Deterministic tool execution
    ↓
Structured result + execution trace
    ↓
LLM answers from the result
```

The model never executes a tool or changes runtime state directly.

## Status

Milestones 1–4 are complete and milestone 5 (Modern RAG) is in its final stage.

| Area | State |
| --- | --- |
| Agent runtime with an explicit state machine | Done |
| Tool runtime: validation, policy, human approval, tracing | Done |
| Local embeddings, Qdrant vector search, retrieval benchmark | Done |
| Document processing (text, Markdown, PDF), chunking, durable ingestion | Done |
| Lexical BM25, hybrid retrieval, cross-encoder reranking, evidence selection | Done, optional (dense retrieval is the default) |
| Larger RAG evaluation: dataset, ablations, answer quality | In progress |
| Context system, inference optimization, Context-Aware DJ | Planned |

See the [roadmap](docs/product/roadmap.md) for details.

## Try it

The Agent Workbench is a local Streamlit app where you can ask questions over indexed
documents, upload your own, and inspect every tool call and trace.

You need Python 3.11+, [Ollama](https://ollama.com), and Docker.

```bash
git clone https://github.com/Tdelasson/context-engine.git
cd context-engine
python -m pip install -e ".[workbench,pdf]"
docker run --rm -p 6333:6333 qdrant/qdrant
```

In a second terminal:

```bash
ollama pull llama3.2:1b
streamlit run src/context_engine/workbench/streamlit_app.py
```

Open `http://localhost:8501`. The first start downloads a small embedding model.
Configuration, optional retrieval strategies, and troubleshooting are in the
[workbench guide](docs/product/agent-workbench.md).

## Documentation

- [Product requirements](docs/product/prd.md) and [roadmap](docs/product/roadmap.md)
- [Architecture overview](docs/architecture/overview.md), with
  [tool runtime](docs/architecture/tool-runtime.md) and
  [embedding and retrieval](docs/architecture/embedding-and-retrieval.md) details
- [Architecture decision records](docs/architecture/decisions/)
- [API notes](docs/api/) for processing, chunking, ingestion, and reranking
- [Experiments and benchmark results](docs/experiments/)

## Contributing

Development setup, validation commands, and opt-in integration tests are in
[CONTRIBUTING.md](CONTRIBUTING.md). Rules for AI coding agents are in [AGENTS.md](AGENTS.md).

## License

[MIT](LICENSE)
