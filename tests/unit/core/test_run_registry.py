from __future__ import annotations

import subprocess
import sys
from dataclasses import replace

import pytest

from context_engine.agent import (
    AgentExecutionState,
    AgentExecutionStatus,
    AgentRuntimeExecutionOutcome,
    AgentRuntimeExecutionResult,
)
from context_engine.core.runs import (
    RunAlreadyActiveError,
    RunRecord,
    RunRegistry,
    RunStatus,
    UnknownRunError,
    derive_error,
    derive_run_status,
)
from context_engine.observability import RunEvent, RunStarted
from context_engine.tools import (
    ToolExecutionErrorDetails,
    ToolExecutionTrace,
    ToolInvocation,
    ToolResultStatus,
)


def _record(run_id: str) -> RunRecord:
    return RunRecord(
        run_id=run_id,
        prompt="hello",
        model_id="fake-model",
        max_model_iterations=4,
        status=RunStatus.RUNNING,
        started_at=1.0,
    )


def _event(run_id: str, sequence: int) -> RunEvent:
    return RunEvent(
        run_id=run_id,
        sequence=sequence,
        timestamp=float(sequence),
        payload=RunStarted(model_id="fake-model", max_model_iterations=4),
    )


def _result(
    outcome: AgentRuntimeExecutionOutcome, error: str | None = None
) -> AgentRuntimeExecutionResult:
    return AgentRuntimeExecutionResult(
        outcome=outcome,
        terminal_state=AgentExecutionState(status=AgentExecutionStatus.FAILED),
        error_message=error,
    )


def _trace(status: ToolResultStatus) -> ToolExecutionTrace:
    return ToolExecutionTrace(
        invocation=ToolInvocation.from_mapping("search_documents", {"query": "x"}),
        policy_decision=None,
        approval_decision=None,
        status=status,
        error=(
            ToolExecutionErrorDetails(error_type="RuntimeError", message="boom")
            if status is ToolResultStatus.ERROR
            else None
        ),
    )


def test_registry_allows_one_active_run_and_frees_the_slot_on_finish() -> None:
    registry = RunRegistry()
    registry.begin(_record("a"))

    with pytest.raises(RunAlreadyActiveError):
        registry.begin(_record("b"))
    assert registry.active_run_id == "a"

    finished = registry.finish("a", lambda record: replace(record, status=RunStatus.SUCCESS))
    assert finished.status is RunStatus.SUCCESS
    assert registry.active_run_id is None

    registry.begin(_record("b"))
    assert [record.run_id for record in registry.list_runs()] == ["a", "b"]


def test_registry_rejects_duplicate_ids_and_unfinished_finish_records() -> None:
    registry = RunRegistry()
    registry.begin(_record("a"))

    with pytest.raises(ValueError, match="finished status"):
        registry.finish("a", lambda record: record)
    registry.finish("a", lambda record: replace(record, status=RunStatus.FAILED))
    with pytest.raises(ValueError, match="Duplicate run id"):
        registry.begin(_record("a"))


def test_registry_appends_events_and_returns_only_newer_ones() -> None:
    registry = RunRegistry()
    registry.begin(_record("a"))
    registry.append_event(_event("a", 1))
    registry.append_event(_event("a", 2))
    registry.append_event(_event("unknown", 1))

    newer, done = registry.wait_for_events("a", after_sequence=1, timeout=0)
    assert [event.sequence for event in newer] == [2]
    assert done is False

    nothing, done = registry.wait_for_events("a", after_sequence=2, timeout=0)
    assert nothing == () and done is False

    registry.finish("a", lambda record: replace(record, status=RunStatus.SUCCESS))
    nothing, done = registry.wait_for_events("a", after_sequence=2, timeout=0)
    assert nothing == () and done is True


def test_registry_raises_for_unknown_runs() -> None:
    registry = RunRegistry()

    with pytest.raises(UnknownRunError):
        registry.get("missing")
    with pytest.raises(UnknownRunError):
        registry.wait_until_finished("missing", timeout=0)
    with pytest.raises(UnknownRunError):
        registry.finish("missing", lambda record: record)


@pytest.mark.parametrize(
    ("outcome", "trace_status", "expected"),
    [
        (AgentRuntimeExecutionOutcome.RESPONDED, ToolResultStatus.SUCCESS, RunStatus.SUCCESS),
        (AgentRuntimeExecutionOutcome.RESPONDED, ToolResultStatus.ERROR, RunStatus.FAILED),
        (AgentRuntimeExecutionOutcome.FAILED, ToolResultStatus.SUCCESS, RunStatus.FAILED),
        (
            AgentRuntimeExecutionOutcome.LIMIT_REACHED,
            ToolResultStatus.ERROR,
            RunStatus.LIMIT_REACHED,
        ),
    ],
)
def test_run_status_never_reports_success_after_a_tool_error(
    outcome: AgentRuntimeExecutionOutcome, trace_status: ToolResultStatus, expected: RunStatus
) -> None:
    assert derive_run_status(_result(outcome), (_trace(trace_status),)) is expected


def test_error_details_prefer_the_first_tool_error_over_the_runtime_message() -> None:
    result = _result(AgentRuntimeExecutionOutcome.FAILED, "runtime message")

    assert derive_error(result, (_trace(ToolResultStatus.ERROR),), RunStatus.FAILED) == (
        "tool_execution",
        "RuntimeError: boom",
    )
    assert derive_error(result, (), RunStatus.FAILED) == ("agent_runtime", "runtime message")
    assert derive_error(result, (), RunStatus.SUCCESS) == (None, None)


def test_core_package_imports_without_a_ui_or_web_framework() -> None:
    script = (
        "import sys, context_engine.core;"
        "loaded = [m for m in ('streamlit', 'fastapi', 'starlette') if m in sys.modules];"
        "print(','.join(loaded))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True, timeout=120
    )
    assert completed.stdout.strip() == ""
