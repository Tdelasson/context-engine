# ADR-017: Model output and tool diagnostics

- **Status:** Accepted
- **Date:** 2026-11-12
- **Supersedes:** the `selection_diagnostics` clause of ADR-014

## Context

ADR-014 made `selection_diagnostics` a reserved field inside the `search_documents` output.
Before a tool result reached the model, it was removed by `model_visible_tool_output`, which
matched the tool name `"search_documents"` and that key. The rule was split across four
modules, and no interface showed it:

- `tools/retrieval/tool.py` wrote the report into the output mapping.
- `models/tool_serialization.py` matched the tool name and key to remove it.
- `agent/runtime.py` and `models/ollama.py` both applied that filter.

A new tool with runtime-only data would have leaked it to the model unless someone also edited
`models/`. Evidence selection also counts tokens on `render_tool_output`. Ollama built its
tool message with its own `json.dumps`, so the counted text matched the sent text only
because a comment said so.

## Decision

1. **Tool output has two parts.** `Tool.execute` returns either a plain mapping, which is all
   model output, or `ToolOutput(model=..., diagnostics=...)`. `ToolRuntime` normalizes both.
2. **Diagnostics live on the trace only.** `ToolResult.output` holds only the model output, so
   the agent runtime and the gateways cannot send diagnostics to the model.
   `ToolExecutionTrace.diagnostics` keeps them for observability. The HTTP API exposes them as
   `traces[].diagnostics`.
3. **`search_documents` moves its selection report** from `output.selection_diagnostics` to
   `diagnostics["selection"]` on its trace. The frontend reads it from the trace that matches
   the search result's invocation id.
4. **One renderer.** The Ollama gateway renders its tool-message envelope with
   `render_tool_output`, which evidence selection also counts. The counted output text is
   therefore byte-identical to what is sent. Output that JSON cannot represent (NaN,
   infinity) fails with `ModelGatewayRequestError` and is never sent.

`model_visible_tool_output` is deleted.

## Alternatives considered

- **Tool declares hidden output keys** (`hidden_output_keys` on the `Tool` protocol). This
  keeps the trace shape, but model and runtime data stay mixed in one flat mapping, and every
  consumer of the output has to apply the filter.
- **A shared constant for the key name.** This makes the leak visible but leaves it in place.
- **Diagnostics on both `ToolResult` and the trace.** A smaller frontend change, but
  diagnostics would sit on the record the model message is built from.
- **A renderer method on the `ModelGateway` port.** Each provider would count exactly its own
  bytes, but every gateway adapter would need a new method. There is only one gateway today.

## Consequences

- The visibility rule is part of the `Tool` interface. Adding a tool with diagnostics needs no
  change in `models/` or `agent/`.
- The HTTP trace schema gains a required, nullable `diagnostics` field. `tool_results[].output`
  no longer contains `selection_diagnostics`. Runs are only held in memory, so no migration is
  needed.
- The package-level `retrieval` ↔ `models` import cycle (`evidence_selection` imports
  `tool_serialization`, `evidence_counting` imports `evidence_selection`) is unchanged and out
  of scope.
