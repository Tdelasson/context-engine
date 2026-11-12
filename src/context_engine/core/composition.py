"""Composition of live local dependencies behind provider-independent contracts."""

from __future__ import annotations

from dataclasses import dataclass

from context_engine.core.application import ContextEngineApplication
from context_engine.core.settings import ApplicationSettings
from context_engine.core.sources import DocumentCatalog, UploadLimits
from context_engine.knowledge.chunking import ChunkingConfig, StructureAwareChunker
from context_engine.knowledge.ingestion import (
    INDEX_VERSION,
    SourceIngestionCoordinator,
    indexing_configuration_id,
)
from context_engine.models import OllamaModelGateway
from context_engine.retrieval import (
    EmbeddingVectorStoreRetriever,
    LocalEmbeddingProvider,
    LocalEmbeddingProviderConfig,
    QdrantVectorStore,
    Retriever,
    VectorStoreCollectionConfig,
)
from context_engine.retrieval.local_cross_encoder import (
    LocalCrossEncoderConfig,
    LocalCrossEncoderReranker,
)
from context_engine.retrieval.reranking import RerankingRetriever, RerankingRetrieverConfig
from context_engine.tools import ToolRegistry
from context_engine.tools.calculator.tool import Calculator
from context_engine.tools.retrieval import SearchDocumentsTool


@dataclass(frozen=True, slots=True)
class ApplicationDependencyError(RuntimeError):
    """Labeled live-dependency failure during application composition."""

    phase: str
    message: str

    def __str__(self) -> str:
        return f"{self.phase}: {self.message}"


def _build_lexical_retriever(vector_store: QdrantVectorStore) -> Retriever:
    from context_engine.retrieval.lexical import LexicalRetriever
    from context_engine.retrieval.qdrant_lexical_index import (
        QdrantBM25ChunkStore,
        QdrantLexicalIndex,
    )

    if not isinstance(vector_store, QdrantBM25ChunkStore):
        raise ValueError("Lexical composition requires a combined chunk store.")
    return LexicalRetriever(lexical_index=QdrantLexicalIndex(chunk_store=vector_store))


