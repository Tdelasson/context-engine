# RAG answer review rubric v1

The answer runner outputs a review packet in each raw query record. Reference facts
and labels are evaluation-only and never included in model requests. They remain
provisional until the dataset's independent annotation review is complete.

For each primary answer, an identified independent human reviewer checks the full
question, expected answerability, actual retrieved/selected evidence, citations,
provider errors and generated answer. Check claims against source context, not just
word overlap. Answer variation in repeat records can be reviewed separately; do not
count repeats as new questions.

Set `review.rubric_version` to `rag-answer-rubric-v1` and record:

- `requirements`: a boolean for every requirement ID; true means the answer
  correctly conveys its required fact, including qualifiers, without contradiction.
- `factual_correctness`: true only if the factual statements are correct in context.
- `unsupported_claims`: true if any factual claim lacks support in the supplied
  evidence, even if it happens to be true outside the corpus.
- `citation_support`: true only if cited passages actually support the associated
  claims and citations cover every factual claim that needs support. Existing IDs
  alone do not establish this. For an abstention with no factual claims, true is
  acceptable; supported-answer success additionally requires at least one citation.
- `abstained`: true if the answer explicitly declines the requested factual answer
  because the documents lack support. Partial supported answers must identify missing
  parts; a false claim of complete support is a failure.
- `notes`: explain missing facts, wrong qualifiers, unsupported/citation claims,
  ambiguous cases, policy errors and review disagreements.

Resolve disagreements before changing `status` from pending to approved and adding
`reviewer`. Failed/empty/truncated runs still require review and remain in the task
success denominator. Do not approve unseen records. Pending records prevent an
aggregate accuracy for that split; selective review cannot silently exclude failures.

For answerable queries, task success requires a responded outcome, a successful
observable tool path, every required fact, correct supported claims, valid supported
citations and no erroneous abstention. For unsupported queries it requires an
observable successful search followed by abstention without unsupported claims.
Report correctness, fact completeness, citation support, unsupported claims and
incorrect refusals separately. An answer failure is not an appropriate abstention.

Edit a copy of the raw artifact's review fields, retain all traces/facts, then run:

```bash
python -m benchmarks.benchmark_rag_answers \
  --review-artifact /path/reviewed-answers.json \
  --output /path/scored-answers.json.gz
```

An automated judge is not implemented. This rubric and review workflow do not imply
that human review has already occurred. Model-visible instructions encourage search,
citations and abstention, but only execution traces and review establish what happened.
