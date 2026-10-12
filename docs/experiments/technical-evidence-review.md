# Evidence review and corrected benchmark results

Reviewed on 2026-10-12 at the user's request. This is **AI self-review by Codex**,
which authored the initial annotations. All 136 current-workload questions were
reviewed: 124 main questions and 12 separate published-PDF questions. Independent
human review is not claimed; its approval fields remain unchanged and pending.

## What was checked and changed

The review checked question meaning, corpus-relative answerability, required facts,
labelled source text plus surrounding context, API/revision identity and each
explicit supporting alternative. Canonical source bytes/extraction hashes were
validated again. Existing source/topic groups and split assignments were checked
for consistency, without reshuffling questions after looking at held-out results.

The machine-readable [review ledger](../../benchmarks/data/retrieval/evidence-review-2026-10-12.json)
records all decisions. 110 main records and four PDF records were updated; 22 were
retained. Update counts include API identity, clearer reference wording and evidence
scope improvements, rather than counting every update as a wrong original answer.

| Finding | Correction |
| --- | --- |
| API paragraphs often omitted which function/class they described | Added a short identifying declaration span alongside behaviour; applied to the 96 API questions and their 12 compound questions |
| `csv.reader` described its input but not returned rows | Added lists-of-strings behaviour and the QUOTE_NONNUMERIC exception |
| `sqlite3.connect` labelled opening a connection, not the returned type | Added Connection return-type evidence and a complete tutorial alternative |
| `PurePath` described flavour selection, not when to choose pure paths | Added the no-filesystem/OS-access use case |
| `shutil.copy` labelled destination handling, not metadata preservation | Replaced it with permission-mode versus other-metadata behaviour |
| `mkstemp` labelled secure creation, not deletion responsibility | Labelled the caller's responsibility to remove the file |
| `deque` labelled construction, not its optimization | Labelled approximately O(1) appends/pops at either end |
| `Decimal` labelled construction without supported value types | Added the explicit integer/string/tuple/float/Decimal list |
| Median, open modes and partial argument parsing were incompletely described | Added the even-count condition, supported bz2/lzma modes and the parse_known_args return contract |
| Some labels required irrelevant options, examples or policy text | Restricted them to the answer-bearing statements and necessary qualifications; reference facts now answer the actual question |
| Handout alternatives did not identify named fnmatch APIs | Removed those alternatives for named-API questions; retained the valid handout-only behaviour question |
| Additional complete supporting passages were available | Added the json.dumps worked example, sqlite connection tutorial and arithmetic-mean definition |
| Revision-2 retry alternatives lacked revision identity | Added revision identity to both independently sufficient alternatives |
| PDF count question pointed to a str-exponentiation error | Replaced it with the NoneType/integer comparison error and default=0 explanation; removed the incidental count-action definition from required facts |
| PDF installation facts omitted concrete commands/output | Included version-pinning syntax, the requirements install command and the freeze output-format example |

Unsupported questions remain unsupported **relative to this supplied corpus**.
They ask for private organizational facts, credentials or telemetry absent from
these public documents and fictional stress sources. This does not establish that
an answer is unavailable in the outside world. Their simplicity remains a limitation.

## Current results after regrading

No documents, questions, embedding outputs, rankings, selected passage IDs, rendered
output or token counts changed. Replay verified the original selected IDs and exact
complete-output counts across all five retrieval artifacts. Selection policies were
frozen at their original development choices, without retuning on corrected labels.
The original v1 manifests and all v1 results are preserved.

Main Qdrant held-out evidence recall still uses 55 supported questions over six
source/topic groups; six unsupported questions have no recall score. Recall is mean
complete-required-fact coverage, not generated-answer accuracy.

| Path, fixed 128/16 MiniLM-L6 | Original v1 recall | Corrected v2 recall | V2 all-required questions | Exploratory v2 recall 95% interval |
| --- | ---: | ---: | ---: | --- |
| Dense | 39.1% | 39.1% | 38.2% | 31.8–45.4% |
| Lexical | 53.6% | 51.8% | 47.3% | 43.0–61.1% |
| Hybrid | 57.3% | 55.5% | 52.7% | 41.1–70.9% |
| Reranked hybrid | 64.5% | 64.5% | 61.8% | 49.1–80.6% |

