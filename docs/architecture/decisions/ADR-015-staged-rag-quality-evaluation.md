# ADR-015: Staged RAG quality evaluation and explicit human review

- Status: Accepted for opt-in evaluation tooling
- Date: 2026-10-10
- Related issues: #77, #78, #79; performance/load work remains #80

## Context

The #64/#69 diagnostic suite detects failures but has four sources and only four
supported held-out questions. Evidence coverage alone cannot establish answer
correctness. Ranking and serialized diagnostic overhead confound comparisons.

## Decision

Keep the original suite unchanged. Add a versioned English technical-document
workload with evaluation-only answer requirements and independently sufficient
support alternatives. One alternative can require a union of multiple spans;
partial support from different alternatives cannot be combined. Validate original
source/extracted-text hashes, locations, answerability, identities and connected
source/topic split groups. Separate authored drafts from independently approved
annotations. Never auto-approve labels or publish unreviewed answer accuracy.

Use one opt-in ingestion/retrieval setup behind existing domain contracts. Freeze
bounded candidates once per path/query, and replay equal-budget selection and
rendering choices on those exact records. Record candidates@20, ranked@5 and selected
evidence coverage, exclusions, all-required outcomes and complete JSON token costs.
Marginal token attribution recounts nested complete envelopes in a specified order;
fragment counts are not presumed additive. Tune using development only, then record
the frozen choice and predeclared paired baselines on held-out queries.

SearchDocumentsToolConfig can explicitly omit upstream ranking diagnostics from
model-visible evidence. It preserves intact content, scores, all canonical metadata
and provenance. The default includes diagnostics. Selection configuration identity
includes the alternate rendering identity; UI/tracing-only selection reports retain
selected ranking diagnostics. This is a diagnostic-overhead ablation, not a claim
that the remaining citation envelope is the smallest possible representation.

Observe end-to-end answers through the real AgentRuntime, ToolRuntime and ModelGateway.
A benchmark gateway wrapper records typed requests/responses/errors and explicitly
prepends predeclared user/assistant history supplied by the request owner. It does
not fabricate tool calls or past tool-result claims. The normal runtime accumulates
actual new tool calls/results, including repeated calls, under its existing policy.
The Ollama evaluation adapter records actual serialized provider payloads, model
identity/template/configuration and reported usage. Raw payload tokenization is a
proxy, not the provider's chat-template count. Full context fit and hidden truncation
remain unverified unless independently established; no new global context subsystem
or hard provider-context guarantee is introduced.
Other answering models require an explicit tokenizer-proxy declaration when using
the supplied Qwen counter. The benchmark gives that proxy its own target identity
and method; it rejects mismatches otherwise. It does not weaken the production
Qwen counter's pinned-byte compatibility checks or assert native target token parity.

Score answers with an identified human rubric for required facts, factual correctness,
citation support, unsupported claims and abstention. Mechanical citation-ID validation
is supplementary. Keep failures and pending reviews visible; do not calculate a
reviewed-only accuracy that drops harder pending cases. Repeated generation is saved
but does not increase independent quality denominators. Bootstrap source/topic groups
and paired differences, with small-group warnings and conditional-corpus limits.

## Alternatives and consequences

Replacing diagnostic tests would lose fast regression coverage. A broad parameter
sweep would not isolate causes. Automatic judge-only scoring would create an
unverified ground truth. Cloud experiment infrastructure is unnecessary here.

Local JSON/gzip artifacts preserve raw candidates, choices, outputs and traces;
deterministic compression reduces repeated evidence storage. Human label/answer
review is an explicit remaining evaluation step, not a loader or test-suite result.
The dataset is a bounded public-document workload and includes synthetic stress
cases. It does not certify private production documents or choose defaults by itself.
No latency, memory, capacity or load benchmark is added; those measurements remain #80.

Evidence-label repairs are published as new manifests while preserving the original
labels/artifacts. AI self-review records are separate from independent approval.
Replay may regrade unchanged candidates and delivered passages, verifying identities
and counts; it must not retune against the already-inspected held-out set or silently
carry answer-review approval across changed reference requirements.
