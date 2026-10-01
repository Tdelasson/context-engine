"""Opt-in verification of the workbench with real local dependencies."""

import os
from dataclasses import replace
from uuid import uuid4

import pytest

from context_engine.workbench.application import PROMPT_PRESETS, build_live_workbench
from context_engine.workbench.config import WorkbenchSettings
from context_engine.workbench.documents import UploadCandidate
from context_engine.workbench.presentation import WorkbenchRunStatus


def test_live_workbench_search_upload_calculation_and_cleanup() -> None:
    if os.getenv("CONTEXT_ENGINE_RUN_WORKBENCH_INTEGRATION") != "1":
        pytest.skip("Set CONTEXT_ENGINE_RUN_WORKBENCH_INTEGRATION=1 for the local workbench test.")
    qdrant = pytest.importorskip("qdrant_client")
    settings = replace(
        WorkbenchSettings.from_environment(),
        collection_name=f"context-engine-workbench-it-{uuid4().hex}",
    )
    application = build_live_workbench(settings)
    try:
        application.prepare()
        preloaded = application.run_prompt(PROMPT_PRESETS["Project architecture"])
        assert preloaded.status is WorkbenchRunStatus.SUCCESS, preloaded.error_message
        assert any(item.source_kind == "preloaded" for item in preloaded.evidence)
        assert preloaded.final_response

        uploaded_ids = application.ingest_uploads(
            (
                UploadCandidate(
                    name="meeting-fact.md", content=b"The meeting access code is COBALT-742."
                ),
            )
        )
        uploaded = application.run_prompt(
            "Search the uploaded documents: what is the meeting access code?"
        )
        assert uploaded.status is WorkbenchRunStatus.SUCCESS, uploaded.error_message
        assert any(item.document_id in uploaded_ids for item in uploaded.evidence)
        assert uploaded.final_response and "COBALT-742" in uploaded.final_response.upper()

        calculation = application.run_prompt(PROMPT_PRESETS["Calculator"])
        assert calculation.status is WorkbenchRunStatus.SUCCESS, calculation.error_message
        assert any(
            result.invocation.tool_name == "calculator"
            and result.output_as_mapping().get("value") == 19
            for result in calculation.tool_results
        )
        assert application.clear_uploads() == uploaded_ids
        assert not application.documents.uploaded_documents
        after_cleanup = application.run_prompt(PROMPT_PRESETS["Project architecture"])
        assert after_cleanup.status is WorkbenchRunStatus.SUCCESS, after_cleanup.error_message
        assert after_cleanup.evidence
        assert all(item.source_kind == "preloaded" for item in after_cleanup.evidence)
    finally:
        # A unique test collection prevents touching the user's workbench documents.
        client = qdrant.QdrantClient(
            url=settings.qdrant_url, timeout=settings.qdrant_timeout_seconds
        )
        try:
            client.delete_collection(settings.collection_name)
        finally:
            client.close()
