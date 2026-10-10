# Source ingestion and lifecycle

`knowledge/ingestion.py` connects processing → exact-token chunking → embedding →
indexing. It keeps inference in `EmbeddingProvider`, persistence in `VectorStore`,
and search behind `search_documents → Retriever → VectorStore`. M4 `Ingestor` remains
available for historical whole-document benchmarks; the workbench uses the M5 coordinator.

## Composition

```python
from context_engine.knowledge.chunking import ChunkingConfig, StructureAwareChunker
from context_engine.knowledge.ingestion import (
    INDEX_VERSION,
    SourceIngestionCoordinator,
    indexing_configuration_id,
)
from context_engine.knowledge.processing import SourceInput, SourceFormat
from context_engine.retrieval import (
    LocalEmbeddingProvider,
    LocalEmbeddingProviderConfig,
    QdrantVectorStore,
    VectorStoreCollectionConfig,
)

provider = LocalEmbeddingProvider(
    LocalEmbeddingProviderConfig(
        model_id="sentence-transformers/all-MiniLM-L6-v2",
        model_reference="sentence-transformers/all-MiniLM-L6-v2",
        normalize_embeddings=True,
    )
)
chunker = StructureAwareChunker(
    ChunkingConfig(provider.model_id, max_input_tokens=128, overlap_tokens=16),
    provider.build_token_counter(),
)
identity = provider.indexing_identity
store = QdrantVectorStore(
    VectorStoreCollectionConfig(
        collection_name="my-m5-index-v1",
        embedding_model_id=provider.model_id,
        dimensions=provider.dimensions,
        index_version=INDEX_VERSION,
        index_configuration_id=indexing_configuration_id(chunker, embedding_identity=identity),
    )
)
ingestion = SourceIngestionCoordinator(
    chunker=chunker,
    embedding_provider=provider,
    vector_store=store,
    embedding_identity=identity,
)
recovery = ingestion.recover()  # explicit startup work; inspect every outcome
outcome = ingestion.ingest(
    SourceInput(
        source_id="project/guide",
        source_name="guide.md",
        source_kind="supplied",
        content=b"# Guide\n\nA useful fact.",
        format=SourceFormat.MARKDOWN,
    )
)
# Later, using the same durable source ID:
# ingestion.delete_source("project/guide")
```

The example's 128/16 settings are conservative operational settings, **not measured
quality defaults**. The chunk benchmark (#64) will compare settings. The provider
exposes the loaded runtime's tokenizer and actual `max_seq_length`; no second model
is downloaded. A cached fingerprint binds loaded weights, tokenizer, preprocessing,
pooling/model configuration, prefixes, and normalization to the effective index identity. Custom embedding runtimes
must supply their compatible exact counter and explicit embedding identity themselves.

## Identity, results, and restart

Caller-assigned source IDs are logical identities, never byte hashes. A source's name
and namespace remain fixed while it is indexed. Its byte SHA-256 identifies a revision.
Different IDs with the same filename remain independent. Workbench IDs hash the exact
filename within separate `preloaded-` and `uploaded-` namespaces. In the collection-wide
upload namespace, the same filename replaces a source even across browser restarts;
multiple independent same-name uploads require separate collections or caller IDs.
Preload filenames include extensions, avoiding stem collisions.

`IngestionOutcome.status` is `created`, `unchanged`, `replaced`, `deleted`, or `failed`.
Outcomes include source ID, chunk IDs/count, previous count, processing diagnostics,
error phase/message, `requires_recovery`, and `recovered`. Repeat unchanged ingestion
avoids embedding and writes; repeat deletion returns unchanged. Processing, chunking,
state-read, embedding count/space errors occur before storage mutation. Application
adapters can supply a validated `ProcessedSource` through `ingest_processed`.

Each chunk persists original text, heading context, revision, source/config identities,
block/page/section locations, overlap spans, token count, and diagnostics. Qdrant also
persists one excluded control point per source with active/proposed revisions and chunk
IDs. `SourceLifecycleStore` exposes typed manifest read/write operations; no Qdrant SDK
objects cross this boundary. `list_sources()` reconstructs the catalog after restart.
Deleted sources leave small active tombstones with no chunks.

## Replacement, failures, and recovery

All new content is processed, chunked, embedded, and compatibility-validated first.
Replacement then acknowledges these operations:

1. Save `staging` with previous and target revisions.
2. Upsert every target chunk.
3. Save `ready`, confirming the complete target is stored.
4. Delete obsolete previous chunk IDs (including shorter replacements).
5. Save `active` with the new revision.

Deletion starts at ready with no target. A failed/ambiguous write reports failure and
recovery required. Search rejects any pending manifest; it also compares all manifest
operation IDs before/after querying and rejects a changed snapshot. Control points
never appear in search. Pending mutations block the entire collection, preserving
explicit failure rather than serving a successful-looking mixed revision.

`recover()` requires no model inference or original bytes. Staging recovery deletes the
possibly partial target and restores the old manifest; a new source becomes an empty
tombstone. Ready recovery repeats obsolete deletion and activates the complete target,
or completes source deletion. Inspect recovery outcomes: rollback returns failed with
`recovered=True`, while an unresolved recovery returns `requires_recovery=True`.
A lost final acknowledgment may leave an already-active operation; recovery then has
nothing to do. Retry ingestion/deletion to determine its final idempotent outcome.

There is **no atomic visibility guarantee or distributed transaction**. Use a local
Qdrant server and one writer process per collection. Coordinators serialize mutations
across sessions in that process. Cross-process writers, direct adapter mutations,
external point deletion, and database loss are outside these recovery guarantees.
A batch is validated in full, but commits per source: a storage failure can leave earlier
sources committed. The workbench retains the structured outcomes and stops the batch.
See [ADR-009](../architecture/decisions/ADR-009-source-index-lifecycle.md).

## Migration and rebuild

The default workbench collection is `context-engine-workbench-m5-v1`; M4's
`context-engine-workbench` is retained. Existing M4 whole-document collections and
incompatible M5 configurations are rejected rather than adopted or mixed.

To rebuild, stop the writer, set `CONTEXT_ENGINE_WORKBENCH_COLLECTION` to a **new**
collection name, choose the desired chunk/model configuration, and restart. Preloads
are reingested automatically; explicitly reupload the original files. The old index
remains intact for rollback. Delete it separately only when it is no longer needed.
Changing token budgets, overlap, tokenizer/weights, prefixes, or normalization requires
this rebuild. There is no silent migration and no original-upload byte archive.

## Verification

Unit tests cover creation, repeat ingestion/deletion, fewer replacement chunks, independent
same-name sources, restart catalogs, provenance, stage failures, partial writes/deletes,
lost acknowledgments, recovery failure, and incompatible configurations. Controlled
workbench/tool tests verify chunk evidence and source-level cleanup without live models.

Run the real adapter checks against an isolated Qdrant instance:

```bash
CONTEXT_ENGINE_RUN_QDRANT_INTEGRATION=1 \
  python -m pytest tests/integration/test_source_ingestion_integration.py -v
```

These tests use deterministic embeddings and unique temporary collections, which they
remove. Real loaded-tokenizer checks share the embedding integration opt-in flag; the
workbench integration additionally exercises real model inference. Tests establish
lifecycle correctness, not retrieval quality; #64 owns the measured dense baseline.
