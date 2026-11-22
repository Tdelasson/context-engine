# Contributing

Rules for AI agents working in this repository are in [AGENTS.md](AGENTS.md). This file covers
the local development setup, the validation commands, and the opt-in integration tests.

## Development setup

Requires Python 3.11 or newer.

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
pre-commit install
```

Optional extras, defined in `pyproject.toml`:

| Extra | Adds |
| --- | --- |
| `dev` | pytest, ruff, mypy, pre-commit, and `pypdf` for the PDF tests |
| `pdf` | PDF text extraction |
| `qdrant` | Qdrant client |
| `reranking` | Local cross-encoder reranking |
| `benchmark` | Local embedding inference for the benchmark runners |
| `api` | HTTP API and the React app: FastAPI, Qdrant and local embeddings |

### Frontend

The React app in `frontend/` needs [Node.js](https://nodejs.org) LTS (24 or newer). It is not
needed for the Python checks.

```bash
cd frontend
npm ci              # install exactly what package-lock.json pins
npm run dev         # Vite dev server; proxies /api to http://127.0.0.1:8000
npm run build       # type-check, then build to frontend/dist
```

Run the API next to the dev server with `python -m context_engine.api`. To serve the built
bundle from the API on one port, pass `--static-dir frontend/dist`.

The TypeScript API types in `frontend/src/api/schema.d.ts` are generated from the API's
OpenAPI document. After changing an API schema, regenerate and commit both files:

```bash
python scripts/export_openapi.py   # writes frontend/openapi.json
cd frontend && npm run gen:api     # writes src/api/schema.d.ts
```

## Workflow

Issue → feature branch → implementation and tests → pull request → CI → review → merge.
Never commit directly to `main`.

## Validation

Run these before opening a pull request. CI runs the same checks.

```bash
pytest
ruff check .
ruff format --check .
mypy src/
pre-commit run --all-files
```

When you change `frontend/` or an API schema, also run, from `frontend/`:

```bash
npm run typecheck
npm run lint
npm run test
npm run build
```

The default test run needs no models or services. Tests that depend on an optional extra
or a live service are skipped unless enabled as described below.

## Opt-in integration tests

Integration tests live in `tests/integration/` and are skipped unless their gate variable
is set to `1`. They need real local services:

- **Ollama** with a tool-capable model pulled, for example `ollama pull llama3.2`.
- **Qdrant** on `http://127.0.0.1:6333`: `docker run --rm -p 6333:6333 qdrant/qdrant`.
  The default uses `127.0.0.1` rather than `localhost` because `localhost` can resolve to
  IPv6 `::1` first, which rootless Podman forwards to a container port Qdrant does not
  listen on.
- **A local embedding model**, for example `sentence-transformers/all-MiniLM-L6-v2`
  (install the `benchmark` or `api` extra).

| Test file | Gate variable | Needs |
| --- | --- | --- |
| `test_ollama_runtime_integration.py` | `CONTEXT_ENGINE_RUN_OLLAMA_INTEGRATION` | Ollama, `CONTEXT_ENGINE_OLLAMA_MODEL` |
| `test_local_embedding_provider_integration.py` | `CONTEXT_ENGINE_RUN_LOCAL_EMBEDDING_INTEGRATION` | `CONTEXT_ENGINE_EMBEDDING_MODEL` |
| `test_qdrant_vector_store_integration.py` | `CONTEXT_ENGINE_RUN_QDRANT_INTEGRATION` | Qdrant |
| `test_source_ingestion_integration.py` | `CONTEXT_ENGINE_RUN_QDRANT_INTEGRATION` | Qdrant |
| `test_retriever_integration.py` | `CONTEXT_ENGINE_RUN_RETRIEVER_INTEGRATION` | Qdrant, `CONTEXT_ENGINE_EMBEDDING_MODEL` |
| `test_search_documents_agent_integration.py` | `CONTEXT_ENGINE_RUN_SEARCH_TOOL_INTEGRATION` | Ollama, Qdrant, `CONTEXT_ENGINE_EMBEDDING_MODEL`, `CONTEXT_ENGINE_OLLAMA_MODEL` |
| `test_qdrant_lexical_integration.py` | `CONTEXT_ENGINE_RUN_QDRANT_LEXICAL_INTEGRATION` | Qdrant 1.16.3 or newer |
| `test_core_application_integration.py` | `CONTEXT_ENGINE_RUN_WORKBENCH_INTEGRATION` | Ollama, Qdrant, `CONTEXT_ENGINE_WORKBENCH_MODEL` |

Example:

```bash
CONTEXT_ENGINE_RUN_SEARCH_TOOL_INTEGRATION=1 \
CONTEXT_ENGINE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2 \
CONTEXT_ENGINE_OLLAMA_MODEL=llama3.2 \
pytest tests/integration/test_search_documents_agent_integration.py
```

The reranking, hybrid-reranking, evidence-selection, chunked-application, and M5 benchmark
integration tests need prepared local model snapshots. Their setup is documented with the
feature they verify: [application](docs/product/agent-workbench.md),
[reranking](docs/experiments/m5-local-reranking.md),
[evidence selection](docs/experiments/m5-evidence-selection.md), and the
[chunked dense benchmark](docs/experiments/m5-chunked-dense-benchmark.md).

### Shared optional variables

| Variable | Default |
| --- | --- |
| `CONTEXT_ENGINE_OLLAMA_BASE_URL` | `http://localhost:11434` |
| `CONTEXT_ENGINE_OLLAMA_TIMEOUT_SECONDS` | `30` |
| `CONTEXT_ENGINE_QDRANT_URL` | `http://127.0.0.1:6333` |
| `CONTEXT_ENGINE_QDRANT_API_KEY` | unset |
| `CONTEXT_ENGINE_QDRANT_TIMEOUT_SECONDS` | `5` |
| `CONTEXT_ENGINE_EMBEDDING_MODEL_ID` | same as `CONTEXT_ENGINE_EMBEDDING_MODEL` |
| `CONTEXT_ENGINE_EMBEDDING_BATCH_SIZE` | `8` |
| `CONTEXT_ENGINE_EMBEDDING_NORMALIZE` | `0` (`1` enables normalized vectors) |
| `CONTEXT_ENGINE_EMBEDDING_QUERY_PREFIX` | empty |
| `CONTEXT_ENGINE_EMBEDDING_DOCUMENT_PREFIX` | empty |

## Benchmarks

Benchmark runners live in `benchmarks/` and are never part of CI. Each experiment report
under [docs/experiments/](docs/experiments/) records its method, results, and the exact
command to reproduce it. Start with the
[M4 retrieval benchmark](docs/experiments/m4-retrieval-benchmark.md).
