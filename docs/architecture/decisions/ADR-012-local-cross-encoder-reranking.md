# ADR-012: Optional local cross-encoder reranking

- **Status:** Accepted for optional composition; default adoption pending evaluation
- **Date:** 2026-10-10
- **Related issue:** #68

## Context

Candidate retrieval and evidence ranking have different responsibilities. Cross-encoders
score a query together with each passage and add inference cost. They cannot recover
missing candidates, verify facts, or establish calibrated probabilities. Embedding input
compatibility does not guarantee that a query/passage pair fits a cross-encoder.

## Decision

Use a typed, provider-independent `Reranker` with immutable candidates and explicit
identity/score association. `RerankingRetriever` wraps any existing `Retriever`, forwards
query and metadata filters, requests a fixed application candidate budget, validates one
finite score per unique identity, and orders by descending relevance then upstream rank.
Duplicate/conflicting candidates, missing/unknown/duplicate scores and enabled failures
are explicit errors. No score blending or successful upstream fallback is permitted.

Final count is `min(request.top_k, final_limit, available_candidates)`; the candidate
budget is independent of request top_k and inference batch size. final_limit cannot
exceed candidate_limit. Empty results avoid model scoring. Source content, revision,
metadata and provenance stay intact; source visibility remains upstream's responsibility.

`SearchResult.diagnostics` is an immutable tuple of typed `RetrievalStageDiagnostic`
records. Each record includes native score kind, rank and configuration identity, with
optional model identity, candidate count and duration. Wrappers append original upstream
score/rank and reranker score/rank without changing canonical source metadata. The search
tool serializes diagnostics separately and the workbench shows them. Empty diagnostics
preserve previous serialized output. Native scores have stage-specific semantics.

The local adapter loads Sentence Transformers `CrossEncoder` once, supports single-logit
text classifiers on the torch backend, and returns native logits (higher is better).
It scores exact query and original content with explicitly configured optional prefixes;
there is no stripping, heading insertion, query rewriting or prompt template. Existing
headings inside content are included as ordinary text. The actual tokenizer's pair
encoding includes special tokens and is evaluated without truncation for every candidate
before any batch runs. A configured cap cannot exceed actual tokenizer/model position
limits. Direct classifier inference uses the same untruncated tokenizer encoding and
bypasses `predict` preprocessing, activation and hidden truncation. Batches only pad.

Loading is offline by default and remote code is disabled. Downloads require explicit
setup or `local_files_only=False` outside workbench composition. Configuration identity
binds prefixes, budgets, device, requested revision and a digest of loaded tokenizer,
model configuration and weights. Runtime objects remain inside the adapter. Initialization
time and parameter bytes are observable; neither equals process peak memory.

The initial optional candidate is `cross-encoder/ms-marco-MiniLM-L6-v2`, an Apache-2.0
English MS-MARCO passage-ranking classifier. Its 512-token limit and small parameter
footprint are suitable for an initial CPU experiment. It differs from the embedding
model `sentence-transformers/all-MiniLM-L6-v2`; weights and tasks are independent.
It remains optional pending domain-specific quality and cost evaluation.

## Alternatives and consequences

Using `CrossEncoder.predict` with default preprocessing risks unnoticed truncation.
Window scoring changes evidence semantics and requires a separate evaluated decision.
Cloud reranking adds an external capability and is unnecessary for the local-first scope.
Raw logits preserve native ordering without an unvalidated probability threshold.
Hashing weights adds startup work but prevents mutable model names from masking changes.
CPU/backend scores need not be bitwise identical across machines. Unit fixtures validate
orchestration; opt-in real tests and evidence benchmarks validate actual inference.

## References

- [Model card and Apache-2.0 license](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2)
- [Sentence Transformers cross-encoder score semantics](https://sbert.net/docs/cross_encoder/usage/usage.html)
- [Transformers padding and explicit truncation control](https://huggingface.co/docs/transformers/main/pad_truncation)
