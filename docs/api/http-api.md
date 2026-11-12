# HTTP API (`/api/v1`)

A thin FastAPI adapter (`context_engine.api`) over `ContextEngineApplication`. Routes validate
transport input and call the core facade; they hold no business logic.

**Local use only.** There is no authentication. The launcher binds to `127.0.0.1` by default;
do not expose it to a network.

## Run it

```bash
python -m pip install -e ".[api,pdf]"
python -m context_engine.api [--host 127.0.0.1] [--port 8000] [--static-dir DIR]
```

The launcher composes the live application (Ollama, Qdrant, local embeddings), prepares the
index, then serves. `--static-dir` serves a built frontend at `/` after the API routes when
the directory exists; client-side routes such as `/runs/{id}` fall back to `index.html`, while
unknown `/api/...` paths and missing files stay `404`. The OpenAPI document is at `/openapi.json` for client type generation.

## Endpoints

| Method and path | Purpose |
| --- | --- |
| `POST /runs` | Start a run from `{"prompt": ...}`. `202` with a run summary. |
| `GET /runs` | List run summaries (no events or traces). |
| `GET /runs/{id}` | Full structured run: tool results, traces, events. |
| `GET /runs/{id}/events` | Server-sent event stream (below). |
| `POST /runs/{id}/approval` | Answer the run's pending tool approval (below). |
| `GET /sources` | Indexed `preloaded` and `uploaded` sources. |
| `POST /sources` | Multipart upload, repeated `files` field. |
| `DELETE /sources/{id}` | Delete one uploaded source. |
| `DELETE /sources` | Delete all uploaded sources. |
| `POST /sources/recover` | Recover interrupted index writes. |
| `GET /system` | Dependency status, tools, prompt presets, effective read-only settings, active run id. |

All paths are under `/api/v1`. Responses are structured data; clients derive display views.

In a run, `tool_results[].output` is the model output: exactly what the model saw.
`traces[].diagnostics` holds runtime-only tool diagnostics, which were never sent to the model,
or `null`. `search_documents` records its evidence-selection report there as
`diagnostics.selection` (ADR-017).

## Event stream

Each frame carries `id` (event sequence), `event` (event kind) and `data` (a JSON event
with `run_id`, `sequence`, `timestamp`, `kind`, `payload`). The server replays recorded
events first, then follows live, and closes after `run_finished`. To resume, reconnect with
the `Last-Event-ID` header or `?after=<sequence>`. Idle periods emit `: keep-alive` comments.
Retrieval stages do not emit live events.

## Tool approval

Tools named in `CONTEXT_ENGINE_APPROVAL_TOOLS` (empty by default) pause the run before they
execute. The run reports status `awaiting_approval` with `pending_approval`
(`tool_name`, `arguments`, `invocation_id`, `reason`), and a `tool_approval_requested` event is
streamed. Answer with:

```json
POST /api/v1/runs/{id}/approval
{"decision": "approved", "reason": "optional"}
```

`decision` is `approved` or `rejected`. Returns the run summary. An unanswered request is
rejected after `CONTEXT_ENGINE_APPROVAL_TIMEOUT_SECONDS` (default 120). Rejection and timeout
mark the run `failed`; the trace records the policy and approval decisions. A run keeps the
single active-run slot while it waits. There is no cancel endpoint.

## Errors

Every non-2xx response is `{"error": {"code", "message", "details"}}`.

| Status | Codes |
| --- | --- |
| `404` | `unknown_run`, `unknown_source`, `http_error` |
| `409` | `run_already_active` (`details.active_run_id`), `no_pending_approval`, `source_not_deletable` |
| `422` | `invalid_prompt`, `invalid_request`, `invalid_upload`, `source_rejected` |
| `500` | `source_operation_failed`, `source_recovery_failed` |

Only one run is active at a time; runs are held in memory and lost on restart. A run that
fails is reported with status `failed` and an `error_phase`, never as a success.
Upload limits and validation are owned by the knowledge layer (`UploadLimits`).
Retrieval strategy, reranking and evidence selection are read-only configuration.
