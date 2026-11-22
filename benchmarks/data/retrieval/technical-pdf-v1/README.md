# Published technical PDF diagnostic v1

The original `dataset.json` and v1 artifacts are preserved. `dataset-v2.json` records
the 2026-10-12 AI evidence-review corrections without changing PDF bytes, extraction,
questions or splits. For v2 runs, explicitly supply that manifest. AI self-review
is recorded separately from the still-pending independent review. See the
[current review packet](../../../../docs/experiments/technical-pdf-v2-annotation-review.md)
and [review findings](../../../../docs/experiments/technical-evidence-review.md).

This separate suite contains 12 draft questions over two licensed, published Python
3.11.0 PDFs: the tutorial's virtual-environment chapter (original PDF pages 101–103)
and the complete 12-page argparse tutorial. Original page objects, fonts, diagrams
and code-box layout are preserved; this is not a newly typeset text fixture.

The manifest pins the official archive URL, archive/member SHA-256, one-based
original page indices, redistributed PDF bytes and canonical extracted-text hash.
The archive is `python-3.11.0-docs-pdf-a4.zip` from
<https://docs.python.org/3.11/archives/>. `CPYTHON-LICENSE.txt` is from the v3.11.0
source tag. PDF page extraction used pypdf 6.20.0; inspect the recorded byte hashes
when reproducing the corpus, rather than assuming regenerated PDF bytes match.

The virtual-environment topic is development (six questions); argparse is held out
(six questions). Each split has just one independent topic. These are extraction
diagnostics with exploratory uncertainty, not a second population-quality sample.
Do not pool scores with technical-v1: its argparse topic is already held out and
the two suites have different source distributions. All 12 questions are supported;
unsupported cases belong to the primary suite. Coverage includes exact API,
paraphrase and multi-span requirements with concrete published-page locations.

Extraction retains page headers/footers and sometimes joins words or separates
code tokens differently from the visible page. Evidence labels refer to the
canonical extracted representation. Page rendering was visually checked separately;
successful extraction does not establish faithful layout understanding. No OCR,
scans, complex tables or multi-column guarantee is introduced.

Use the shared loader, ablation runner and annotation workflow with
`--dataset benchmarks/data/retrieval/technical-pdf-v1/dataset.json`. See the
[review packet](../../../../docs/experiments/technical-pdf-v1-annotation-review.md)
and primary dataset guide for independent approval, disagreement resolution and
versioning. All labels remain authored drafts pending independent human review.
