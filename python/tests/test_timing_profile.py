"""Scheduler-independent timing profile tests."""

from chiplib.db import component_ids, load_digital_definition
from chiplib.timing import ConstraintKind, DelayKind, TimingProfile, ns_to_ps


def profile(part):
    return TimingProfile.from_definition(load_digital_definition(part))


def test_transition_mapping_covers_six_logic_classes_and_clock_to_q():
    assert DelayKind.for_transition(0, 1) is DelayKind.LOW_TO_HIGH
    assert DelayKind.for_transition(1, 0) is DelayKind.HIGH_TO_LOW
    assert DelayKind.for_transition("Z", 1) is DelayKind.Z_TO_HIGH
    assert DelayKind.for_transition("Z", 0) is DelayKind.Z_TO_LOW
    assert DelayKind.for_transition(1, "Z") is DelayKind.HIGH_TO_Z
    assert DelayKind.for_transition(0, "Z") is DelayKind.LOW_TO_Z
    assert DelayKind.for_transition(0, 1, clock_to_q=True) is DelayKind.CLOCK_TO_Q_HIGH
    assert DelayKind.for_transition(1, 0, clock_to_q=True) is DelayKind.CLOCK_TO_Q_LOW


def test_integer_picosecond_conversion_is_exact():
    assert ns_to_ps(18) == 18_000
    assert ns_to_ps("0.125") == 125


def test_representative_profiles_select_conservative_values_with_provenance():
    assert profile("74HC00").select(DelayKind.LOW_TO_HIGH).delay_ps == 23_000
    assert profile("74HC245").select(DelayKind.Z_TO_HIGH).delay_ps == 340_000
    assert profile("74HC574").select(DelayKind.CLOCK_TO_Q_HIGH).delay_ps == 28_000
    assert profile("74HC161").select(DelayKind.CLOCK_TO_Q_LOW).delay_ps == 25_000
    assert profile("62256").select(DelayKind.LOW_TO_HIGH, path="oe_to_data_valid_ns").delay_ps == 35_000
    assert profile("AT28C256").select(DelayKind.HIGH_TO_Z).delay_ps == 50_000
    assert profile("74HC00").select(DelayKind.LOW_TO_HIGH).provenance == "exact"


def test_not_applicable_is_visible_and_does_not_fall_back():
    selected = profile("74HC00").select(DelayKind.Z_TO_HIGH)
    assert selected.delay_ps is None
    assert selected.provenance == "not_applicable"
    assert selected.reason


def test_generic_path_and_default_fallback_provenance_is_visible():
    generic = profile("74HC74").select(DelayKind.LOW_TO_HIGH)
    assert generic.provenance == "generic"
    assert generic.delay_ps == 44_000

    missing = {"status": "missing", "reason": "no polarity-specific value"}
    path_profile = TimingProfile("example", {DelayKind.Z_TO_HIGH: missing}, {}, {"oe_to_q_ns": 7}, 11_000, "model default")
    path = path_profile.select(DelayKind.Z_TO_HIGH, path="oe_to_q_ns")
    assert (path.delay_ps, path.provenance, path.source) == (7_000, "path", "public_timing.paths.oe_to_q_ns")

    default = path_profile.select(DelayKind.Z_TO_HIGH)
    assert (default.delay_ps, default.provenance, default.source) == (11_000, "default", "model default")


def test_all_active_digital_definitions_normalize():
    active = []
    for part in component_ids():
        definition = load_digital_definition(part, required=False)
        if definition is None or definition.get("metadata", {}).get("group") not in {"74xx", "memory"}:
            continue
        active.append(part)
        timing = profile(part)
        assert timing.part == part
        assert set(timing.parameters) == set(DelayKind)
        assert set(timing.constraints) == set(ConstraintKind)
        for kind in DelayKind:
            record = timing.parameters[kind]
            assert record["status"] in {"exact", "generic", "missing", "not_applicable"}
    assert len(active) == 70


def test_constraint_selection_is_conservative_and_source_backed():
    timing = profile("74HC161")
    setup = timing.select_constraint(ConstraintKind.SETUP, path="data_min")
    hold = timing.select_constraint(ConstraintKind.HOLD)
    pulse = timing.select_constraint(ConstraintKind.MINIMUM_PULSE_WIDTH)
    assert (setup.delay_ps, hold.delay_ps, pulse.delay_ps) == (30_000, 0, 16_000)
    assert setup.provenance == "exact"
    assert "setup_before_clock_ns" in setup.source


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print("Components timing profile tests passed")
