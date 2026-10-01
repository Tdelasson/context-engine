# Context Engine Agent Workbench

**Issue:** #53  
**Status:** Implementation design  
**Scope:** Meeting-ready M3/M4 demonstration

## Design brief

The workbench demonstrates one integrated agent run. A user submits one prompt; the configured
local model either responds or proposes `search_documents`/`calculator`; the existing Agent and
Tool runtimes validate, authorize, execute, and trace that proposal; then the model receives the
structured result and produces the final response.

The workbench is deliberately an application-composition and presentation layer. It does not
access provider payloads or Qdrant directly from rendering code, and it does not implement
automatic context assembly, chunking, reranking, hybrid search, or other M5/M6 behavior.

## Integrated-flow wireframe

```text
+--------------------------------------------------------------------------------+
| Context Engine Agent Workbench                 LIVE | LOCAL | M3 + M4          |
| Tool-mediated retrieval is live; automatic context assembly is future work.    |
+---------------------------+----------------------------------------------------+
| DOCUMENTS                 | ASK THE AGENT                                      |
|                           |                                                    |
| Demo documents     Ready  | Prompt preset [ Project architecture           v ] |
|  - architecture.md        | [ editable free-form prompt                    ]   |
|  - roadmap.md             |                                      [ Run agent ] |
|  - demo-guide.md          |                                                    |
|                           | FINAL RESPONSE                                     |
| Upload .txt/.md           | [ response grounded in the structured tool result ]|
| [ choose files ]          |                                                    |
| Limits: 5 × 256 KiB       | LIVE EXECUTION LIFECYCLE                           |
| [ Clear uploads ]         | 1 User prompt                         complete     |
|                           | 2 Model proposal                      complete     |
| DEPENDENCIES              | 3 Registry + schema validation        complete     |
| Model       connected     | 4 Policy decision                     allow        |
| Embeddings  connected     | 5 Tool execution                      complete     |
| Qdrant      connected     | 6 Structured ToolResult               complete     |
| Runtime     ready         | 7 Final model response                 complete     |
|                           |                                                    |
|                           | RETRIEVED EVIDENCE / TOOL RESULT                    |
|                           | document_id | score | source | metadata | content   |
|                           |                                                    |
|                           | EXECUTION TRACE                                    |
|                           | invocation | arguments | policy | status | error    |
+---------------------------+----------------------------------------------------+
```

## Interaction and failure states

- Presets only populate the same editable prompt field used by free-form prompts; both execute
  through the same application method.
- Demo documents are ingested idempotently on application preparation. Uploaded files are one
  document each and receive deterministic IDs plus `source_kind=uploaded` metadata.
- Clearing uploads deletes only IDs tracked as uploaded by this workbench. Preloaded document IDs
  are never included in that delete operation.
- Initialization, upload, ingestion, model, malformed-proposal, retrieval, tool, timeout, and
  runtime failures are displayed as failures with a phase and message. They are never rendered as
  successful runs.
- The primary hierarchy is prompt → response → lifecycle → evidence → trace. Configuration and
  document management remain secondary in the sidebar.

## Visual direction

Use Streamlit's native typography and controls with a restrained dark-blue accent, compact status
labels, bordered evidence cards, and readable structured data. The prototype intentionally avoids
a custom component library or decorative imagery so the live execution path remains the focus.

