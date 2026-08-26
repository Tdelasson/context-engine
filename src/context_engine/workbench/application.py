"""Application composition for the integrated local agent workbench."""

from __future__ import annotations

from dataclasses import dataclass

from context_engine.agent import AgentRuntime
from context_engine.models import ModelGateway, OllamaModelGateway
from context_engine.retrieval import (
    EmbeddingVectorStoreRetriever,
    Ingestor,
    LocalEmbeddingProvider,
    LocalEmbeddingProviderConfig,
    QdrantVectorStore,
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
Use search_documents when the answer may be in indexed project or uploaded documents.
Use calculator for arithmetic. Keep the final answer concise and explicitly use tool evidence.
Never claim a tool ran unless its structured result appears in the conversation."""

PROMPT_PRESETS: dict[str, str] = {
    "Project architecture": (
        "How does Context Engine keep model proposals separate from tool execution?"
    ),
    "Project roadmap": "What is implemented in M4, and what remains future M5/M6 work?",
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
        """Ingest validated uploads through the existing Document/Ingestor path."""
        return self.documents.ingest_uploads(candidates).document_ids

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
    except Exception as exc:
        raise WorkbenchDependencyError("embedding", f"{type(exc).__name__}: {exc}") from exc
    try:
        vector_store = QdrantVectorStore(
            VectorStoreCollectionConfig(
                collection_name=active_settings.collection_name,
                embedding_model_id=embedding_provider.model_id,
                dimensions=embedding_provider.dimensions,
            ),
            url=active_settings.qdrant_url,
            timeout_seconds=active_settings.qdrant_timeout_seconds,
        )
    except Exception as exc:
        raise WorkbenchDependencyError("vector_store", f"{type(exc).__name__}: {exc}") from exc

    ingestor = Ingestor(embedding_provider=embedding_provider, vector_store=vector_store)
    retriever = EmbeddingVectorStoreRetriever(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )
    registry = ToolRegistry()
    registry.register(Calculator())
    registry.register(SearchDocumentsTool(retriever))
    catalog = DocumentCatalog(
        ingestor=ingestor,
        vector_store=vector_store,
        upload_limits=UploadLimits(
            max_files=active_settings.max_uploads,
            max_bytes_per_file=active_settings.max_upload_bytes,
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