def build_live_application(
    settings: ApplicationSettings | None = None,
) -> ContextEngineApplication:
    """Compose live local dependencies behind their existing provider-independent contracts."""
    active_settings = settings or ApplicationSettings.from_environment()
    try:
        embedding_provider = LocalEmbeddingProvider(
            LocalEmbeddingProviderConfig(
                model_id=active_settings.embedding_model_id,
                model_reference=active_settings.embedding_model_reference,
                batch_size=8,
                normalize_embeddings=True,
            )
        )
        chunker = StructureAwareChunker(
            ChunkingConfig(
                model_id=embedding_provider.model_id,
                max_input_tokens=active_settings.chunk_max_input_tokens,
                overlap_tokens=active_settings.chunk_overlap_tokens,
            ),
            embedding_provider.build_token_counter(),
        )
        embedding_identity = embedding_provider.indexing_identity
    except Exception as exc:
        raise ApplicationDependencyError("embedding", f"{type(exc).__name__}: {exc}") from exc
    try:
        from context_engine.retrieval.qdrant_lexical_index import QdrantBM25ChunkStore

        store_class: type[QdrantVectorStore] | type[QdrantBM25ChunkStore] = QdrantVectorStore
        if active_settings.retrieval_strategy in {"lexical", "hybrid"}:
            store_class = QdrantBM25ChunkStore
        vector_store = store_class(
            VectorStoreCollectionConfig(
                collection_name=(
                    active_settings.lexical_collection_name
                    if active_settings.retrieval_strategy in {"lexical", "hybrid"}
                    else active_settings.collection_name
                ),
                embedding_model_id=embedding_provider.model_id,
                dimensions=embedding_provider.dimensions,
                index_version=INDEX_VERSION,
                index_configuration_id=indexing_configuration_id(
                    chunker, embedding_identity=embedding_identity
                ),
            ),
            url=active_settings.qdrant_url,
            timeout_seconds=active_settings.qdrant_timeout_seconds,
        )
    except Exception as exc:
        raise ApplicationDependencyError("vector_store", f"{type(exc).__name__}: {exc}") from exc

    ingestion = SourceIngestionCoordinator(
        chunker=chunker,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        embedding_identity=embedding_identity,
    )
    dense_retriever = EmbeddingVectorStoreRetriever(
        embedding_provider=embedding_provider, vector_store=vector_store
    )
    retriever: Retriever = dense_retriever
    if active_settings.retrieval_strategy in {"lexical", "hybrid"}:
        lexical_retriever = _build_lexical_retriever(vector_store)
        retriever = lexical_retriever
        if active_settings.retrieval_strategy == "hybrid":
            from context_engine.retrieval.hybrid import (
                HybridRetriever,
                HybridRetrieverConfig,
                lifecycle_visibility_reader,
            )

            retriever = HybridRetriever(
                dense_retriever=dense_retriever,
                lexical_retriever=lexical_retriever,
                config=HybridRetrieverConfig(
                    active_settings.hybrid_dense_candidates,
                    active_settings.hybrid_lexical_candidates,
                    active_settings.hybrid_final_results,
                    active_settings.hybrid_smoothing,
                ),
                visibility_reader=lifecycle_visibility_reader(vector_store),
            )
    try:
        retriever = configure_reranking(retriever, active_settings)
    except Exception as exc:
        raise ApplicationDependencyError("reranking", f"{type(exc).__name__}: {exc}") from exc
    registry = ToolRegistry()
    registry.register(Calculator())
    registry.register(configure_evidence_selection(retriever, active_settings))
    catalog = DocumentCatalog(
        ingestion=ingestion,
        upload_limits=UploadLimits(
            max_files=active_settings.max_uploads,
            max_bytes_per_file=active_settings.max_upload_bytes,
            max_pdf_bytes_per_file=active_settings.max_pdf_upload_bytes,
            max_pdf_pages=active_settings.max_pdf_pages,
            max_pdf_text_characters=active_settings.max_pdf_text_characters,
        ),
    )
    model_gateway = OllamaModelGateway(
        base_url=active_settings.ollama_base_url,
        model_name=active_settings.model_id,
        timeout_seconds=active_settings.ollama_timeout_seconds,
    )
    return ContextEngineApplication(
        settings=active_settings,
        document_catalog=catalog,
        model_gateway=model_gateway,
        tool_registry=registry,
    )


def configure_reranking(upstream: Retriever, settings: ApplicationSettings) -> Retriever:
    """Application controls providers and budgets; tool schema remains unchanged."""
    if not settings.reranking_enabled:
        return upstream
    reranker = LocalCrossEncoderReranker(
        LocalCrossEncoderConfig(
            model_reference=settings.reranking_model_reference,
            revision=settings.reranking_revision,
            device=settings.reranking_device,
            batch_size=settings.reranking_batch_size,
            max_input_tokens=settings.reranking_input_tokens,
        )
    )
    return RerankingRetriever(
        upstream,
        reranker,
        config=RerankingRetrieverConfig(
            settings.reranking_candidate_limit, settings.reranking_final_limit
        ),
    )


def configure_evidence_selection(
    retriever: Retriever, settings: ApplicationSettings
) -> SearchDocumentsTool:
    """Compose optional selection after retrieval/reranking without altering runtime policy."""
    if not settings.evidence_selection_enabled:
        return SearchDocumentsTool(retriever)
    from context_engine.models.evidence_counting import QwenEvidenceTokenCounter
    from context_engine.retrieval.evidence_selection import EvidenceSelectionConfig
    from context_engine.tools.retrieval import SearchDocumentsToolConfig

    try:
        counter = QwenEvidenceTokenCounter(
            settings.evidence_tokenizer_directory, model_id=settings.model_id
        )
        return SearchDocumentsTool(
            retriever,
            config=SearchDocumentsToolConfig(
                top_k=settings.evidence_max_results,
                candidate_limit=settings.evidence_candidate_limit,
            ),
            selection_config=EvidenceSelectionConfig(
                settings.evidence_token_budget,
                settings.evidence_max_results,
                overlap_threshold=settings.evidence_overlap_threshold,
            ),
            evidence_counter=counter,
        )
    except Exception as exc:
        raise ApplicationDependencyError("evidence_selection", str(exc)) from exc
