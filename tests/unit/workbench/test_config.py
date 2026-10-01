import pytest

from context_engine.workbench.config import WorkbenchConfigurationError, WorkbenchSettings


@pytest.mark.parametrize("value", [0.0, -1.0, float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize("field", ["ollama_timeout_seconds", "qdrant_timeout_seconds"])
def test_timeouts_must_be_positive_and_finite(field: str, value: float) -> None:
    with pytest.raises(WorkbenchConfigurationError, match=field):
        WorkbenchSettings(**{field: value})  # type: ignore[arg-type]


def test_environment_overrides_model_and_upload_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTEXT_ENGINE_WORKBENCH_MODEL", "local-model")
    monkeypatch.setenv("CONTEXT_ENGINE_WORKBENCH_MAX_UPLOADS", "2")
    monkeypatch.setenv("CONTEXT_ENGINE_EMBEDDING_MODEL", "local-embedding")
    monkeypatch.delenv("CONTEXT_ENGINE_EMBEDDING_MODEL_REFERENCE", raising=False)

    settings = WorkbenchSettings.from_environment()

    assert settings.model_id == "local-model"
    assert settings.max_uploads == 2
    assert settings.embedding_model_reference == "local-embedding"


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("CONTEXT_ENGINE_WORKBENCH_MAX_UPLOADS", "many"),
        ("CONTEXT_ENGINE_OLLAMA_TIMEOUT_SECONDS", "later"),
        ("CONTEXT_ENGINE_WORKBENCH_MODEL", " "),
    ],
)
def test_invalid_environment_is_rejected(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(WorkbenchConfigurationError):
        WorkbenchSettings.from_environment()
