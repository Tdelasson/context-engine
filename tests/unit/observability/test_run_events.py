import pytest

from context_engine.observability import (
    RecordingRunEventSink,
    RunEvent,
    RunEventEmitter,
    RunEventSink,
    RunFinished,
    RunStarted,
    StateTransitioned,
)


class _RaisingSink:
    def __init__(self) -> None:
        self.calls = 0

    def record(self, event: RunEvent) -> None:
        self.calls += 1
        raise RuntimeError("sink unavailable")


def test_emitter_stamps_run_identity_sequence_and_timestamp_in_order() -> None:
    sink = RecordingRunEventSink()
    ticks = iter([10.0, 11.5, 13.0])
    emitter = RunEventEmitter(sink, run_id="run-1", wall_clock=lambda: next(ticks))

    emitter.emit(RunStarted(model_id="stub", max_model_iterations=4))
    emitter.emit(StateTransitioned(from_status="start", to_status="context"))
    emitter.emit(RunFinished(outcome="responded", terminal_status="completed", model_iterations=1))

    assert [event.sequence for event in sink.events] == [1, 2, 3]
    assert [event.timestamp for event in sink.events] == [10.0, 11.5, 13.0]
    assert {event.run_id for event in sink.events} == {"run-1"}
    assert [event.kind for event in sink.events] == [
        "run_started",
        "state_transitioned",
        "run_finished",
    ]
    assert sink.events[1].payload == StateTransitioned(from_status="start", to_status="context")


def test_emitter_generates_distinct_run_ids_when_none_is_supplied() -> None:
    first = RunEventEmitter(RecordingRunEventSink())
    second = RunEventEmitter(RecordingRunEventSink())

    assert first.run_id
    assert first.run_id != second.run_id


def test_emitter_rejects_blank_run_id() -> None:
    with pytest.raises(ValueError, match="run_id"):
        RunEventEmitter(RecordingRunEventSink(), run_id="   ")


def test_emitter_contains_sink_failures_and_keeps_sequencing() -> None:
    sink = _RaisingSink()
    emitter = RunEventEmitter(sink, run_id="run-1")

    emitter.emit(RunStarted(model_id="stub", max_model_iterations=1))
    emitter.emit(RunFinished(outcome="failed", terminal_status="failed", model_iterations=0))

    assert sink.calls == 2
    assert emitter.sink_failures == 2


def test_emitter_exposes_the_injected_monotonic_clock() -> None:
    emitter = RunEventEmitter(RecordingRunEventSink(), monotonic_clock=lambda: 42.0)

    assert emitter.monotonic() == 42.0


def test_recording_sink_satisfies_the_sink_protocol() -> None:
    assert isinstance(RecordingRunEventSink(), RunEventSink)
