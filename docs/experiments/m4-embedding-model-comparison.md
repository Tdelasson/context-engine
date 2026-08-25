# M4 Embedding Model Comparison

Generated: `2026-08-25T19:08:48.988248+00:00`

## Configuration

- Dataset: `m4-retrieval-benchmark-v1` version `1.0.0`
- Dataset SHA-256: `60886b5dcd84beab03a933d0e88d21b982aa96ec93de5d4274de0b64858959ea`
- Documents / queries: 34 / 20
- K values: 1, 5, 10
- Distance metric: `cosine`
- Platform: `Windows-11-10.0.26200-SP0`
- Python: `3.12.10`

## Results

| Model | Status | Recall@10 | MRR | NDCG@10 | Dimensions | Query mean ms | Docs/sec | Parameter GiB |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bge-m3 | completed | 0.9750 | 0.9167 | 0.9200 | 1024 | 78.152 | 17.584 | 2.115 |
| qwen3-embedding-0.6b | completed | 1.0000 | 0.8625 | 0.8876 | 1024 | 60.865 | 40.884 | 1.110 |
| nomic-embed-text | completed | 1.0000 | 0.8383 | 0.8710 | 768 | 29.724 | 46.751 | 0.509 |
| all-minilm-l6-v2 | completed | 1.0000 | 0.9125 | 0.9210 | 384 | 5.143 | 389.875 | 0.085 |

## Default Model Decision

**Status:** `selected_with_hardware_exclusions`

**Selected model:** `all-minilm-l6-v2`

all-minilm-l6-v2 remained in the quality-equivalent shortlist and had the best recorded local efficiency trade-off under the selection policy.

Selection policy: Successively shortlist models within 0.01 of the best NDCG@10, MRR, and Recall@10; then prefer lower parameter footprint and mean query latency.

Hardware exclusion: `qwen3-embedding-8b` was not run on this machine.

## Interpretation

Quality metrics are comparable because every completed model used the same dataset, relevance judgments, cosine search, and K values. Latency and memory figures describe only the recorded local environment and are not production capacity guarantees.
