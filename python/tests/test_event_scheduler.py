"""Focused contract tests for the standalone deterministic event scheduler."""

import json
import unittest

from chiplib.events import EventPhase, EventScheduler, SchedulerLimitError


def test_integer_picoseconds_phases_and_stable_sequence_ordering():
    scheduler = EventScheduler()
    scheduler.schedule("sample", {"name": "last"}, time_ps=125, phase=EventPhase.SAMPLE_PROBES)
    scheduler.schedule("drive-a", time_ps=125, phase=EventPhase.APPLY_DRIVERS)
    scheduler.schedule("drive-b", time_ps=125, phase=EventPhase.APPLY_DRIVERS)

    events = scheduler.run_next_time()

    assert scheduler.time_ps == 125
    assert [event.kind for event in events] == ["drive-a", "drive-b", "sample"]
    assert [event.sequence for event in events] == [2, 3, 1]


def test_run_next_time_drains_generated_deltas_and_run_until_has_inclusive_boundary():
    scheduler = EventScheduler()
    scheduler.schedule("resolve", time_ps=10, phase=EventPhase.RESOLVE_NETS)
    scheduler.schedule("later", time_ps=20)

    def dispatch(event, queue):
        if event.kind == "resolve":
            queue.schedule("drive-next-delta", phase=EventPhase.APPLY_DRIVERS)
            queue.schedule("sample-same-delta", phase=EventPhase.SAMPLE_PROBES)

    first = scheduler.run_next_time(dispatch)
    assert [(event.kind, event.delta) for event in first] == [
        ("resolve", 0),
        ("sample-same-delta", 0),
        ("drive-next-delta", 1),
    ]
    assert [event.kind for event in scheduler.run_until(20)] == ["later"]
    assert scheduler.time_ps == 20
    assert scheduler.run_until(25) == ()
    assert scheduler.time_ps == 25


def test_inertial_generation_token_replaces_pending_event():
    scheduler = EventScheduler()
    old = scheduler.schedule("output", 0, time_ps=100, cancellation_key="U1.Q")
    new = scheduler.schedule("output", 1, time_ps=80, cancellation_key="U1.Q")

    assert (old.generation, new.generation) == (1, 2)
    assert [event.payload for event in scheduler.run_until(100)] == [1]


def test_transport_opt_in_preserves_every_transition():
    scheduler = EventScheduler()
    scheduler.schedule("output", 0, time_ps=100, cancellation_key="U1.Q", transport=True)
    scheduler.schedule("output", 1, time_ps=80, cancellation_key="U1.Q", transport=True)

    assert [event.payload for event in scheduler.run_until(100)] == [1, 0]


def test_delta_and_same_time_convergence_guards_include_deterministic_state():
    scheduler = EventScheduler(max_delta_cycles=2, max_same_time_events=20)
    scheduler.schedule("loop", phase=EventPhase.APPLY_DRIVERS)

    def loop(event, queue):
        queue.schedule("loop", phase=EventPhase.APPLY_DRIVERS)

    try:
        scheduler.run_next_time(loop)
    except SchedulerLimitError as caught:
        assert caught.code == "scheduler.max_delta_cycles"
        assert caught.snapshot["blocked_event"]["delta"] == 3
    else:
        raise AssertionError("delta-cycle limit did not fail")

    scheduler = EventScheduler(max_same_time_events=2)
    for index in range(3):
        scheduler.schedule("event", index)
    try:
        scheduler.run_next_time()
    except SchedulerLimitError as caught:
        assert caught.code == "scheduler.max_same_time_events"
    else:
        raise AssertionError("same-time event limit did not fail")


def test_snapshot_is_serializable_canonical_and_omits_cancelled_work():
    scheduler = EventScheduler(max_delta_cycles=7, max_same_time_events=11)
    scheduler.schedule("stale", {"z": 1}, time_ps=9, cancellation_key="Q")
    scheduler.schedule("live", {"z": 2, "a": [1, "Z"]}, time_ps=8, cancellation_key="Q")
    scheduler.schedule("probe", {"b": 2, "a": 1}, time_ps=8, phase=EventPhase.SAMPLE_PROBES)

    snapshot = scheduler.snapshot()

    assert [event["kind"] for event in snapshot["queue"]] == ["live", "probe"]
    assert list(snapshot["queue"][1]["payload"]) == ["a", "b"]
    assert json.loads(json.dumps(snapshot, sort_keys=True)) == snapshot


def test_rejects_fractional_time_past_time_and_opaque_payloads():
    scheduler = EventScheduler()
    with unittest.TestCase().assertRaises(ValueError):
        scheduler.schedule("bad", time_ps=1.5)
    with unittest.TestCase().assertRaises(TypeError):
        scheduler.schedule("bad", object())
    scheduler.run_until(10)
    with unittest.TestCase().assertRaises(ValueError):
        scheduler.schedule("past", time_ps=9)


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print("Components event scheduler tests passed")
