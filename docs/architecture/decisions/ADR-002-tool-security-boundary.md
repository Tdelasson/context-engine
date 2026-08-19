# ADR-002: Runtime-Owned Tool Security Boundary

- **Status:** Accepted
- **Date:** 2026-08-13
- **Decision Type:** Architecture
- **Related Milestone:** M3 — Deterministic Tool Use

## Context

Context Engine is designed to support applications that can register and execute tools. Tools may eventually perform meaningful side effects such as filesystem writes, HTTP requests, external data mutations, playlist changes, messaging, or system operations.

The LLM must not be trusted to decide whether a proposed action is safe to execute. Application-provided tools must also not be able to bypass a platform-controlled execution boundary.

## Decision

Context Engine enforces a runtime-owned security boundary between model-generated tool proposals and actual tool execution.

The implemented execution flow is:

```text
LLM
 ↓
Structured Tool Proposal
 ↓
Tool Registry Lookup
 ↓
Input Schema Validation
 ↓
Policy Evaluation
 ├── ALLOW ───────────────┐
 ├── DENY                 │
 └── REQUIRE_APPROVAL     │
          ↓              │
     Approval Resolver   │
       ├─ APPROVED ──────┘
       └─ REJECTED
                ↓
          Tool Execution
                ↓
            ToolResult
                ↓
        ToolExecutionTrace
                ↓
               Agent
```

The Agent Runtime and Tool Runtime own this boundary. A model can propose a tool call, but it cannot execute the tool, bypass validation, override policy, or approve its own request.

## Trust Model

### Runtime

The runtime is authoritative for execution state, transition validation, tool-call validation, policy enforcement, approval handling, and execution control.

### Model

The model is an untrusted decision-making component. Model output may contain invalid tool names, invalid arguments, unsafe requests, or malformed structured data.

### Application

Applications may register tools, but registration does not grant unrestricted execution authority.

### Tool

A tool is an execution capability. It cannot grant itself additional permissions or bypass the runtime security boundary.

## Validation and Authorization Boundary

Every model-generated tool proposal must establish that:

- the requested tool is registered;
- arguments conform to the tool's input schema;
- the policy decision permits execution; and
- any required approval has been obtained.

Only then may the runtime invoke the tool.

The current policy model supports three decisions:

```text
ALLOW
DENY
REQUIRE_APPROVAL
```

`ALLOW` executes immediately. `DENY` produces a structured failure without executing. `REQUIRE_APPROVAL` invokes the configured provider-independent approval resolver; the tool executes only after `APPROVED`.

## Human Approval

Human approval is deliberately modeled as a runtime abstraction rather than a UI concern.

The current implementation provides a synchronous `ToolApprovalResolver` that receives the proposed invocation and policy evaluation and returns an explicit `APPROVED` or `REJECTED` decision.

If approval is required but no resolver is configured, the runtime fails explicitly with an approval-required error and does not execute the tool. This is distinct from an explicit rejection: no approval resolution occurred.

The current implementation does not provide interactive UI, asynchronous suspension/resumption, persistent approval requests, or an external approval service. Those concerns belong to a later application/API layer.

## Tool Registration

A registered tool exposes a unique name, description, input schema, and execution behavior. Registration makes a tool available to the runtime but does not bypass validation or policy.

## Side Effects

Side-effecting operations require explicit policy handling. Examples include filesystem writes, external API mutations, messaging, playlist changes, and system commands.

The runtime distinguishes these operations from unrestricted model behavior by requiring every tool call to cross the validation and authorization boundary.

## Observability

Tool execution produces a structured `ToolExecutionTrace`. The trace records the invocation, policy decision, approval decision when applicable, result status, output, errors, and tool-call identity.

This provides deterministic runtime observability without requiring an external telemetry or persistence system.

## Rationale

This design preserves the project's core principle:

> LLMs propose actions; the runtime determines what is allowed to happen.

It creates a clear security boundary between model decision-making and side-effecting execution, while keeping policy and approval independently testable from model behavior.

## Alternatives Considered

### Direct model-to-tool execution

Rejected because model output would have direct access to side effects and central validation and authorization would be weaker.

### Application-owned security checks

Rejected because security behavior would become inconsistent across applications and could be bypassed accidentally.

### Trust all registered tools

Rejected because registration does not prove that a tool is safe and would remove meaningful runtime control.

### Prompt-based safety rules

Rejected because prompts are not an enforceable security boundary for critical execution controls.

## Consequences

### Positive

- Model output cannot directly execute tools.
- Validation and authorization are centralized.
- Human approval can be introduced without coupling the runtime to a UI.
- Tool execution and failures are structured and observable.
- Security behavior can be tested independently of individual models.

### Negative

- Tool execution requires runtime infrastructure and explicit schemas/policies.
- Approval-required actions can add latency and reduce automation.
- A future interactive approval flow will require an application/API layer beyond the current synchronous resolver.

## Security Properties

The implementation preserves these invariants:

- No LLM output directly invokes a tool.
- No tool executes before runtime validation.
- No side-effecting tool executes before policy evaluation.
- A tool requiring approval does not execute before explicit approval.
- A model cannot approve its own tool call.
- A registered tool cannot bypass the runtime security boundary.
- Tool execution produces an observable structured result/trace.
- Security failures fail explicitly rather than silently degrading into unrestricted execution.

## Implementation Status

The M3 implementation is complete. The relevant components are:

- Tool interface
- Tool registry
- Tool input schemas and validation
- Tool execution runtime
- Policy layer
- Human approval resolver
- Structured tool errors
- Tool execution tracing

See `docs/architecture/tool-runtime.md` and `docs/product/roadmap.md` for the current implementation details and milestone status.

## Related Documentation

- `AGENTS.md`
- `docs/product/roadmap.md`
- `docs/product/PROJECT_CONTEXT.md`
- `docs/architecture/overview.md`
- `docs/architecture/tool-runtime.md`
- `docs/architecture/decisions/ADR-001-explicit-agent-state-machine.md`
