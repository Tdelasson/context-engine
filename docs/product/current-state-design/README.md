# Current-State Design

These mockups show what Context Engine can do today, in the visual style of the
[first prototype design](../first-prototype-design/README.md). They add a per-prompt
**technical view** that exposes the agent run and the retrieval pipeline, in the spirit
of the [Agent Workbench](../agent-workbench.md).

They are static design mockups, not an implemented interface. The React app in `frontend/`
implements them; the screens also describe the interactive UI planned in
[ADR-015](../../architecture/decisions/ADR-015-runtime-run-events.md) and
[ADR-016](../../architecture/decisions/ADR-016-http-api-and-react-frontend.md). All prompts, answers, scores, counts and durations in the
screens are illustrative examples, not measurements.

Open the `.html` files directly in a browser. They need no server, build step or network.

## Design decisions

| Decision | Choice |
| --- | --- |
| Scope | Only implemented features appear as working. Activities, saved decisions, plugins, search and history are listed in the sidebar with a `Planned` tag. |
| Technical view placement | A right-hand inspector opened per run, so the answer and its runtime detail are visible together. |
| Conversation model | A thread of independent runs. Each prompt is a fresh run and runs last for the browser session only. |
| Trace data | Shown from the run's typed events (ADR-015): state transitions, model-call and tool-call timings, and token usage when the model reports it. Values in the mockups are illustrative. |
| Live runs | A run streams its events as it executes. Lifecycle steps and the state timeline fill in live, and steps not reached yet are shown dashed. The composer is disabled while a run is active, because only one run is active at a time. |
| Retrieval view | The retrieval pipeline and evidence come from the structured tool result, so they appear once the run has finished. Retrieval stages do not emit live events. |
| Approval | Tools listed in the `approval_required_tools` setting pause the run. The person approves or rejects in the thread, with an optional reason. An unanswered request is rejected after a timeout. Rejection and timeout fail the run. |
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

### 5. Run in progress

[05-run-in-progress.html](05-run-in-progress.html)

A run between its tool call and its final answer. The lifecycle and the state timeline are
partly filled in, the current step is highlighted and later steps are dashed. Step timings
and token usage show what has been reported so far. Retrieval is marked as available after
the run finishes, and the composer is disabled.

### 6. Run awaiting approval

[06-run-awaiting-approval.html](06-run-awaiting-approval.html)

A run paused on a tool that requires approval. The thread shows the pending tool call with
its arguments, approve and reject actions, an optional reason and the timeout. The
inspector shows the require-approval policy decision, the pending approval and the time
spent waiting. The tool has not executed.

## Technical view contents

| Section | Source in the codebase | State |
| --- | --- | --- |
| Outcome, model iterations, terminal state | `AgentRuntimeExecutionResult` | Recorded |
| Execution lifecycle | Run events and `ToolExecutionTrace`, derived by the client | Recorded, live while running |
| Tool trace: arguments, policy, approval, status, error | `ToolExecutionTrace` | Recorded |
| Retrieved evidence: score, source, metadata, truncation | `search_documents` structured result | Recorded |
| Per-stage scores, ranks and candidate counts | `RetrievalStageDiagnostic` | Recorded for hybrid and reranking |
| Hybrid branch, fusion and reranking durations | `RetrievalStageDiagnostic.duration_seconds` | Recorded for hybrid and reranking |
| Selection diagnostics | `diagnostics.selection` on the search tool's trace | Recorded when selection is enabled |
| Run configuration | Workbench configuration | Recorded |
| State-machine timeline | `state_transitioned` events | Recorded, live |
| Model-call timings and token usage | `model_call_completed` events (tokens only when the model reports them) | Recorded, live |
| Tool-execution timing | `tool_call_finished` event (`executed` flag, duration) | Recorded, live |
| Pending approval | `pending_approval` on the run and the `tool_approval_requested` event | Recorded, live |
| Approval timeout | `approval_timeout_seconds` in the system configuration | Read-only configuration |

The event contracts are defined in ADR-015. The mockups only show data those contracts
provide; retrieval-stage data is not part of the live stream.

## Files

Each `.html` file is self-contained: its styles and the shared sidebar are inlined, and it
uses no scripts. A change to the shared shell must be repeated in all six files.
