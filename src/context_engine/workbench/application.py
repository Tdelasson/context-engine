"""Application composition for the integrated local agent workbench."""

from __future__ import annotations

from dataclasses import dataclass

from context_engine.agent import AgentRuntime
from context_engine.knowledge.chunking import ChunkingConfig, StructureAwareChunker
from context_engine.knowledge.ingestion import (
    INDEX_VERSION,
    SourceIngestionCoordinator,
    indexing_configuration_id,
)
from context_engine.models import ModelGateway, OllamaModelGateway
from context_engine.retrieval import (
    EmbeddingVectorStoreRetriever,
    LocalEmbeddingProvider,
    LocalEmbeddingProviderConfig,
    QdrantVectorStore,
    Retriever,
    VectorStoreCollectionConfig,
)
from context_engine.tools import AllowAllToolPolicy, ToolRegistry, ToolRuntime
from context_engine.tools.calculator.tool import Calculator
from context_engine.tools.retrieval import SearchDocumentsTool
from context_engine.workbench.config import WorkbenchSettings
from context_engine.workbench.documents import DocumentCatalog, UploadCandidate, UploadLimits
from context_engine.workbench.presentation import (
    WorkbenchRunView,
    build_failed_run_view,
    build_run_view,
)

SYSTEM_PROMPT = """You are the Context Engine workbench assistant.
Use search_documents whenever the answer may be in indexed project or uploaded documents, or 
just seems like a general question more than a calculation. 
Use calculator for arithmetic. Keep the final answer concise and explicitly use tool evidence. 
Dont use the calculator for non-arithmetic questions.
Never claim a tool ran unless its structured result appears in the conversation."""

PROMPT_PRESETS: dict[str, str] = {
    "Project architecture": (
        "How does Context Engine keep model proposals separate from tool execution?"
    ),
    "Project roadmap": "What has been implemented in M4, and what remains future M5 and M6 work?",
    "Calculator": "Use the calculator to compute (144 / 12) + 7.",
    "Uploaded fact": "Search the uploaded documents and answer using the most relevant fact.",
}


@dataclass(frozen=True, slots=True)
class WorkbenchDependencyError(RuntimeError):
    """Labeled live-dependency failure during workbench composition."""

    phase: str
    message: str

    def __str__(self) -> str:
        return f"{self.phase}: {self.message}"


class WorkbenchApplication:
    """Framework-independent facade used by both presets and free-form prompts."""

    def __init__(
        self,
        *,
        settings: WorkbenchSettings,
        document_catalog: DocumentCatalog,
        model_gateway: ModelGateway,
        tool_registry: ToolRegistry,
    ) -> None:
        self.settings = settings
        self.documents = document_catalog
        self._model_gateway = model_gateway
        self._tool_registry = tool_registry

    def prepare(self) -> None:
        """Prepare the idempotent preloaded corpus."""
        self.documents.prepare()

    def ingest_uploads(self, candidates: tuple[UploadCandidate, ...]) -> tuple[str, ...]:
        """Ingest source revisions and return stable source IDs, not passage IDs."""
        return self.documents.ingest_uploads(candidates).source_ids

    def clear_uploads(self) -> tuple[str, ...]:
        """Clear only uploads tracked by this workbench."""
        return self.documents.clear_uploads()

    def run_prompt(self, prompt: str) -> WorkbenchRunView:
        """Execute every prompt through the same live Agent Runtime path."""
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            return build_failed_run_view(
                prompt=prompt,
                phase="prompt_validation",
                message="Prompt must contain non-whitespace characters.",
            )
        tool_runtime = ToolRuntime(self._tool_registry, policy=AllowAllToolPolicy())
        runtime = AgentRuntime(model_gateway=self._model_gateway, tool_runtime=tool_runtime)
        try:
            result = runtime.run(
                model_id=self.settings.model_id,
                user_prompt=normalized_prompt,
                system_prompt=SYSTEM_PROMPT,
                max_output_tokens=self.settings.max_output_tokens,
                temperature=0.0,
                max_model_iterations=self.settings.max_model_iterations,
            )
        except Exception as exc:  # defensive application boundary
            return build_failed_run_view(
                prompt=normalized_prompt,
                phase="agent_runtime",
                message=f"{type(exc).__name__}: {exc}",
            )
        return build_run_view(
            prompt=normalized_prompt,
            result=result,
            tool_results=runtime.tool_results,
            traces=runtime.tool_execution_traces,
        )


def _build_lexical_retriever(vector_store: QdrantVectorStore) -> Retriever:
    from context_engine.retrieval.lexical import LexicalRetriever
    from context_engine.retrieval.qdrant_lexical_index import (
        QdrantBM25ChunkStore,
        QdrantLexicalIndex,
    )

    if not isinstance(vector_store, QdrantBM25ChunkStore):
        raise ValueError("Lexical composition requires a combined chunk store.")
    return LexicalRetriever(lexical_index=QdrantLexicalIndex(chunk_store=vector_store))


def build_live_workbench(settings: WorkbenchSettings | None = None) -> WorkbenchApplication:
    """Compose live local dependencies behind their existing provider-independent contracts."""
    active_settings = settings or WorkbenchSettings.from_environment()
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
        raise WorkbenchDependencyError("embedding", f"{type(exc).__name__}: {exc}") from exc
    try:
        from context_engine.retrieval.qdrant_lexical_index import QdrantBM25ChunkStore

        store_class: type[QdrantVectorStore] | type[QdrantBM25ChunkStore] = QdrantVectorStore
        if active_settings.retrieval_strategy == "lexical":
            store_class = QdrantBM25ChunkStore
        vector_store = store_class(
            VectorStoreCollectionConfig(
                collection_name=(
                    active_settings.lexical_collection_name
                    if active_settings.retrieval_strategy == "lexical"
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
        raise WorkbenchDependencyError("vector_store", f"{type(exc).__name__}: {exc}") from exc

    ingestion = SourceIngestionCoordinator(
        chunker=chunker,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        embedding_identity=embedding_identity,
    )
    retriever: Retriever = (
        _build_lexical_retriever(vector_store)
        if active_settings.retrieval_strategy == "lexical"
        else EmbeddingVectorStoreRetriever(
            embedding_provider=embedding_provider, vector_store=vector_store
        )
    )
    registry = ToolRegistry()
    registry.register(Calculator())
    registry.register(SearchDocumentsTool(retriever))
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
    return WorkbenchApplication(
        settings=active_settings,
        document_catalog=catalog,
        model_gateway=model_gateway,
        tool_registry=registry,
    )
