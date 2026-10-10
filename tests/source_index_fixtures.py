"""Controlled source lifecycle fixtures with real chunking and injected storage faults."""

from collections.abc import Sequence

from context_engine.knowledge.chunking import ChunkingConfig, StructureAwareChunker
from context_engine.knowledge.ingestion import (
    INDEX_VERSION,
    SourceIngestionCoordinator,
    indexing_configuration_id,
)
from context_engine.retrieval import (
    Document,
    Embedding,
    MetadataFilter,
    SearchResult,
    VectorStoreCollectionConfig,
    VectorStoreRecord,
)
from context_engine.retrieval.source_store import (
    SourceIndexPhase,
    SourceIndexState,
    SourceIndexUnavailableError,
)


class CharacterCounter:
    model_id = "fixture-embedding"
    tokenizer_id = "unicode-characters-v1"
    max_input_tokens = 256

    def count_tokens(self, text: str, *, add_special_tokens: bool = True) -> int:
        return len(text) + (2 if add_special_tokens else 0)


class FixtureEmbeddingProvider:
    model_id = "fixture-embedding"
    dimensions = 2

    def __init__(self) -> None:
        self.calls = 0
        self.fail = False

    def embed_documents(self, documents: Sequence[Document]) -> tuple[Embedding, ...]:
        self.calls += 1
        if self.fail:
            raise RuntimeError("injected embedding failure")
        return tuple(
            Embedding.from_sequence(vector=(1, len(doc.content)), model_id=self.model_id)
            for doc in documents
        )

    def embed_query(self, query: str) -> Embedding:
        return Embedding.from_sequence(vector=(1, len(query)), model_id=self.model_id)


class MemorySourceStore:
    """State survives coordinator restarts; faults model writes with lost acknowledgments."""

    def __init__(self, chunker: StructureAwareChunker) -> None:
        self.collection_config = VectorStoreCollectionConfig(
            "fixture-m5",
            "fixture-embedding",
            2,
            index_version=INDEX_VERSION,
            index_configuration_id=indexing_configuration_id(
                chunker, embedding_identity="fixture-v1"
            ),
        )
        self.records: dict[str, VectorStoreRecord] = {}
        self.states: dict[str, SourceIndexState] = {}
        self.upsert_batches: list[tuple[str, ...]] = []
        self.delete_calls: list[tuple[str, ...]] = []
        self.fail_on: dict[str, int] = {}
        self.fail_before_save = False

    def _fault(self, operation: str) -> None:
        count = self.fail_on.get(operation, 0)
        if count:
            self.fail_on[operation] = count - 1
            if count == 1:
                raise RuntimeError(f"injected {operation} failure")

    def list_source_states(self) -> tuple[SourceIndexState, ...]:
        self._fault("read")
        return tuple(self.states[key] for key in sorted(self.states))

    def save_source_state(self, state: SourceIndexState) -> None:
        if self.fail_before_save:
            self._fault("save")
        self.states[state.source_id] = state
        if not self.fail_before_save:
            self._fault("save")

    def upsert(self, records: Sequence[VectorStoreRecord]) -> None:
        self.upsert_batches.append(tuple(record.document.document_id for record in records))
        for record in records:
            self.records[record.document.document_id] = record
            self._fault("upsert")

    def delete(self, document_ids: Sequence[str]) -> None:
        self.delete_calls.append(tuple(document_ids))
        for document_id in document_ids:
            self.records.pop(document_id, None)
            self._fault("delete")

    def search(
        self,
        query_embedding: Embedding,
        *,
        top_k: int = 5,
        metadata_filter: MetadataFilter | None = None,
    ) -> tuple[SearchResult, ...]:
        if any(state.phase is not SourceIndexPhase.ACTIVE for state in self.states.values()):
            raise SourceIndexUnavailableError("pending source operation")
        matches = [
            record
            for record in self.records.values()
            if metadata_filter is None
            or all(
                record.document.metadata_as_mapping().get(key) == value
                for key, value in metadata_filter.equals
            )
        ]
        return tuple(SearchResult(record.document, 1.0) for record in matches[:top_k])


def fixture_chunker(*, limit: int = 48, overlap: int = 4) -> StructureAwareChunker:
    return StructureAwareChunker(
        ChunkingConfig("fixture-embedding", limit, overlap), CharacterCounter()
    )


def coordinator(
    store: MemorySourceStore,
    provider: FixtureEmbeddingProvider | None = None,
    chunker: StructureAwareChunker | None = None,
) -> SourceIngestionCoordinator:
    return SourceIngestionCoordinator(
        chunker=chunker or fixture_chunker(),
        embedding_provider=provider or FixtureEmbeddingProvider(),
        vector_store=store,
        embedding_identity="fixture-v1",
    )
