# ADR-015: Typed run events from the Agent and Tool runtimes

- **Status:** Accepted; implemented in #86
- **Date:** 2026-11-12
- **Related issues:** #86, #89

## Context

`AgentRuntimeExecutionResult` returns the outcome, the terminal state, the proposed response,
an error message and the model-iteration count. The Tool Runtime records one
`ToolExecutionTrace` per invocation. Nothing else about a run is recorded:

- the state-machine transitions between `start` and the terminal state;
- how long each model call and each tool execution took;
- token usage, although `ModelUsage` already exists on `ModelResponse`.

The whole result is available only after the run ends. A run on a local model can take from
seconds to minutes, so an interface cannot show progress, and a person cannot be asked to
approve a tool call while the run waits.

AGENTS.md (2.7) requires agent executions to make durations observable. The architecture
overview already describes an append-oriented event log (section 11) and run traces
(section 12), neither of which is implemented. The current-state design
(`docs/product/current-state-design/`) marks the three items above as "not yet recorded".

## Decision

Add typed, immutable run events, emitted by the runtimes through an injected emitter that
delivers them to a sink.

**Contracts.** Event types, the `RunEventSink` protocol and the `RunEventEmitter` live in
`context_engine.observability`. An event is an envelope (`RunEvent`) around a typed payload.
The envelope carries a run id, a sequence number that increases by one per event within a
run, and a timestamp. Payloads hold primitive values only, so the package imports nothing
from the agent, tool or model packages. The initial event set is:

| Event | Payload |
| --- | --- |
| Run started | model id, iteration limit |
| State transition | from status, to status |
| Model call started / completed | iteration, duration, finish reason, input and output tokens when reported, error |
| Tool proposed | invocation (tool name, arguments) |
| Tool validated | accepted, or the validation error |
| Policy decided | decision, reason |
| Approval requested / resolved | invocation, decision, reason |
| Tool call finished | status, whether tool code executed, duration, error |
| Run finished | outcome, terminal status, iterations |

**Emission.** `AgentRuntime` and `ToolRuntime` each accept an optional `RunEventEmitter`.
The emitter wraps a `RunEventSink` and owns the run id, the sequence counter and the clocks.
The application creates one emitter per run and passes the same instance to both runtimes.
The Tool Runtime is constructed separately from the Agent Runtime, so a shared emitter is
what gives a run a single ordered sequence; two runtimes holding a bare sink could not
number their events consistently. They emit at the points where transitions are applied and
tools are executed today.

The terminal tool event is "tool call finished", emitted exactly once per invocation. It
carries an `executed` flag because validation, policy or approval can end an invocation
before any tool code runs; in that case there is no duration. Each started run ends with
exactly one "run finished" event, including a run that raises; the exception is then
re-raised unchanged. The runtimes own
event creation; applications and models cannot inject events. Durations use an injectable
monotonic clock so tests are deterministic.

**Isolation.** Telemetry must not determine runtime behavior. The emitter contains and counts
exceptions raised by a sink, so they do not change transitions, tool execution or the run
outcome. With no emitter configured, behavior is unchanged.

**Compatibility.** Events are additive. `AgentRuntimeExecutionResult`, `ToolResult` and
`ToolExecutionTrace` keep their current shape, so existing callers and tests are unaffected.

**Content.** Tool arguments and outputs appear in events only where the existing trace
already exposes them. Model prompts and raw provider payloads are not included.

**Approval.** Approval-requested and approval-resolved events are emitted around the existing
`ToolApprovalResolver.resolve` call. The resolver contract stays synchronous and
provider-independent. An application may supply a resolver that waits for a person; that
resolver, its timeout and its transport belong to the application layer (ADR-016).

## Out of scope

- Events for retrieval stages inside `search_documents`. Dense, lexical, fusion, reranking and
  selection diagnostics keep arriving with the tool result through `RetrievalStageDiagnostic`
  and `selection_diagnostics`. Live stage events would require a sink through every retriever,
  the reranker and the selector. _Since ADR-017 the selection report is tool diagnostics on
  the trace (`diagnostics.selection`), not part of the tool result._
- Persisting events. The first consumer keeps them in process memory.
- OpenTelemetry export. The event contracts are intended to map onto spans later.
- Run cancellation.

## Alternatives considered

- **Extend the result with a transition list and timings.** Smaller, and it would fill the
  "not yet recorded" gaps, but everything still arrives only at the end. It cannot support a
  live view or interactive approval.
- **Make `run` a generator that yields steps.** Gives a stream without a sink, but changes the
  primary runtime entry point for every caller and makes the Tool Runtime, which is called
  from inside the loop, awkward to include.
- **Adopt OpenTelemetry directly in the runtimes.** Ties core contracts to a telemetry SDK
  and adds a dependency to a core that has none. Spans also do not model "awaiting approval".
- **Derive the timeline in the application from traces.** This is what the workbench does for
  its lifecycle list. It can only reconstruct what traces contain, so state transitions,
  timings and tokens stay missing.

## Consequences

- The Agent and Tool runtime constructors gain an optional parameter. This is a change to
  core interfaces, kept backward compatible.
- Event ordering and content become a tested contract. Failure paths need the same care as
  the success path: every run must end with exactly one run-finished event.
- The event set must stay in step with the transition map in `agent/transitions.py`.
- Sequence numbers allow a consumer to replay recorded events and then continue live, which
  the HTTP event stream in ADR-016 relies on.
- Event volume is small (tens of events per run), so no batching or back-pressure is designed.
