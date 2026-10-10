# Reranking API

`context_engine.retrieval.reranking` defines `Reranker`, `RerankingCandidate`,
`RerankingRequest`, `RerankingScore`, `RerankingRetriever` and its bounded configuration.
Candidates contain original `Document` evidence. Score outputs reference document IDs;
the provider cannot replace text or metadata. Scores must be finite and higher-is-better.

```python
from context_engine.retrieval.local_cross_encoder import (
    LocalCrossEncoderConfig,
    LocalCrossEncoderReranker,
)
from context_engine.retrieval.reranking import RerankingRetriever, RerankingRetrieverConfig

reranker = LocalCrossEncoderReranker(
    LocalCrossEncoderConfig(
        model_reference="/absolute/path/to/prepared/snapshot",
        device="cpu",
        batch_size=8,
        max_input_tokens=512,
    )
)
# upstream is any injected Retriever, including the existing dense retriever.
retriever = RerankingRetriever(
    upstream, reranker, config=RerankingRetrieverConfig(candidate_limit=20, final_limit=5)
)
```

The original query and metadata filter are forwarded with candidate_limit as upstream
`top_k`. Final count cannot exceed request.top_k or final_limit. Candidate count, model
batch size and final result count have separate application controls. Upstream overflow,
duplicate IDs (including conflicting records), malformed score association and enabled
inference failures raise typed `RerankerError` subclasses, which inherit `RetrieverError`.
The normal tool/runtime boundary reports structured failures; no silent fallback occurs.

The local adapter validates complete exact query/passage pairs including configured
prefixes and model special tokens. Original content is preserved. Oversize pairs raise
`RerankerInputCompatibilityError` naming the candidate, observed count and cap before
any scoring batch executes. Queries/passages are never shortened; embedding budgets
are unrelated. Unsupported classifiers, invalid caps, dependency/load errors and inference
errors are explicit. Native logits are not calibrated probabilities or an abstention rule.

SearchResult carries typed stage diagnostics separate from source metadata. Existing
stages are preserved; the wrapper appends upstream score/rank and reranking score/rank,
model/configuration identity, count and shared request scoring duration. Duration includes
adapter tokenization/validation and all scoring batches, excludes upstream retrieval and
model construction, and must not be summed once per returned result.

The adapter exposes `initialization_seconds` and `model_parameter_bytes`. These exclude
process peak allocations and should be labeled accordingly in measurements. Runtime
identity includes tokenizer/config/weights digest; optional revision is forwarded to loading.

See [ADR-012](../architecture/decisions/ADR-012-local-cross-encoder-reranking.md).
