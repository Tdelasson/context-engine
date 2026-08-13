# ADR-002: Runtime-Owned Tool Security Boundary

- **Status:** Accepted
- **Date:** 2026-08-13
- **Decision Type:** Architecture
- **Related Milestone:** M3 — Deterministic Tool Use

## Context

Context Engine is designed to support applications that can register and
execute tools.

Tools may eventually perform operations with meaningful side effects, such
as:

- reading or writing files
- making HTTP requests
- modifying external data
- creating playlists
- sending messages
- executing system-level operations

Tools are therefore an important security boundary.

The project also allows applications to register their own tools. This is
necessary for Context Engine to be useful as a platform, but it introduces a
trust boundary: application-provided tools cannot automatically be assumed
to be safe.

The LLM must also not be trusted to decide whether a tool is safe to execute.

The architecture therefore needs a central mechanism that controls whether
a proposed tool action is allowed to execute.

## Decision

Context Engine will enforce a runtime-owned security boundary between agent
tool proposals and tool execution.

The execution flow will be:

```text
LLM
 |
 v
Structured Tool Proposal
 |
 v
Runtime Validation
 |
 v
Policy / Permission Check
 |
 v
Tool Execution
 |
 v
Structured Tool Result
 |
 v
Agent Runtime
```

The Agent Runtime owns the execution boundary.

Application code may register tools, but registered tools do not receive
authority to bypass runtime validation, policy checks, or permission
mechanisms.

The LLM may propose a tool call, but it cannot directly execute a tool.

The runtime must validate the proposed tool call before execution,
including the tool identity and arguments.

Policy and permission checks must occur before a tool capable of external
side effects is executed.

Tools that require human approval must not execute until the required
approval has been obtained.

## Trust Model
Context Engine treats the following components differently:

### Runtime

The runtime is responsible for enforcing execution rules.

It is the authoritative component for:

execution state
transition validation
tool-call validation
policy enforcement
permission checks
execution control

### Model

The model is considered an untrusted decision-making component.

Model output may contain:

invalid tool names
invalid arguments
unsafe requests
malformed structured output
attempts to perform actions outside the permitted scope

Model output must therefore be validated before it can affect external
systems.

### Application

Applications are allowed to register tools.

Application-provided tools are not automatically trusted merely because they
are registered.

The runtime must maintain the ability to control whether and how a tool
executes.

### Tool

A tool is an execution capability.

A tool should not be able to grant itself additional permissions or bypass
the runtime security boundary.

## Tool Registration

Applications may register tools with Context Engine.

A registered tool should expose, at minimum:

a unique identifier
a description
an input schema
an output contract
execution behavior
relevant permission or policy metadata

Registration makes a tool available to the runtime; it does not by itself
grant unrestricted execution authority.

## Validation Boundary

Every model-generated tool proposal must pass through runtime validation
before execution.

At minimum, validation must establish that:

the requested tool exists
the tool is registered
the proposed arguments conform to the tool's schema
the requested operation is permitted by the applicable policy
required permissions or approvals are present

Only after these checks succeed may the runtime invoke the tool.

## Side Effects

Tools capable of external side effects require explicit policy handling.

Examples include:

filesystem writes
external API mutations
sending messages
creating or modifying playlists
system command execution

The runtime must not treat these operations as equivalent to read-only or
pure operations.

The policy layer will determine whether an operation is:

allowed automatically
denied
requires explicit permission
requires human approval

The exact policy model will be defined during M3.


## Rationale

This design preserves the project's core principle:

LLMs should propose actions, not directly execute them.

It also creates a clear security boundary between:

Decision

and

Execution

The model can determine what it wants to accomplish, while the runtime
determines whether the requested action is valid and permitted.

This prevents a malicious or malformed tool proposal from directly causing
an external side effect.

It also prevents an application-provided tool from becoming an uncontrolled
escape hatch around the runtime's security model.

## Alternatives Considered

### Direct model-to-tool execution

The model could directly invoke registered tools.

Rejected because:

model output would have direct access to side effects
validation and authorization would be harder to enforce centrally
malformed or malicious model output could cause unintended actions
observability and auditing would be weaker

### Application-owned security checks

Each application could independently decide whether its tools are safe.

Rejected because:

security behavior would become inconsistent across applications
individual applications could accidentally bypass important controls
the platform would not have a consistent security boundary
common policy enforcement would be duplicated

Applications may still define application-specific policy, but execution
must remain subject to the Context Engine runtime boundary.

### Trust all registered tools

Any tool registered by an application could execute without additional
runtime checks.

Rejected because:

registration does not prove that a tool is safe
malicious or compromised application code could introduce unsafe tools
tools could bypass intended permission boundaries
the runtime would lose meaningful control over execution


### Prompt-based safety rules

The model could be instructed through prompts not to perform unsafe actions.

Rejected because:

prompts are not a reliable security boundary
model behavior is probabilistic
prompt instructions can be misunderstood or ignored
critical security controls should be executable and enforceable in code


## Consequences

### Positive
Tool execution has a clear security boundary.
Model output cannot directly cause side effects.
Application-provided tools remain possible without giving them unrestricted
authority.
Policy enforcement can be centralized.
Human approval can be integrated into the execution flow.
Tool execution can be consistently validated and observed.
Security behavior can be tested independently of individual models.

### Negative
Tool execution requires additional runtime infrastructure.
Tools must provide explicit schemas and metadata.
Policy handling adds complexity to the execution path.
Some operations will require explicit permission or human approval,
increasing latency and reducing automation.

## Security Properties

The architecture should preserve the following invariants:

No LLM output directly invokes a tool.
No tool executes before runtime validation.
No side-effecting tool executes before applicable policy checks.
Required permissions or approvals must exist before execution.
A registered tool cannot bypass the runtime security boundary.
Tool execution should produce an observable execution result.
Security failures must fail explicitly rather than silently degrading into
unrestricted execution.

## Implementation Direction

The detailed implementation will be developed as part of M3 — Deterministic
Tool Use.

Planned components include:

Tool interface
Tool registry
Tool schemas
Argument validation
Tool execution engine
Policy layer
Permission model
Human approval mechanism
Tool execution tracing

The implementation should preserve the security invariants defined in this
ADR.

## Related Documentation
AGENTS.md
docs/product/roadmap.md
docs/architecture/overview.md
docs/architecture/decisions/ADR-001-explicit-agent-state-machine.md
M3 — Deterministic Tool Use