# English technical-workbench evaluation v1

This dataset targets English API documentation search in the current workbench.
It contains 24 original CPython 3.14.0 standard-library documentation files, four
explicitly authored synthetic Markdown stress documents, and a two-page PDF
handout derived from the public fnmatch documentation. Source sizes, bytes and
processed-text coordinates are pinned in dataset.json. Original CPython files are
reStructuredText read as plain text by the current reader: markup remains visible.
They represent a bounded public-document workload, not the user's production corpus.

124 authored questions comprise 96 single-API questions, 12 compound questions,
12 unsupported questions, three revision/distractor questions and one two-page PDF
question. There are 63 development and 61 held-out questions, including six
unsupported in each split. Public queries reference actual docs; Juniper policies
are fictional stress cases and their answers are not public Python facts.

## Attribution and redistribution

Original files are unmodified snapshots from
https://github.com/python/cpython/tree/v3.14.0/Doc/library .
Each source records its exact upstream URL and byte hash. Retain CPYTHON-LICENSE.txt
with the snapshots and derivative PDF. Python documentation is under the terms in
that notice; examples have the additional zero-clause BSD terms stated there.
The fnmatch-handout.pdf is a derivative: fnmatchcase on page 1, filtering on page 2,
with simple authored layout. It is not an authentic complex-layout PDF workload.
Juniper stress files and authored question/annotation data are dedicated to CC0-1.0:
https://creativecommons.org/publicdomain/zero/1.0/ . No private source data is used.

## Annotation and split contract

Each fact has reference text and one or more complete supporting alternatives.
Multiple spans within one alternative are conjunctive; different alternatives are
independently sufficient. Completing pieces of different alternatives does not
establish full support. Unsupported queries have no evidence/recall denominator;
answerability is an expected corpus property, not a retrieval score threshold.

Sources/topics involved in compound or alternative evidence share a connected
split group. Related questions, duplicates and derivative PDF sources stay in that
group. There are only seven development and six held-out independent groups after
pairing modules: 124 questions are not 124 independent topics. Bootstrap intervals
resample those groups, with a warning for fewer than ten. They describe this corpus,
not a population confidence guarantee. Generic API phrasing and compression-module
similarities can still generalize across groups; this is a documented residual
leakage risk for independent annotation review. All source files remain searchable
in both splits; held-out means held-out questions/labels, not hidden documents.

The split was fixed before the first comparison and is separate from the #64
four-source suite. Use development for tuning. The bounded #78 plan evaluates only
its frozen development choice plus predeclared paired baselines on held-out queries.
Any later tuning after inspection needs a new held-out revision.

## Review and versioning

Annotations were authored by Codex and checked against pinned source text, but are
**drafts awaiting independent review**. Mechanical coordinate/hash checks do not
establish semantic correctness. The concrete [review packet](../../../../docs/experiments/technical-v1-annotation-review.md)
contains every query, reference fact and alternative location.
Generate it with `python -m benchmarks.review_rag_dataset --output /path/review.md`.

An independent reviewer checks the full question, reference fact, source context,
all alternative spans, answerability, category and split grouping. Record notes and
disagreements under the query's review entry; resolve disagreements before setting
status=approved and reviewer to an identity distinct from the author. Do not approve
unseen items. All-corpus approval and release readiness must be assessed separately
from selective review. Change dataset ID/version and regenerate hashes/offsets when
source extraction, facts or splits change; retain previous results with their
original manifest SHA. Re-run or replay against the new manifest explicitly.

Remaining gaps include OCR/complex layouts, multilingual and user-private documents,
long narrative troubleshooting tasks, ambiguous questions, adversarial source text,
and genuinely unsupported public API questions. Unsupported cases here deliberately
ask for fictional private organizational facts and are comparatively easy to refuse.
Public docs may overlap a model's pretraining; answer evaluation requires observable
retrieval and supported citations, rather than trusting memorized knowledge.
