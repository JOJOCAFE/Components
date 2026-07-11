"""Focused tests for deterministic named virtual runtime adapters."""

import json
import math
import unittest

from chiplib.virtual_runtime import (
    BusProbeAdapter,
    ClockSourceAdapter,
    DelayNoiseAdapter,
    OutputAssertAdapter,
    OutputAssertionFailure,
    ProbeAdapter,
    RCParasiticAdapter,
    SwitchAdapter,
    VirtualRuntimeError,
    VirtualTransition,
    create_virtual_adapter,
)


def test_factory_builds_named_contracts_and_rejects_generic_virtual():
    assert isinstance(create_virtual_adapter("ClockSource", "CLK"), ClockSourceAdapter)
    assert isinstance(create_virtual_adapter("Switch", "SW"), SwitchAdapter)
    assert isinstance(create_virtual_adapter("Probe", "P"), ProbeAdapter)
    assert isinstance(create_virtual_adapter("BusProbe", "BP"), BusProbeAdapter)
    assert isinstance(create_virtual_adapter("OutputAssert", "A"), OutputAssertAdapter)
    assert isinstance(create_virtual_adapter("RCParasitic", "RC"), RCParasiticAdapter)
    assert isinstance(create_virtual_adapter("DelayNoise", "D", seed=7), DelayNoiseAdapter)
    with unittest.TestCase().assertRaisesRegex(VirtualRuntimeError, "generic Virtual"):
        create_virtual_adapter("Virtual", "CTRL")
    with unittest.TestCase().assertRaisesRegex(VirtualRuntimeError, "unsupported virtual part"):
        create_virtual_adapter("Mystery", "X1")


def test_clock_and_switch_emit_repeatable_integer_picosecond_plans():
    clock = ClockSourceAdapter("VCLK", period_ps=100, idle_state=0)
    assert [(event.time_ps, event.value) for event in clock.ticks(2, start_ps=25)] == [
        (25, 1), (75, 0), (125, 1), (175, 0),
    ]
    assert clock.manual_tick(start_ps=200) == clock.ticks(1, start_ps=200)

    switch = SwitchAdapter("SW1")
    assert switch.set_state(1, time_ps=4).snapshot()["value"] == 1
    assert [(event.time_ps, event.value) for event in switch.pulse(20, start_ps=10)] == [
        (10, 1), (30, 0),
    ]


def test_probe_and_bus_probe_are_passive_serializable_observers():
    probe = ProbeAdapter("P1")
    assert probe.sample("Z", time_ps=10)["value"] == "Z"

    bus = BusProbeAdapter("BP1")
    clear = bus.sample({"U2": "Z", "U1": 1}, time_ps=20)
    conflict = bus.sample({"U2": 0, "U1": 1}, time_ps=30)
    assert clear["active_drivers"] == ["U1"] and clear["value"] == 1
    assert conflict["conflict"] and conflict["value"] == "X"
    assert list(conflict["drivers"]) == ["U1", "U2"]
    json.dumps({"probe": probe.snapshot(), "bus": bus.snapshot()}, sort_keys=True)


def test_output_assert_passes_and_fails_loudly_with_recorded_evidence():
    assertion = OutputAssertAdapter("CHECK")
    assert assertion.check(1, 1, time_ps=5)["passed"]
    assert assertion.check("Z", mode="is_high_z", time_ps=6)["passed"]
    assert assertion.check(
        1, 1, mode="within_timing_window", time_ps=10,
        window_start_ps=8, window_end_ps=12,
    )["passed"]
    with unittest.TestCase().assertRaisesRegex(OutputAssertionFailure, "CHECK failed at 7 ps"):
        assertion.check(0, 1, time_ps=7)
    assert assertion.snapshot()["checks"][-1]["passed"] is False


def test_rc_estimate_matches_database_formula_and_marks_claim_boundary():
    estimate = RCParasiticAdapter(
        "BUSRC", source_resistance_ohm=80, wire_capacitance_pf=50,
        chip_input_capacitance_pf=20, probe_capacitance_pf=10,
    ).estimate()
    assert estimate["total_capacitance_pf"] == 80
    assert estimate["tau_ns"] == 6.4
    assert math.isclose(estimate["settling_10_90_ns"], 14.08)
    assert estimate["delay_ps"] == 14080
    assert estimate["modeled_only"] is True
    assert "physical signoff requires measurement" in estimate["claim_boundary"]


def test_delay_noise_is_seeded_repeatable_and_every_result_is_modeled_only():
    inputs = (VirtualTransition(10, 1), VirtualTransition(50, 0))
    config = dict(
        seed=35863, base_delay_ps=5, jitter_ps=5,
        glitch_probability=1.0, glitch_width_ps=10,
    )
    first = DelayNoiseAdapter("D1", **config).transform(inputs)
    second = DelayNoiseAdapter("D1", **config).transform(inputs)
    assert first == second
    assert [event.kind for event in first] == [
        "modeled_glitch", "delayed_drive", "modeled_glitch", "delayed_drive",
    ]
    assert all(event.modeled_only for event in first)


def test_invalid_profiles_fail_before_runtime_integration():
    case = unittest.TestCase()
    with case.assertRaises(ValueError):
        ClockSourceAdapter("CLK", period_ps=1)
    with case.assertRaises(ValueError):
        SwitchAdapter("SW", state="Z")
    with case.assertRaises(ValueError):
        RCParasiticAdapter("RC", source_resistance_ohm=-1)
    with case.assertRaises(ValueError):
        DelayNoiseAdapter("D", seed=1, glitch_probability=1.1)
    with case.assertRaises(ValueError):
        DelayNoiseAdapter("D", seed=True)


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Components virtual runtime tests passed: {len(tests)}")
