# Agent Workbench Demo

## Preparation checklist

1. Install the workbench dependencies with `python -m pip install -e ".[workbench,dev]"`.
2. Start local Qdrant on `http://localhost:6333`.
3. Install/start Ollama and pull a small 1–3B instruct model, for example `llama3.2:1b`.
4. Set any non-default environment variables listed below.
5. Launch the workbench once and wait for demo-document ingestion to finish.
6. Run one retrieval prompt and one calculator prompt to warm the model before presenting.

## Run locally

```powershell
$env:CONTEXT_ENGINE_WORKBENCH_MODEL = "llama3.2:1b"
streamlit run src/context_engine/workbench/streamlit_app.py
```

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