Unchanged aggregates do not mean the review was irrelevant: individual held-out
outcomes changed for two dense, three lexical, three hybrid and four reranked
queries. Gains/losses can cancel in the mean. The differences above concern the
answer key; they do not indicate that the underlying retrieval system changed.

The equal-budget diagnostic-omission effects remain +19.1 points for hybrid
(exploratory paired interval 8.9–31.5), +13.6 for reranked (7.3–20.9), +3.6 for
lexical and zero for dense. Overlap suppression still has no main held-out recall
gain; the separate authored overlap mechanism test remains unchanged.

At fixed L6, 96/0 now scores 27.3%, versus 39.1% for 128/16: +11.8 points
(exploratory paired interval 3.6–23.1). Size and overlap both change in this
comparison. At fixed 96/0, L12 now scores 28.2%, versus L6's 27.3%: +0.9 points
(interval -11.8 to +11.1). The original direction of the L12 point estimate does
not survive label repair; there remains insufficient evidence to prefer either
model on this comparison.

The separate six-question held-out published-PDF diagnostic now scores 0.0% for
dense, lexical and hybrid, and 16.7% for reranked (originally 22.2%, 0.0%, 16.7%
and 33.3%). Correct source attribution, error identity and complete multi-part
facts expose additional failures. One held-out PDF topic cannot establish population
uncertainty or general parser quality.

## Answer pilot and interpretation limits

Only evidence/reference fields of the saved answer pilot were regraded. The derived
`technical-v2-answer-evidence-replay.json.gz` preserves all answers, native requests,
provider measurements, tool outputs, failures, the interrupted status and 103 unrun
primary IDs. No new model invocation or answer-quality scoring occurred. Previous
review fields are retained separately and current answer review remains pending.
Both actual search executions still have complete retrieved evidence but incomplete
selected evidence, followed by a provider failure; this is not a reviewed answer
accuracy or a completed deployment evaluation.

This is a post-hoc annotation repair on an already-inspected corpus, **not fresh
held-out validation**. Cross-topic API-template similarity, limited groups, incomplete
enumeration of all possible semantic alternatives, public pretraining overlap,
fictional unsupported cases and parser/layout gaps remain. Repeated self-review by
the same AI author does not establish independent ground truth. No production
default changes or runtime performance measurements were made.

## Reviewable records and reproduction

- [Main v2 review packet](technical-v2-annotation-review.md): every question, concise
  reference fact, exact labelled text, surrounding source context and AI decision.
- [PDF v2 review packet](technical-pdf-v2-annotation-review.md): the same records for
  the separate PDF diagnostic.
- [Main corrected manifest](../../benchmarks/data/retrieval/technical-v1/dataset-v2.json)
  and [PDF corrected manifest](../../benchmarks/data/retrieval/technical-pdf-v1/dataset-v2.json).
- [Historical v1 report](english-technical-rag-evaluation.md), original manifests
  named dataset.json and v1 artifacts remain available for comparison.

The main runner defaults to v2. Reproduce regrading with the pinned tokenizer
from the historical report; no embedding model or running server is needed:

```bash
export PYTHONPATH=src
python -m benchmarks.replay_rag_ablation \
  --artifact benchmarks/results/technical-v1-qdrant-128-16.json.gz \
  --dataset benchmarks/data/retrieval/technical-v1/dataset-v2.json \
  --tokenizer-directory "$QWEN_TOKENIZER" \
  --output /tmp/technical-v2-qdrant-128-16.json.gz
python -m benchmarks.replay_answer_evidence \
  --artifact benchmarks/results/technical-v1-answers-qwen-05b.json.gz \
  --dataset benchmarks/data/retrieval/technical-v1/dataset-v2.json \
  --output /tmp/technical-v2-answer-evidence-replay.json.gz
python -m benchmarks.review_rag_dataset --output /tmp/technical-v2-review.md
```

Apply the same retrieval replay command to the other three main retrieval artifacts;
for the PDF artifact use the PDF v2 manifest. Current results are the separately
named `technical-v2-*` and `technical-pdf-v2-*` files. Tokenizer/corpus identities,
paired comparisons and original choices remain recorded in those artifacts.

Independent review should check the revised propositions and alternative sufficiency
against their shown context. Approve only actually reviewed items and record an
identified reviewer; preserve AI review history. New factual/split changes require a
new dataset version and explicit replay or new retrieval when query text changes.
