# Agent Workbench

## Setup

1. Activate the project's Python environment and install dependencies with
   `python -m pip install -e ".[workbench,pdf,dev]"`.
2. Start Docker Desktop, then local Qdrant on `http://localhost:6333`:
   `docker run --rm --name context-engine-qdrant -p 6333:6333 qdrant/qdrant`.
3. Install/start Ollama and pull a small tool-capable model, for example
   `ollama pull llama3.2:3b`. Use a quantization suitable for the local hardware;
   inspect the installed model with `ollama show llama3.2:3b`.
4. Set any non-default environment variables listed below.
5. Launch the workbench and wait for preloaded-document ingestion to finish.

Initial embedding-model setup can require a download; subsequent inference runs locally.
The workbench indexes exact-token chunks and persists source lifecycle state in Qdrant.
See [source ingestion](../api/source-ingestion.md) for replacement, recovery, and rebuild semantics.

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
- collection: `context-engine-workbench-m5-v1`
- embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- chunk budget: 128 tokens including heading context/special tokens; overlap: up to 16 tokens
- five uploads maximum across `.txt`, `.md`, and `.pdf`
- text/Markdown: 256 KiB per file
- PDF: 10 MiB per file, 100 pages, 1048576 extracted characters

Optional environment variables:

- `CONTEXT_ENGINE_WORKBENCH_MODEL`
- `CONTEXT_ENGINE_OLLAMA_BASE_URL`
- `CONTEXT_ENGINE_OLLAMA_TIMEOUT_SECONDS`
- `CONTEXT_ENGINE_EMBEDDING_MODEL`
- `CONTEXT_ENGINE_EMBEDDING_MODEL_REFERENCE`
- `CONTEXT_ENGINE_QDRANT_URL`
- `CONTEXT_ENGINE_QDRANT_TIMEOUT_SECONDS`
- `CONTEXT_ENGINE_WORKBENCH_COLLECTION`
- `CONTEXT_ENGINE_WORKBENCH_CHUNK_TOKENS`
- `CONTEXT_ENGINE_WORKBENCH_CHUNK_OVERLAP_TOKENS`
- `CONTEXT_ENGINE_WORKBENCH_MAX_UPLOADS`
- `CONTEXT_ENGINE_WORKBENCH_MAX_UPLOAD_BYTES`
- `CONTEXT_ENGINE_WORKBENCH_MAX_PDF_BYTES`
- `CONTEXT_ENGINE_WORKBENCH_MAX_PDF_PAGES`
- `CONTEXT_ENGINE_WORKBENCH_MAX_PDF_TEXT_CHARACTERS`

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
The source list shows chunk counts and ingestion outcomes. Same-name uploads replace their
previous chunks; individual delete and clear actions remove all chunks for the persisted
uploaded sources, including after restart. Preloaded sources remain indexed.

Context assembly and hybrid retrieval remain future work. Local reranking is optional as described below.

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
They are not continuous health monitoring. Displayed runs belong to the browser session;
source tracking and index lifecycle state persist in Qdrant. Startup explicitly recovers
interrupted writes. A pending index blocks search; use Recover source index or reload.
Run one writer process per collection. No cross-process transaction or atomic visibility is claimed.


## Reusable source processing

Uploads and preloaded documents use `context_engine.knowledge.processing`.
The workbench acquires bytes, checks upload filenames and counts, and translates typed
processing failures into UI errors. The core validates byte and extracted-character
limits, UTF-8 or PDF format, and nonempty extracted content. Text/Markdown uploads use the configured
per-file byte limit as both the byte and character cap. PDF uploads have separate byte,
page, and extracted-character limits. Markdown syntax and whitespace remain intact; a leading
UTF-8 BOM is removed. Each processed source is split into budget-checked retrieval chunks.

Within the upload catalog, a filename identifies a logical source. Uploading revised
content under the same name updates that record and does not consume another upload
slot. SHA-256 revision metadata is separate from source identity. Different filenames
remain distinct sources. Upload filenames are identities within a collection-wide namespace.
Preloaded IDs use full package filenames, including extensions. M4 collections are retained;
use the new M5 default or a new collection for rebuilding and explicitly reupload original files.

See [ADR-006](../architecture/decisions/ADR-006-knowledge-document-processing.md) for block
location semantics and the knowledge/retrieval boundary. See
[ADR-009](../architecture/decisions/ADR-009-source-index-lifecycle.md) for durable lifecycle state
and the [rebuild instructions](../api/source-ingestion.md#migration-and-rebuild).
The 128/16 token settings are operational defaults, not benchmark-selected quality settings.

## PDF extraction and diagnostics

PDF support requires the optional `pdf` extra (also installed by `dev`). If it is missing,
ingestion reports installation guidance. The extractor reads an existing text layer;
it performs no OCR and cannot guarantee layout, table structure, or visual reading order.
Encrypted and malformed PDFs are rejected. PDFs with no usable extracted text fail clearly.

Extraction-empty pages have explicit page diagnostics; mixed documents show a partial
extraction warning after ingestion. These warnings remain outside source text and are
updated with same-name revisions or cleared with uploads. Retrieved PDF evidence shows
source page numbers and page-to-text spans in metadata. PDF input byte/page/text caps
limit accepted data, but they do not guarantee parser CPU or peak memory limits.

See the [PDF API](../api/pdf-processing.md) and
[chunking API](../api/document-chunking.md). The combined deterministic pipeline tests verify
text/PDF processing, chunk coverage and token limits, embedding composition, page provenance
in search evidence, and tool policy enforcement. They use controlled model/tokenizer fixtures;
live inference and retrieval-quality benchmarking remain separate checks.

## Optional local reranking

Reranking is disabled by default. Install `python -m pip install -e ".[reranking]"`
and explicitly prepare `cross-encoder/ms-marco-MiniLM-L6-v2` before enabling it:

```bash
hf download cross-encoder/ms-marco-MiniLM-L6-v2 --revision 233902d25c440f23af6f7d6e94d2946bac0bee0a
export CONTEXT_ENGINE_RERANKING_ENABLED=true
export CONTEXT_ENGINE_RERANKING_MODEL_REFERENCE=/absolute/path/to/prepared/snapshot
```

The workbench always loads this model offline with remote code disabled. Model preparation
is an explicit setup operation. Enabled initialization failures are labeled `reranking`;
enabled scoring/input failures appear in structured tool results and traces. Set enabled
back to `false` to intentionally compare the same upstream retrieval without reranking.

Additional application settings: `CONTEXT_ENGINE_RERANKING_REVISION` (optional),
`CONTEXT_ENGINE_RERANKING_DEVICE` (`cpu`), `CONTEXT_ENGINE_RERANKING_CANDIDATES` (20),
`CONTEXT_ENGINE_RERANKING_FINAL_LIMIT` (5), `CONTEXT_ENGINE_RERANKING_BATCH_SIZE` (8),
`CONTEXT_ENGINE_RERANKING_INPUT_TOKENS` (512). Candidate and final limits are positive
integers; final cannot exceed candidate. Actual search tool top_k still caps returned
results. Combined query/passage input includes special tokens; oversized pairs fail without
truncation. These are operational bounds, not benchmark-selected defaults. Reranking
requires no reindexing. The model cannot choose providers or resource settings.

Evidence displays upstream and reranker diagnostics separately from canonical metadata.
Logits are higher-is-more-relevant native scores, not relevance probabilities. Actual local
verification is opt-in with `CONTEXT_ENGINE_RERANKING_INTEGRATION_MODEL` set to the
prepared snapshot and `pytest tests/integration/test_local_reranking_integration.py`.
