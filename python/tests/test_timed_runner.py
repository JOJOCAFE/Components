"""Threshold tests for deterministic modeled timing primitives."""

from chiplib.db import load_digital_definition
from chiplib.timed_runner import TimedRunner
from chiplib.timing import ConstraintKind, TimingProfile


def profile(part="74HC161"):
    return TimingProfile.from_definition(load_digital_definition(part))


def test_propagation_and_clock_to_q_apply_at_exact_catalog_thresholds():
    timing = profile()
    runner = TimedRunner()
    selected = runner.schedule_output("Q0", 0, 1, timing, clock_to_q=True)
    runner.run_until(selected.delay_ps - 1)
    assert "Q0" not in runner.signals
    runner.run_until(selected.delay_ps)
    assert runner.signals["Q0"] == 1
    assert runner.trace[-1]["provenance"] == "exact"
    assert runner.snapshot()["boundary"].startswith("modeled digital")


def test_inertial_output_cancels_short_pulse_but_transport_preserves_it():
    timing = profile("74HC00")
    runner = TimedRunner()
    runner.schedule_output("Y", 0, 1, timing)
    runner.schedule_output("Y", 1, 0, timing)
    runner.run_until(100_000)
    assert runner.signals["Y"] == 0
    assert len([row for row in runner.trace if row["signal"] == "Y"]) == 1


def test_setup_threshold_one_before_at_and_after():
    timing = profile()
    required = timing.select_constraint(ConstraintKind.SETUP, path="data_min").delay_ps
    for offset, violates in [(-1, True), (0, False), (1, False)]:
        runner = TimedRunner()
        runner.drive("D", 1, time_ps=0)
        runner.run_until(required + offset)
        runner.check_active_edge("CLK", ["D"], timing, setup_path="data_min")
        assert any(d.code == "timing.setup_violation" for d in runner.diagnostics) is violates


def test_hold_window_is_open_interval_and_has_provenance():
    timing = profile("74HC164")
    required = timing.select_constraint(ConstraintKind.HOLD).delay_ps
    assert required > 0
    for offset, violates in [(-1, True), (0, False), (1, False)]:
        runner = TimedRunner()
        runner.check_active_edge("CLK", ["D"], timing)
        runner.drive("D", 1, time_ps=required + offset)
        runner.run_until(required + offset)
        found = [d for d in runner.diagnostics if d.code == "timing.hold_violation"]
        assert bool(found) is violates
        if found:
            assert found[0].provenance in {"exact", "generic"}


def test_pulse_width_threshold_one_before_at_and_after():
    timing = profile()
    required = timing.select_constraint(ConstraintKind.MINIMUM_PULSE_WIDTH).delay_ps
    for offset, violates in [(-1, True), (0, False), (1, False)]:
        runner = TimedRunner()
        runner.check_clock_transition("CLK", 0, 1, timing)
        runner.run_until(required + offset)
        runner.check_clock_transition("CLK", 1, 0, timing)
        assert any(d.code == "timing.pulse_width_violation" for d in runner.diagnostics) is violates


def test_x_z_contention_and_contiguous_episode_are_distinct():
    runner = TimedRunner()
    assert runner.resolve_bus("BUS", {"A": "Z", "B": "Z"}) == "Z"
    assert runner.resolve_bus("BUS", {"A": 0, "B": 1}) == "X"
    assert runner.resolve_bus("BUS", {"A": 0, "B": 1}) == "X"
    assert len(runner.diagnostics) == 1
    assert runner.resolve_bus("BUS", {"A": 1, "B": 1}) == 1
    assert runner.resolve_bus("BUS", {"A": "X", "B": "Z"}) == "X"
    assert len(runner.diagnostics) == 2


def test_bus_ownership_overlap_is_visible_even_for_equal_values():
    runner = TimedRunner()
    assert runner.resolve_bus(
        "BUS", {"ALU": 1, "RAM": 1}, enforce_single_owner=True
    ) == 1
    assert runner.diagnostics[0].code == "simulation.bus_contention"


def test_deadband_threshold_one_before_at_and_after():
    for observed, violates in [(9, True), (10, False), (11, False)]:
        runner = TimedRunner()
        runner.mark_driver_disabled("BUS")
        runner.run_until(observed)
        runner.mark_driver_enabled("BUS", required_deadband_ps=10)
        assert any(d.code == "timing.deadband_violation" for d in runner.diagnostics) is violates


def test_unknown_clock_edge_is_diagnostic_not_valid_pulse():
    runner = TimedRunner()
    runner.check_clock_transition("CLK", 0, "X", profile())
    assert runner.diagnostics[0].code == "timing.unknown_clock_edge"
    assert runner.diagnostics[0].modeled_only is True


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print("Components timed runner tests passed")
