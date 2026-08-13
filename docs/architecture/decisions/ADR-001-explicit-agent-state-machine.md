# ADR-001: Explicit Agent State Machine

- **Status:** Accepted
- **Date:** 2026-08-13
- **Decision Type:** Architecture
- **Related Milestone:** M2 — Agent Runtime

## Context

Context Engine requires agent execution to be deterministic, controllable,
testable, and observable.

An agent execution consists of multiple distinct phases, including context
processing, model reasoning, action proposal, runtime validation, tool
execution, and response generation.

If execution state is represented implicitly through control flow, model
output, or prompts, it becomes difficult to:

- validate which transitions are allowed
- prevent invalid execution paths
- reason about agent behavior
- test execution deterministically
- observe and debug agent executions
- enforce runtime safety boundaries

The project therefore needs an explicit representation of agent execution
state.

## Decision

Context Engine will use an explicit state machine for agent execution.

The runtime will represent execution using a typed
`AgentExecutionState` containing an explicit `AgentExecutionStatus`.

The initial lifecycle states are:

```text
START
  ↓
CONTEXT
  ↓
THINK
  ↓
ACTION_PROPOSED
  ↓
RUNTIME_VALIDATE
  ↓
TOOL_CALL ─────┐
  ↓            │
THINK ←────────┘
  ↓
RESPOND
  ↓
COMPLETED
```


Execution may also terminate in:

FAILED

The allowed transitions are defined explicitly by the runtime rather than
being inferred dynamically.

The state object is immutable. State changes produce a new state rather than
mutating the existing state.

The AgentRuntime owns execution state and is responsible for applying
validated transitions.

Invalid transitions must be rejected explicitly.

Terminal states (COMPLETED and FAILED) cannot transition to another state.

## Rationale

An explicit state machine provides a clear boundary between model reasoning
and runtime control.

The model may influence what the agent wants to do, but it does not control
the lifecycle of the runtime itself.

This supports the project's core principle:

LLMs should propose actions, not directly control execution.

It also provides a foundation for deterministic tool execution, policy
enforcement, observability, testing, and future execution tracing.

Keeping the state machine runtime-owned also prevents application-level
components or model output from silently introducing new execution states or
bypassing validation.

## Alternatives Considered
### Implicit state through control flow

The runtime could represent states implicitly through functions, loops, and
conditional branches.

Rejected because:

allowed execution paths are less explicit
transition validation becomes difficult
testing individual transitions is harder
execution state is harder to observe and serialize

### Model-controlled execution state

The LLM could determine the next execution state directly.

Rejected because:

model output is probabilistic
invalid execution paths could be proposed
runtime safety boundaries become weaker
critical control logic would reside in model behavior or prompts

### Mutable state object

The runtime could mutate a single state object during execution.

Rejected because:

previous states cannot be safely retained
state changes become harder to reason about
accidental mutation becomes possible
deterministic execution tracing becomes more difficult

## Consequences
### Positive
Agent lifecycle is explicit and inspectable.
Invalid transitions can be rejected centrally.
Runtime behavior is easier to test.
State can be logged and traced.
The model/runtime boundary is clearer.
Future persistence or replay of execution state is easier.
The architecture provides a foundation for controlled tool execution.


### Negative
The runtime must explicitly define and maintain valid transitions.
Adding new execution phases requires an architectural decision and
corresponding tests.
The state machine introduces some additional structure compared with a
simple execution loop.

## Implementation
The current implementation consists of:

AgentExecutionStatus
AgentExecutionState
ALLOWED_TRANSITIONS
can_transition()
transition_agent_state()
AgentRuntime

The implementation is intentionally provider-independent.

Model providers, tools, and applications must not directly modify runtime
state.

## Related Documentation
AGENTS.md
docs/product/roadmap.md
docs/architecture/overview.md