# ADR 0002 — Provider-Independent Model Gateway

**Status:** Accepted
**Date:** 2026-08-13

## Context

The Agent Runtime needs to invoke language models without depending on a concrete provider SDK. The architecture requires provider independence and keeps model behavior behind a boundary controlled by the runtime.

## Decision

Introduce a small synchronous `ModelGateway` interface under `context_engine.models` with explicit typed request and response records:

- `ModelRequest` contains the minimum invocation data currently required: prompt and model identifier.
- `ModelResponse` contains provider-independent output: text and model identifier.
- `ModelGatewayError` is the explicit error boundary for gateway failures.
- `ModelGateway.generate()` is the only inference operation in this initial contract.
- `MockModelGateway` provides a deterministic, dependency-free implementation for unit tests.

The gateway does not execute tools, mutate application state, or perform external side effects.

Streaming, structured-output schemas, provider routing, embeddings, reranking, and concrete provider integrations remain separate follow-up concerns unless a later issue requires them.

## Alternatives considered

### Provider SDK directly in the Agent Runtime

Rejected because it couples runtime behavior to a concrete provider and makes deterministic unit testing harder.

### Large universal model interface

Rejected because the current issue only requires the minimum language-model inference boundary. Additional capabilities can be added deliberately when their contracts are understood.

### Async-first gateway

Rejected for now. The architecture explicitly allows asynchronous infrastructure behind a simple request/response interface, so the initial contract remains easy to use and test.

## Consequences

- The Agent Runtime can depend on a stable provider-independent contract.
- Tests can use `MockModelGateway` without network access or provider credentials.
- Concrete providers can be implemented later without changing the runtime contract.
- The current contract intentionally does not yet model structured outputs or streaming; those should be introduced as explicit requirements rather than speculative abstraction.
