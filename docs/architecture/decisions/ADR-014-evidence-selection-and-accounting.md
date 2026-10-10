# ADR-014: Deterministic evidence selection and explicit JSON accounting

- **Status:** Accepted for optional application composition
- **Date:** 2026-10-10
- **Related issue:** #69

## Context

Ranked retrieval may repeat source material or return more evidence than an answering
request can accommodate. Embedding token counts do not measure an answering tokenizer
or the complete model-visible result. Existing character clipping cuts passages.

## Decision

Add a provider-independent EvidenceSelector after any Retriever/RerankingRetriever.
Applications supply positive token/resource limits and an identified EvidenceTokenCounter.
The selector validates all candidates, walks supplied rank order, deduplicates identities,
suppresses comparable source overlap, and tests whole serialized passages against the
complete evidence JSON budget. Oversized passages are skipped; later candidates can fit.
Result-count and content-character limits remain independent and cause exclusions rather
than passage clipping. Conflicting content/provenance for one identity fails explicitly.
Same text in different sources is retained. Duplicate records may have different native
scores; the first supplied identity owns its rank/score, with later duplicates reported.

Overlap is the fraction of the candidate's union of contributing source spans covered
by the union of previously selected spans of the same source and byte revision. Use
canonical half-open extracted_text character offsets from #59–#62. Different revisions
and pages do not imply overlap. Missing/other-coordinate/incomplete locations are retained
as uncomparable and cannot suppress evidence. Present malformed canonical provenance,
including zero-length/out-of-passage spans, fails. Only selected spans contribute coverage.
Threshold is in (0, 1], or None to disable suppression for the equal-budget baseline.

The renderer and tool serialize identical intact results, including query, result count,
all original metadata/citations and model-visible ranking diagnostics. Re-encode the whole
JSON object for every trial; fragment token counts are not assumed additive. Empty envelope
over budget is an explicit accounting failure. Empty/no-fit outcomes and original ranks,
scores, exclusions, final count, counter/configuration identities are typed runtime reports.
`selection_diagnostics` is a reserved UI/tracing-only field in search_documents output.
AgentRuntime filters it before building model history; Ollama applies the same projection
for direct calls. Other output and all original ranking diagnostics remain model-visible.
The workbench labels selected passages and retains the full selection report in tool results.

The initial optional counter supports qwen2.5:0.5b using the official Qwen2.5-0.5B-Instruct
raw tokenizer pinned to revision 7ae557604adf67be50417f59c2c2f167def9a775. Verify both tokenizer
file hashes and fingerprint the counter method; disable truncation/padding and special
insertion. Only local tokenizer files are loaded, with no weights, inference or automatic
download. Unsupported answering identities or tokenizers fail rather than falling back.
The tokenizers runtime is already supplied by existing benchmark/workbench dependencies.

The hard guarantee is a budget for that tokenizer's encoding of the raw evidence JSON.
Ollama/GGUF tokenizer parity is unverified; its answering-model token estimate is therefore
not a hard provider context guarantee. Ollama's surrounding tool-name/status/call-ID JSON,
chat template, other tool results, history, instructions, tool definitions and answer reserve
are outside this budget. The request owner must enforce those limits. Multiple tool calls
can accumulate evidence. No full-request or M6 conversation-budget subsystem is introduced.

## Alternatives and consequences

Summing passage tokens misses citation/metadata costs and non-additive encoding. Cutting
passages breaks intact evidence; fixed top-K has no token guarantee. Semantic diversity,
source quotas, neighbor expansion and LLM selection remain out of scope. Full-request
budget enforcement belongs to the request owner and needs a separate scoped design.

Complete recounting is simple and correct but costs more CPU for tight budgets. Rich ranking
diagnostics consume real budget and can exclude relevant evidence. This is deliberately
observable rather than silently hidden. Ground-truth labels are evaluation-only; selection
cannot establish answerability or recover missing candidates. Selection stays optional;
existing dense retrieval, tool policy, execution transitions and default answering model
are preserved. Runtime determinism applies only to fixed inputs/configuration/encoding.
