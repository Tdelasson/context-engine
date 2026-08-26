# Tool Runtime Architecture

**Status:** Implemented M3 foundation
**Last Updated:** 2026-08-19

The Tool Runtime is the deterministic boundary between model-generated tool proposals and actual tool execution.

The model may propose a tool call, but it does not execute tools directly. The runtime owns lookup, validation, policy, approval, execution, structured results, and execution tracing.

## 1. Execution Flow

```text
ModelResponse
     ↓
ModelDecision(tool_call)
     ↓
ToolInvocation
     ↓
Tool Registry lookup
     ↓
Input schema validation
     ↓
Policy evaluation
     │
     ├── ALLOW ───────────────────┐
     │                            │
     ├── DENY                     │
     │                            │
     └── REQUIRE_APPROVAL         │
              ↓                   │
        ToolApprovalResolver      │
          │           │           │
      APPROVED     REJECTED       │
          │           │           │
          └───────────┴───────────┘
                      ↓
                Tool execution
                      ↓
                  ToolResult
                      ↓
             ToolExecutionTrace
                      ↓
              AgentRuntime / Model
```

Every path remains runtime-controlled.

## 2. Tool Registration

Applications register tools with `ToolRegistry`.

A tool provides at least:

- unique name
- description
- input schema
- execution behavior

Registration makes the tool discoverable and callable by the runtime. It does not grant the tool authority to bypass runtime validation or policy.

## 3. Schema Validation

A `ToolInvocation` is validated against the registered tool's declared input schema before execution.

This establishes a deterministic boundary between model-generated arguments and tool code.

Invalid input produces a structured runtime-owned error and the tool is not executed.

## 4. Policy

The policy layer evaluates a validated invocation before execution.

The current decisions are:

| Decision | Runtime behavior |
| --- | --- |
| `ALLOW` | Execute immediately |
| `DENY` | Do not execute; return structured failure |
| `REQUIRE_APPROVAL` | Resolve approval before execution |

The model does not control the policy decision.

## 5. Human Approval

Approval is represented by the provider-independent `ToolApprovalResolver` abstraction.

The current implementation is synchronous and returns an explicit resolution:

```text
APPROVED
REJECTED
```

The approval request contains the proposed invocation and relevant policy evaluation, so an eventual application/UI layer can present the user with enough information to make a decision.

### Approval invariants

- A tool requiring approval never executes before approval.
- The model cannot approve its own request.
- Explicit rejection prevents execution.
- If approval is required but no resolver exists, execution fails explicitly and the tool is not executed.
- The original tool-call identity and invocation arguments are preserved.

Interactive UI, asynchronous suspension/resumption, persistence, and external approval services are intentionally out of scope for the current runtime foundation.

## 6. Tool Errors

Tool failures are represented as structured `ToolResult` values rather than being silently swallowed.

Examples include:

- unknown tool
- invalid arguments
- policy denial
- approval rejection
- approval required but unresolved
- tool execution failure

This allows the Agent Runtime to feed tool outcomes back into the model loop without coupling the model to Python exceptions or provider-specific behavior.

## 7. Execution Tracing

`ToolExecutionTrace` records the runtime's view of a tool execution attempt.

A trace preserves relevant information such as:

- tool invocation
- tool-call identity
- policy decision
- approval decision when applicable
- result status
- output
- error information

The trace is currently in-memory runtime state. It is not yet a persistent telemetry system or external observability backend.

## 8. Agent Runtime Integration

The Agent Runtime owns the overall model/tool loop:

```text
AgentRuntime
    ↓
ModelGateway.generate()
    ↓
ModelResponse
    ↓
ModelDecision
    ↓
ToolRuntime.execute()
    ↓
ToolResult
    ↓
next model request
```

The model receives registered tool definitions through the provider-independent `ModelRequest.tools` contract. Provider-native tool calls are translated by the Model Gateway into `ModelResponse.tool_call`.

The Tool Runtime then executes the proposal deterministically.

## 9. Retriever-Backed Search Tool

The read-only `search_documents` tool composes the M3 Tool Runtime boundary with the
M4 `Retriever` abstraction:

```text
ModelResponse(tool_call)
        ↓
Tool Runtime
        ↓
registry + schema + policy
        ↓
search_documents
        ↓
Retriever.retrieve(RetrievalRequest)
        ↓
bounded JSON-safe results
        ↓
ToolResult + ToolExecutionTrace
        ↓
next model request
```

The tool accepts one required query string. Result count and content-length limits are
runtime configuration rather than model-controlled arguments. Results preserve
Retriever ordering and contain provider-independent document IDs, scores, bounded
content, and supported JSON-safe metadata.

The tool does not access Qdrant or an embedding provider directly. Retrieval and
serialization failures remain inside the existing structured Tool Runtime error path.
Because this is a read-only tool, applications can use the normal policy boundary to
allow, deny, or require approval without creating a separate execution path.

This integration is deliberately narrower than automatic context assembly or modern
RAG. The model selects the tool call; the runtime does not automatically retrieve or
inject context before model reasoning.

## 10. Provider Independence

The Tool Runtime has no dependency on Ollama or another model provider.

Ollama is currently used only to demonstrate that a real local model can participate in the provider-independent model/tool boundary.

This separation allows deterministic tool behavior to be tested with a fake gateway and allows model providers to change without rewriting the tool execution layer.

## 11. Security Boundary

The core invariant is:

> **LLMs propose actions; the runtime determines what is allowed to happen.**

Therefore:

```text
No model output
      ↓
can directly execute a tool.
```

All tool calls must cross:

```text
Registry
  ↓
Validation
  ↓
Policy
  ↓
Approval when required
  ↓
Execution
```

See `docs/architecture/decisions/ADR-002-tool-security-boundary.md` for the architectural decision behind this boundary.

## 12. Current Scope and Future Work

Implemented in M3:

- tool registry
- typed schemas
- validation
- policy decisions
- human approval abstraction
- structured tool errors
- execution tracing
- model/tool integration

Added as an M3/M4 composition:

- read-only, Retriever-backed `search_documents` tool
- runtime-configured result and content bounds
- deterministic JSON-safe search result serialization
- agent loop propagation through structured `ToolResult`

Not yet implemented:

- interactive approval UI
- asynchronous approval suspension/resumption
- persistent approval requests
- persistent execution traces
- external telemetry backend
- sandboxed execution for untrusted third-party tools
- capability isolation beyond the current policy/runtime boundary

These are later concerns and should not be conflated with the deterministic runtime foundation delivered in M3.
