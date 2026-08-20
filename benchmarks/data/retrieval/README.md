# M4 Retrieval Benchmark Dataset (v1)

This directory contains the fixed, hand-curated retrieval benchmark dataset for M4.

## Files

- `m4-retrieval-dataset-v1.json`: version-controlled benchmark input used across candidate embedding models.

## Dataset Shape

The JSON document uses three explicit benchmark components:

- `documents`: stable `document_id`, natural-language `content`, and structured `metadata`
- `queries`: stable `query_id`, natural-language `text`, and retrieval `intent`
- `relevance_judgments`: deterministic mapping from each `query_id` to `relevant_document_ids`

Conceptually:

```text
BenchmarkDataset
├── documents
├── queries
└── relevance_judgments
```

## Curation Methodology

- Manually authored and manually reviewed in-repo.
- Relevance judgments were assigned by human curation, not by LLM judging.
- Judgments include only documents that directly satisfy query intent; merely related documents are excluded.
- Queries are paraphrased and phrased in natural language to exercise semantic retrieval.
- Includes both single-relevant-document and multi-relevant-document queries.
- Includes similar-but-irrelevant documents to reduce pure keyword-matching shortcuts.

## Scope and Constraints

- Model-independent ground truth only; no vectors, model scores, or model-specific labels.
- Benchmark data is kept separate from runtime/production data under `benchmarks/data/`.
- M4 scope only: no chunking, reranking, hybrid retrieval, or RAG generation in dataset creation.

## Change Policy

This dataset is intended to stay fixed during model comparisons. Any changes should be deliberate,
reviewed, and versioned to preserve benchmark reproducibility.

## Known Limitations

- Small size by design (inspectability over volume).
- Domain coverage is representative, not exhaustive.
- Relevance remains binary judgments for M4 and does not encode graded preference.
