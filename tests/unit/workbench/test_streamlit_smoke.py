import importlib


def test_streamlit_module_import_does_not_require_live_dependencies() -> None:
    module = importlib.import_module("context_engine.workbench.streamlit_app")

    assert callable(module.main)
