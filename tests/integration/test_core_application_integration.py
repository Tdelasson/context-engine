"""Opt-in verification of the core application with real local dependencies."""

import os
from dataclasses import replace
from uuid import uuid4

import pytest

from context_engine.core.composition import build_live_application
from context_engine.core.prompts import PROMPT_PRESETS
from context_engine.core.runs import RunRecord, RunStatus
from context_engine.core.settings import ApplicationSettings
from context_engine.core.sources import UploadCandidate


def _evidence(record: RunRecord) -> list[dict[str, object]]:
    """Return every search_documents result the run retrieved."""
    items: list[dict[str, object]] = []
    for result in record.tool_results:
        if result.invocation.tool_name == "search_documents":
            raw = result.output_as_mapping().get("results")
            if isinstance(raw, list):
                items.extend(item for item in raw if isinstance(item, dict))
    return items


def _metadata(item: dict[str, object]) -> dict[str, object]:
    metadata = item.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def test_live_application_search_upload_calculation_and_cleanup() -> None:
    if os.getenv("CONTEXT_ENGINE_RUN_WORKBENCH_INTEGRATION") != "1":
        pytest.skip(
            "Set CONTEXT_ENGINE_RUN_WORKBENCH_INTEGRATION=1 for the local application test."
        )
    qdrant = pytest.importorskip("qdrant_client")
    settings = replace(
        ApplicationSettings.from_environment(),
        collection_name=f"context-engine-application-it-{uuid4().hex}",
    )
    application = build_live_application(settings)
    try:
        application.prepare()
        preloaded = application.run_prompt(PROMPT_PRESETS["Project architecture"])
        assert preloaded.status is RunStatus.SUCCESS, preloaded.error_message
        assert any(
            _metadata(item).get("source_kind") == "preloaded" for item in _evidence(preloaded)
        )
        assert preloaded.final_response

        uploaded_ids = application.ingest_uploads(
            (
                UploadCandidate(
                    name="meeting-fact.md", content=b"The meeting access code is COBALT-742."
                ),
            )
        ).source_ids
        uploaded = application.run_prompt(
            "Search the uploaded documents: what is the meeting access code?"
        )
        assert uploaded.status is RunStatus.SUCCESS, uploaded.error_message
        assert any(_metadata(item).get("source_id") in uploaded_ids for item in _evidence(uploaded))
        assert uploaded.final_response and "COBALT-742" in uploaded.final_response.upper()

        calculation = application.run_prompt(PROMPT_PRESETS["Calculator"])
        assert calculation.status is RunStatus.SUCCESS, calculation.error_message
        assert any(
            result.invocation.tool_name == "calculator"
            and result.output_as_mapping().get("value") == 19
            for result in calculation.tool_results
        )
        assert application.clear_uploads() == uploaded_ids
        assert not application.documents.uploaded_sources
        after_cleanup = application.run_prompt(PROMPT_PRESETS["Project architecture"])
        assert after_cleanup.status is RunStatus.SUCCESS, after_cleanup.error_message
        evidence = _evidence(after_cleanup)
        assert evidence
        assert all(_metadata(item).get("source_kind") == "preloaded" for item in evidence)
    finally:
        # A unique test collection prevents touching the user's documents.
        client = qdrant.QdrantClient(
            url=settings.qdrant_url, timeout=settings.qdrant_timeout_seconds
        )
        try:
            client.delete_collection(settings.collection_name)
        finally:
            client.close()
