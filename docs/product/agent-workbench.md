# Agent Workbench

## Setup

1. Activate the project's Python environment and install dependencies with
   `python -m pip install -e ".[workbench,dev]"`.
2. Start Docker Desktop, then local Qdrant on `http://localhost:6333`:
   `docker run --rm --name context-engine-qdrant -p 6333:6333 qdrant/qdrant`.
3. Install/start Ollama and pull a small tool-capable model, for example
   `ollama pull llama3.2:3b`. Use a quantization suitable for the local hardware;
   inspect the installed model with `ollama show llama3.2:3b`.
4. Set any non-default environment variables listed below.
5. Launch the workbench and wait for preloaded-document ingestion to finish.

Initial embedding-model setup can require a download; subsequent inference runs locally.
Each document is embedded whole, without M5 chunking.

## Run locally

```powershell
$env:CONTEXT_ENGINE_WORKBENCH_MODEL = "llama3.2:1b"
streamlit run src/context_engine/workbench/streamlit_app.py
```

Open `http://localhost:8501`. To use the 3B model instead of the 1B default,
set `CONTEXT_ENGINE_WORKBENCH_MODEL` to `llama3.2:3b` before launching.

The default configuration uses:

- Ollama: `http://localhost:11434`
- Qdrant: `http://localhost:6333`
- collection: `context-engine-workbench`
- embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- five uploads maximum, 256 KiB per file, `.txt` and `.md` only

Optional environment variables:

- `CONTEXT_ENGINE_WORKBENCH_MODEL`
- `CONTEXT_ENGINE_OLLAMA_BASE_URL`
- `CONTEXT_ENGINE_OLLAMA_TIMEOUT_SECONDS`
- `CONTEXT_ENGINE_EMBEDDING_MODEL`
- `CONTEXT_ENGINE_EMBEDDING_MODEL_REFERENCE`
- `CONTEXT_ENGINE_QDRANT_URL`
- `CONTEXT_ENGINE_QDRANT_TIMEOUT_SECONDS`
- `CONTEXT_ENGINE_WORKBENCH_COLLECTION`
- `CONTEXT_ENGINE_WORKBENCH_MAX_UPLOADS`
- `CONTEXT_ENGINE_WORKBENCH_MAX_UPLOAD_BYTES`

Timeouts must be finite and positive. Each prompt starts a fresh run, with at most four
model iterations and 256 output tokens per model invocation. The workbench allows its two
registered tools through the existing policy boundary. Interactive approval is not implemented in
the workbench.

## Behavior

Preset and free-form prompts use the same Agent Runtime execution path. The model may respond
directly or propose `search_documents` or `calculator`; validation, policy, execution, and results
remain owned by the Tool Runtime. Model decisions and latency can vary.

The UI displays the final response, execution lifecycle, retrieved evidence, structured tool results,
and traces. Evidence identifies its document, source, metadata, score, and any content truncation.
Uploads are validated before ingestion and labeled separately from preloaded project documents.
Clearing uploads removes only documents tracked as uploaded by the current session.

Automatic context assembly, chunking, hybrid retrieval, and reranking remain M5/M6 work.

## Verification

Run deterministic checks in the activated development environment:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src/
pre-commit run --all-files
```

With the workbench extra installed, pytest also exercises actual Streamlit widgets with fake
model/tool fixtures. These UI tests do not require running local services.

Verify the application composition against local services separately:

```powershell
$env:CONTEXT_ENGINE_RUN_WORKBENCH_INTEGRATION = "1"
$env:CONTEXT_ENGINE_WORKBENCH_MODEL = "llama3.2:3b"
python -m pytest tests/integration/test_workbench_integration.py -v
```

This live test checks preloaded search, uploaded-fact retrieval, calculation, and upload cleanup.
It creates and removes its own unique Qdrant collection. It does not change the workbench collection.
The existing search-tool integration test and its environment variables are documented in the README.

### Recorded local verification — 2026-10-01

The live workbench test passed with both `llama3.2:1b` (Q8_0) and `llama3.2:3b` (Q4_K_M),
cached MiniLM embeddings, and local Docker Qdrant. It verified preloaded retrieval, an uploaded
`COBALT-742` fact in the final answer, calculator output 19, and retrieval after upload removal.
The existing search-tool integration and deterministic Streamlit widget tests also passed.

## Failure guidance

| Displayed failure | Recovery |
| --- | --- |
| Configuration | Correct the labeled environment value; timeouts and upload limits must be positive. |
| Embedding dependency | Install the workbench extra and prepare the configured embedding model locally. |
| Vector-store dependency | Start Docker/Qdrant, check port 6333 and collection compatibility, then reload. |
| Preparation/ingestion | Check the embedding and vector-store services before retrying. |
| Upload validation | Use non-empty UTF-8 `.txt`/`.md` files within the documented count/size limits. |
| Agent runtime/model timeout | Check Ollama, the configured model, and timeout; warm the model before retrying. |
| Tool execution | Inspect the structured error and trace for invalid arguments, unavailable retrieval, or arithmetic errors. |
| Iteration limit | Use a shorter, specific request and inspect repeated tool proposals; no successful final run is claimed. |

Dependency labels distinguish a configured model from initialized embeddings/vector storage.
They are not continuous health monitoring. Uploaded-document tracking and displayed runs belong to
the browser session; Qdrant records persist independently. Clear uploads before closing the session.

