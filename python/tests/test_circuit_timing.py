"""Package-level timing binding tests using the live RingCounter package."""

from pathlib import Path

from chiplib.circuit_timing import CircuitTimingBinding, CircuitTimingError


ROOT = Path(__file__).resolve().parents[2]
RING = ROOT / "examples" / "circuits" / "RV8GR_RingCounter" / "circuit.json"


def ready_ring() -> CircuitTimingBinding:
    binding = CircuitTimingBinding.load(RING)
    binding.runner.reset({"/CLR": 0})
    binding.runner.set_input("/CLR", 1)
    return binding


def test_clock_edge_binds_actual_functional_output_to_clock_to_q_event():
    binding = ready_ring()
    events = binding.pulse_clock()
    event = next(item for item in events if item.output_port == "T0")

    assert (event.before, event.after) == (0, 1)
    assert event.chip_ref == "U8"
    assert event.part == "74HC164"
    assert event.package_path == "phase_output"
    assert event.selection.kind.value == "clock_to_q_high"
    assert event.selection.delay_ps > 0
    assert event.model_provenance["source"] == "live_db_package"
    assert event.snapshot()["modeled_only"] is True

    signal = "rv8gr_ring_counter.T0"
    event_time = next(
        row["time_ps"] for row in binding.timed.trace if row["kind"] == "active_edge"
    )
    binding.timed.run_until(event_time + event.selection.delay_ps - 1)
    assert binding.timed.signals[signal] == 0
    binding.timed.run_until(event_time + event.selection.delay_ps)
    assert binding.timed.signals[signal] == 1
    output_trace = next(
        row for row in reversed(binding.timed.trace)
        if row.get("kind") == "timed_output" and row.get("signal") == signal
    )
    assert output_trace["provenance"] in {"exact", "generic", "path", "default"}


def test_constraint_records_are_selected_automatically_with_db_provenance():
    constraints = ready_ring().constraint_provenance("CLK")
    for name in ("setup", "hold", "minimum_pulse_width"):
        record = constraints[name]
        assert record["status"] != "blocked"
        assert record["delay_ps"] is not None
        assert record["part"] == "74HC164"
        assert record["package_path"] == "phase_output"
        assert record["provenance"] in {"exact", "generic", "not_applicable"}
        assert record["source"]
        assert record["modeled_only"] is True


def test_package_path_compiles_db_pin_roles_and_real_nets():
    compiled = ready_ring().compiled_path()
    assert compiled.chip_ref == "U8"
    assert compiled.clock_pin == "CLK"
    assert compiled.clock_net == "CLK"
    assert compiled.constrained_nets == ("NOT_T0", "NOT_T1")
    assert compiled.output_ports == ("T0", "T1", "T2")
    assert compiled.trigger_edge == "rising"


def test_actual_package_pulse_width_before_at_after_is_enforced_automatically():
    probe = ready_ring()
    required = probe.constraint_provenance()["minimum_pulse_width"]["delay_ps"]
    for offset, violates in ((-1, True), (0, False), (1, False)):
        binding = ready_ring()
        events = binding.pulse_clock(high_ps=required + offset)
        assert events
        found = [
            item for item in binding.timed.diagnostics
            if item.code == "timing.pulse_width_violation"
        ]
        assert bool(found) is violates
        if found:
            assert found[0].provenance in {"exact", "generic"}
            assert found[0].modeled_only is True


def test_actual_package_setup_threshold_before_at_after_is_enforced_automatically():
    probe = ready_ring()
    required = probe.constraint_provenance()["setup"]["delay_ps"]
    for offset, violates in ((-1, True), (0, False), (1, False)):
        binding = ready_ring()
        binding.pulse_clock(setup_ps=required + offset)
        found = [item for item in binding.timed.diagnostics if item.code == "timing.setup_violation"]
        assert bool(found) is violates


def test_actual_package_hold_threshold_before_at_after_is_enforced_automatically():
    probe = ready_ring()
    required = probe.constraint_provenance()["hold"]["delay_ps"]
    assert required > 0
    for offset, violates in ((-1, True), (0, False), (1, False)):
        binding = ready_ring()
        binding.pulse_clock(
            high_ps=max(required + 1, 1), constrained_change_ps=required + offset
        )
        found = [item for item in binding.timed.diagnostics if item.code == "timing.hold_violation"]
        assert bool(found) is violates


def test_input_without_explicit_package_timing_path_is_blocked():
    binding = ready_ring()
    before = binding.runner.read()
    try:
        binding.set_input("/CLR", 0)
    except CircuitTimingError as exc:
        assert exc.issue.code == "missing_package_timing_path"
        assert exc.issue.path == "timing.paths./CLR"
        assert "found 0" in exc.issue.message
    else:
        raise AssertionError("missing timing path must fail closed")
    assert binding.runner.read() == before


def test_binding_does_not_claim_campaign_or_physical_completion():
    snapshot = ready_ring().pulse_clock()[0].snapshot()
    assert snapshot["circuit"] == "rv8gr_ring_counter"
    assert snapshot["modeled_only"] is True
    assert "campaign" not in snapshot
    assert "physical" not in snapshot


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print("Components circuit timing binding tests passed")
