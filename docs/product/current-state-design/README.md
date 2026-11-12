# Current-State Design

These mockups show what Context Engine can do today, in the visual style of the
[first prototype design](../first-prototype-design/README.md). They add a per-prompt
**technical view** that exposes the agent run and the retrieval pipeline, in the spirit
of the [Agent Workbench](../agent-workbench.md).

They are static design mockups, not an implemented interface. The Streamlit workbench
remains the only running UI. All prompts, answers, scores, counts and durations in the
screens are illustrative examples, not measurements.

Open the `.html` files directly in a browser. They need no server, build step or network.

## Design decisions

| Decision | Choice |
| --- | --- |
| Scope | Only implemented features appear as working. Activities, saved decisions, plugins, search and history are listed in the sidebar with a `Planned` tag. |
| Technical view placement | A right-hand inspector opened per run, so the answer and its runtime detail are visible together. |
| Conversation model | A thread of independent runs. Each prompt is a fresh run and runs last for the browser session only. |
| Trace data | Data the runtime records today is shown as real. Data it does not record is shown in dashed sections tagged `Not yet recorded`. |
| Retrieval view | The finished run drawn as a staged pipeline. There is no live or in-progress state, because the runtime returns the whole result at once. |
| Retrieval settings | Read-only. Strategy, reranking and evidence selection are application configuration and are not editable per prompt. |

## Screens

### 1. Run thread, default dense retrieval

[01-run-default.html](01-run-default.html)

Two runs with the inspector open on a `search_documents` run in the default
configuration. The pipeline shows a single dense stage; lexical search, fusion, reranking
and evidence selection appear as switched-off stages.

### 2. Run thread, full retrieval pipeline

[02-run-full-pipeline.html](02-run-full-pipeline.html)

The same layout with hybrid retrieval, cross-encoder reranking and evidence selection
enabled. Each evidence passage lists its per-stage scores and ranks, and a selection table
shows which candidates were kept or excluded and why.

### 3. Failed run

[03-failed-run.html](03-failed-run.html)

A calculator run that ends in a structured tool error, plus a run that hits the iteration
limit. The inspector names the failing phase and never presents the run as a success.

### 4. Knowledge sources

[04-knowledge-sources.html](04-knowledge-sources.html)

Preloaded and uploaded documents with chunk counts, ingestion outcomes, PDF extraction
warnings, upload limits, delete, clear and index recovery.

## Technical view contents

| Section | Source in the codebase | State |
| --- | --- | --- |
| Outcome, model iterations, terminal state | `AgentRuntimeExecutionResult` | Recorded |
| Execution lifecycle | `workbench/presentation.py` lifecycle steps built from tool traces | Recorded |
| Tool trace: arguments, policy, approval, status, error | `ToolExecutionTrace` | Recorded |
| Retrieved evidence: score, source, metadata, truncation | `search_documents` structured result | Recorded |
| Per-stage scores, ranks and candidate counts | `RetrievalStageDiagnostic` | Recorded for hybrid and reranking |
| Hybrid branch, fusion and reranking durations | `RetrievalStageDiagnostic.duration_seconds` | Recorded for hybrid and reranking |
| Selection diagnostics | `selection_diagnostics` in the tool result | Recorded when selection is enabled |
| Run configuration | Workbench configuration | Recorded |
| State-machine timeline | `AgentExecutionStatus` transitions | Not yet recorded per run |
| Model-call and tool-execution timings | — | Not yet recorded |
| Token usage | `ModelUsage` exists on the gateway response but is not exposed by the runtime result | Not yet recorded |

The three `Not yet recorded` rows are the instrumentation this design would need before it
could be built in full. The state path drawn in those sections is the one the transition
map implies for a run with one tool call; it is not observed data.

## Files

Each `.html` file is self-contained: its styles and the shared sidebar are inlined, and it
uses no scripts. A change to the shared shell must be repeated in all four files.
