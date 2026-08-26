"""Thin Streamlit rendering layer for the Context Engine Agent Workbench."""

from __future__ import annotations

import importlib
from typing import Any

from context_engine.workbench.application import (
    PROMPT_PRESETS,
    WorkbenchApplication,
    WorkbenchDependencyError,
    build_live_workbench,
)
from context_engine.workbench.documents import UploadCandidate, WorkbenchDocumentError
from context_engine.workbench.presentation import WorkbenchRunStatus, WorkbenchRunView


def main() -> None:
    """Render the local workbench without placing domain behavior in the UI layer."""
    st: Any = importlib.import_module("streamlit")
    st.set_page_config(page_title="Context Engine Agent Workbench", page_icon="⚙️", layout="wide")
    st.title("Context Engine Agent Workbench")
    st.caption("LIVE · LOCAL · M3 deterministic tools + M4 tool-mediated retrieval")
    st.info(
        "Tool-mediated retrieval is implemented. Automatic context assembly, chunking, "
        "reranking, and advanced RAG remain future M5/M6 work."
    )

    application = _get_application(st)
    if application is None:
        return

    _render_sidebar(st, application)
    _render_prompt(st, application)
    run_view = st.session_state.get("workbench_run_view")
    if isinstance(run_view, WorkbenchRunView):
        _render_run(st, run_view)


def _get_application(st: Any) -> WorkbenchApplication | None:
    current = st.session_state.get("workbench_application")
    if isinstance(current, WorkbenchApplication):
        return current
    try:
        application = build_live_workbench()
        application.prepare()
    except WorkbenchDependencyError as exc:
        st.error(f"Live dependency failure [{exc.phase}]: {exc.message}")
        st.caption("Fix the labeled local dependency and reload the page.")
        return None
    except Exception as exc:
        st.error(f"Workbench preparation failure: {type(exc).__name__}: {exc}")
        return None
    st.session_state["workbench_application"] = application
    return application


def _render_sidebar(st: Any, application: WorkbenchApplication) -> None:
    with st.sidebar:
        st.header("Documents")
        st.success(f"{len(application.documents.preloaded_documents)} demo documents ready")
        for document in application.documents.preloaded_documents:
            source_name = document.metadata_as_mapping().get("source_name", document.document_id)
            st.caption(f"Preloaded · {source_name}")

        uploaded_files = st.file_uploader(
            "Upload UTF-8 text or Markdown",
            type=("txt", "md"),
            accept_multiple_files=True,
            help=(
                f"Up to {application.settings.max_uploads} files, "
                f"{application.settings.max_upload_bytes} bytes each."
            ),
        )
        if st.button("Ingest selected files", use_container_width=True):
            candidates = tuple(
                UploadCandidate(name=uploaded.name, content=uploaded.getvalue())
                for uploaded in uploaded_files
            )
            if not candidates:
                st.warning("Choose at least one .txt or .md file.")
            else:
                try:
                    document_ids = application.ingest_uploads(candidates)
                except WorkbenchDocumentError as exc:
                    st.error(f"Upload validation failed: {exc}")
                except Exception as exc:
                    st.error(f"Document ingestion failed: {type(exc).__name__}: {exc}")
                else:
                    st.success(f"Ingested {len(document_ids)} uploaded document(s).")

        for document in application.documents.uploaded_documents:
            source_name = document.metadata_as_mapping().get("source_name", document.document_id)
            st.caption(f"Uploaded · {source_name}")
        if st.button("Clear uploaded documents", use_container_width=True):
            try:
                cleared_ids = application.clear_uploads()
            except Exception as exc:
                st.error(f"Uploaded-document cleanup failed: {type(exc).__name__}: {exc}")
            else:
                st.success(f"Cleared {len(cleared_ids)} upload(s); demo documents remain.")

        st.divider()
        st.header("Live dependencies")
        st.caption(f"Model · configured · {application.settings.model_id}")
        st.caption(f"Embeddings · ready · {application.settings.embedding_model_id}")
        st.caption(f"Vector store · ready · {application.settings.qdrant_url}")
        st.caption("Agent + Tool runtime · ready")


def _render_prompt(st: Any, application: WorkbenchApplication) -> None:
    st.header("Ask the agent")
    preset_name = st.selectbox("Prompt preset", tuple(PROMPT_PRESETS))
    if "workbench_prompt" not in st.session_state:
        st.session_state["workbench_prompt"] = PROMPT_PRESETS[preset_name]
    if st.button("Load preset"):
        st.session_state["workbench_prompt"] = PROMPT_PRESETS[preset_name]
    prompt = st.text_area("Editable prompt", key="workbench_prompt", height=110)
    if st.button("Run live agent", type="primary", use_container_width=True):
        with st.spinner("Running the local model and deterministic runtime..."):
            st.session_state["workbench_run_view"] = application.run_prompt(prompt)


def _render_run(st: Any, run_view: WorkbenchRunView) -> None:
    st.header("Final response")
    if run_view.status is WorkbenchRunStatus.SUCCESS:
        st.success(run_view.final_response or "The runtime completed without response text.")
    else:
        st.error(
            f"Live run failed [{run_view.error_phase or run_view.status.value}]: "
            f"{run_view.error_message or 'No further details were returned.'}"
        )

    st.header("Live execution lifecycle")
    for index, step in enumerate(run_view.lifecycle, start=1):
        st.markdown(f"**{index}. {step.name}** · `{step.status}`")
        st.caption(step.detail)

    st.header("Retrieved evidence / structured tool result")
    if not run_view.evidence:
        st.caption("No retrieval evidence was returned in this run.")
    for item in run_view.evidence:
        with st.expander(
            f"{item.document_id} · {item.score:.4f} · {item.source_kind} · {item.source_name}",
            expanded=True,
        ):
            st.json(dict(item.metadata))
            st.text(item.content)
            if item.content_truncated:
                st.caption("Content was bounded by the search_documents tool configuration.")

    if run_view.tool_results:
        st.subheader("Structured ToolResult payloads")
        for result in run_view.tool_results:
            payload: dict[str, object] = {
                "tool_name": result.invocation.tool_name,
                "arguments": result.invocation.arguments_as_mapping(),
                "status": result.status.value,
                "output": result.output_as_mapping(),
                "error": (
                    None
                    if result.error is None
                    else {
                        "type": result.error.error_type,
                        "message": result.error.message,
                    }
                ),
            }
            st.json(payload)

    st.header("Execution trace")
    if not run_view.traces:
        st.caption("No tool execution trace was produced.")
    else:
        st.dataframe(
            [
                {
                    "tool": trace.tool_name,
                    "arguments": dict(trace.arguments),
                    "policy": trace.policy,
                    "status": trace.status,
                    "error_type": trace.error_type,
                    "error_message": trace.error_message,
                }
                for trace in run_view.traces
            ],
            use_container_width=True,
            hide_index=True,
        )


if __name__ == "__main__":
    main()
