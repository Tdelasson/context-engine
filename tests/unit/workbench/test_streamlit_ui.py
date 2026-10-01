"""Exercise real Streamlit widgets with deterministic runtime fixtures."""

import pytest

pytest.importorskip("streamlit", reason="Install the workbench extra for UI tests.")

from streamlit.testing.v1 import AppTest

from context_engine.workbench import streamlit_app
from context_engine.workbench.application import PROMPT_PRESETS, WorkbenchDependencyError
from context_engine.workbench.config import WorkbenchConfigurationError

from .test_application import (
    _application,
    _FailingGateway,
    _FailingSearchTool,
    _final_response,
    _Gateway,
    _SearchFixtureTool,
    _tool_call_response,
)


def _app() -> AppTest:
    return AppTest.from_string(
        "from context_engine.workbench.streamlit_app import main\nmain()"
    ).run()


def _click(app: AppTest, label: str) -> AppTest:
    return next(button for button in app.button if button.label == label).click().run()


def test_preset_and_edited_prompt_run_through_real_widgets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _Gateway(
        (
            _tool_call_response("calculator", {"expression": "(144 / 12) + 7"}),
            _final_response("The result is 19."),
            _final_response("An edited prompt response."),
        )
    )
    application = _application(gateway=gateway)
    monkeypatch.setattr(streamlit_app, "build_live_workbench", lambda: application)
    app = _app()

    app.selectbox[0].select("Calculator").run()
    _click(app, "Load preset")
    assert app.text_area[0].value == PROMPT_PRESETS["Calculator"]
    _click(app, "Run live agent")

    assert not app.exception
    assert any(item.value == "The result is 19." for item in app.success)
    assert len(app.dataframe) == 1
    app.text_area[0].input("My edited question").run()
    _click(app, "Run live agent")
    assert not app.exception
    assert gateway.requests[-1].messages[-1].content == "My edited question"
    assert any(item.value == "An edited prompt response." for item in app.success)


@pytest.mark.parametrize("fails", [False, True])
def test_retrieval_evidence_and_failures_render_without_ui_exceptions(
    monkeypatch: pytest.MonkeyPatch, fails: bool
) -> None:
    gateway = _Gateway(
        (
            _tool_call_response("search_documents", {"query": "bridge"}),
            _final_response("Retrieval failed." if fails else "The bridge opened in 2000."),
        )
    )
    application = _application(
        gateway=gateway,
        search_tool=_FailingSearchTool() if fails else _SearchFixtureTool(),
    )
    monkeypatch.setattr(streamlit_app, "build_live_workbench", lambda: application)
    app = _app()
    _click(app, "Run live agent")

    assert not app.exception
    if fails:
        assert any("tool_execution" in item.value for item in app.error)
        assert not app.expander
    else:
        assert not app.error
        assert "uploaded-fact" in app.expander[0].label
        assert "facts.md" in app.expander[0].label
        assert app.text[0].value == "The bridge opened in 2000."


@pytest.mark.parametrize(
    ("error", "label"),
    [
        (WorkbenchDependencyError("embedding", "model unavailable"), "embedding"),
        (WorkbenchDependencyError("vector_store", "Qdrant unavailable"), "vector_store"),
        (WorkbenchConfigurationError("Invalid timeout"), "configuration"),
        (RuntimeError("Ingestion failed"), "preparation"),
    ],
)
def test_initialization_failures_are_visible(
    monkeypatch: pytest.MonkeyPatch, error: Exception, label: str
) -> None:
    def fail() -> None:
        raise error

    monkeypatch.setattr(streamlit_app, "build_live_workbench", fail)
    app = _app()

    assert not app.exception
    assert label in app.error[0].value
    assert not app.button


def test_model_failure_is_visible_in_the_ui(monkeypatch: pytest.MonkeyPatch) -> None:
    application = _application(gateway=_FailingGateway())
    monkeypatch.setattr(streamlit_app, "build_live_workbench", lambda: application)
    app = _app()
    _click(app, "Run live agent")

    assert not app.exception
    assert "agent_runtime" in app.error[0].value
