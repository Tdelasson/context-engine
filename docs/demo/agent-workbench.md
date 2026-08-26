# Agent Workbench Demo

## Preparation checklist

1. Install the workbench dependencies with `python -m pip install -e ".[workbench,dev]"`.
2. Start local Qdrant on `http://localhost:6333`.
3. Install/start Ollama and pull a small 1–3B instruct model, for example `llama3.2:1b`.
4. Ensure the embedding model is already available locally when the laptop will be offline.
5. Set any non-default environment variables listed below.
6. Launch the workbench once and wait for demo-document ingestion to finish.
7. Run one retrieval prompt and one calculator prompt to warm the model before presenting.

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

## Two-minute script

1. Point out the preloaded documents and the explicit statement that this is tool-mediated M4
   retrieval, not automatic M5/M6 context assembly.
2. Select **Project architecture**, run the prompt, and follow the lifecycle from model proposal
   through validation, policy, `search_documents`, structured result, and final response.
3. Show the retrieved document ID, score, metadata, bounded content, and `preloaded` source label.
4. Select **Calculator**, run it, and show that the same deterministic boundary executes a
   different tool.
5. Upload a small `.txt` or `.md` fact sheet, ask the editable prompt about its unique fact, and
   show the `uploaded` source label in the evidence.
6. Clear uploads and point out that the preloaded demo documents remain ready.

If a live dependency fails, use the labeled error to explain the boundary that failed. Do not
present a recorded trace as a live success.
