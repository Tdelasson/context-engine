"""Real MiniLM/Qdrant workbench composition with controlled model proposals."""

import os
from dataclasses import replace
from typing import Any
from uuid import uuid4

import pytest

from context_engine.core import composition as composition_module
from context_engine.core.runs import RunStatus
from context_engine.core.settings import ApplicationSettings
from context_engine.core.sources import UploadCandidate
from context_engine.models import ModelFinishReason, ModelRequest, ModelResponse, ModelToolCall
from context_engine.retrieval import MetadataFilter, QdrantVectorStore


class ControlledGateway:
    def __init__(self) -> None:
        self.proposal = True

    def generate(self, request: ModelRequest) -> ModelResponse:
        if self.proposal:
            self.proposal = False
            return ModelResponse(
                model_id=request.model_id,
                output_text="",
                finish_reason=ModelFinishReason.STOP,
                tool_call=ModelToolCall.from_mapping(
                    "search_documents", {"query": "meeting access code"}
                ),
            )
        return ModelResponse(
            model_id=request.model_id,
            output_text="Evidence received.",
            finish_reason=ModelFinishReason.STOP,
        )


def test_real_chunked_application_replacement_catalog_restart_and_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if (
        os.getenv("CONTEXT_ENGINE_RUN_LOCAL_EMBEDDING_INTEGRATION") != "1"
        or os.getenv("CONTEXT_ENGINE_RUN_QDRANT_INTEGRATION") != "1"
    ):
        pytest.skip("Enable both local embedding and Qdrant integration for chunked composition.")
    qdrant = pytest.importorskip("qdrant_client")
    settings = replace(
        ApplicationSettings.from_environment(),
        collection_name=f"context-engine-chunk-application-it-{uuid4().hex}",
    )
    monkeypatch.setattr(
        composition_module, "OllamaModelGateway", lambda **kwargs: ControlledGateway()
    )
    app = composition_module.build_live_application(settings)
    try:
        app.prepare()
        source_ids = app.ingest_uploads(
            (
                UploadCandidate(
                    "meeting.md",
                    b"Unrelated background details.\n\n" * 80
                    + b"The meeting access code is COBALT-742.",
                ),
            )
        ).source_ids
        assert len(app.documents.uploaded_sources[0].chunk_ids) > 1
        result = app.run_prompt("What is the meeting access code?")
        assert result.status is RunStatus.SUCCESS
        retrieved: list[dict[str, Any]] = []
        for tool_result in result.tool_results:
            found = tool_result.output_as_mapping().get("results")
            if isinstance(found, list):
                retrieved.extend(found)
        assert any("COBALT-742" in item["content"] for item in retrieved)
        assert any(item["metadata"].get("source_id") in source_ids for item in retrieved)
        assert (
            app.ingest_uploads(
                (UploadCandidate("meeting.md", b"The new access code is AMBER-315."),)
            ).source_ids
            == source_ids
        )
        assert app.documents.last_report.outcomes[0].status.value == "replaced"
        assert (
            app.documents.uploaded_sources[0].chunk_ids
            == app.documents.last_report.outcomes[0].chunk_ids
        )
        assert app.documents.last_report.chunk_count == 1
        restarted = composition_module.build_live_application(settings)
        restarted.prepare()
        assert restarted.documents.uploaded_sources == app.documents.uploaded_sources
        source_store = restarted.documents._ingestion._store
        assert isinstance(source_store, QdrantVectorStore)
        vector = restarted.documents._ingestion._provider.embed_query("access code")
        matches = source_store.search(
            vector,
            top_k=100,
            metadata_filter=MetadataFilter.from_mapping({"source_id": source_ids[0]}),
        )
        assert len(matches) == 1 and "AMBER-315" in matches[0].document.content
        assert restarted.clear_uploads() == source_ids
        assert not source_store.search(
            vector, metadata_filter=MetadataFilter.from_mapping({"source_id": source_ids[0]})
        )
        assert restarted.documents.preloaded_sources
    finally:
        client = qdrant.QdrantClient(url=settings.qdrant_url)
        try:
            client.delete_collection(settings.collection_name)
        finally:
            client.close()
