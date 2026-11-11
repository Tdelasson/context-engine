# Context Engine Agent Workbench

**Issue:** #53  
**Status:** Implemented in PR #57
**Scope:** Local interface for agent execution and retrieval

This is the original M4 design brief, updated where M5 changed behavior. Current setup and
configuration are in the [workbench guide](agent-workbench.md).

## Design brief

The workbench supports one integrated agent run. A user submits one prompt; the configured
local model either responds or proposes `search_documents`/`calculator`; the existing Agent and
Tool runtimes validate, authorize, execute, and trace that proposal; then the model receives the
structured result and produces the final response.

The workbench is deliberately an application-composition and presentation layer. It does not
access provider payloads or Qdrant directly from rendering code. Chunking, lexical and hybrid
retrieval, reranking, and evidence selection are composed from the core packages through
application settings, not implemented in the workbench. Automatic context assembly is M6 work.

## Integrated-flow wireframe

```text
+--------------------------------------------------------------------------------+
| Context Engine Agent Workbench      LIVE | LOCAL | tools + chunked retrieval   |
| Tool-mediated retrieval is live; automatic context assembly is future work.    |
+---------------------------+----------------------------------------------------+
| DOCUMENTS                 | ASK THE AGENT                                      |
|                           |                                                    |
| Project documents  Ready  | Prompt preset [ Project architecture           v ] |
|  - architecture.md        | [ editable free-form prompt                    ]   |
|  - roadmap.md             |                                      [ Run agent ] |
|  - demo-guide.txt         |                                                    |
|                           | FINAL RESPONSE                                     |
| Upload .txt/.md/.pdf      | [ response grounded in the structured tool result ]|
| [ choose files ]          |                                                    |
| Limits: 5 files           | LIVE EXECUTION LIFECYCLE                           |
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
- Preloaded project documents are ingested idempotently on application preparation. Each uploaded file is one
  source, split into chunks that carry `source_kind=uploaded` metadata. A same-name upload
  replaces the previous revision.
- Clearing uploads deletes only sources tracked as uploaded by this workbench. Preloaded sources
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

