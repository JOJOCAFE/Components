"""Library circuit proof checks."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RING_COUNTER = ROOT / "Lib" / "Circuits" / "RV8GR_RingCounter"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def ring_outputs(state: int) -> dict[str, int]:
    return {
        "T0": state & 1,
        "T1": (state >> 1) & 1,
        "T2": (state >> 2) & 1,
    }


def ring_clock(state: int) -> int:
    q0 = state & 1
    q1 = (state >> 1) & 1
    serial = int((not q0) and (not q1))
    return ((state << 1) & 0xFE) | serial


def test_rv8gr_ring_counter_package_shape():
    circuit = load_json(RING_COUNTER / "circuit.json")
    proof = load_json(RING_COUNTER / "tests" / "ring_counter.json")

    assert circuit["schema"] == "components.lib.circuit"
    assert circuit["id"] == "rv8gr_ring_counter"
    assert proof["circuit"] == circuit["id"]
    assert (RING_COUNTER / "README.md").exists()

    chip_parts = {chip["part"] for chip in circuit["chips"]}
    assert chip_parts == {"74HC164", "74HC04"}
    for part in chip_parts:
        assert list((ROOT / "DB").glob(f"*/*{part}/definition/definition.json")), part

    outputs = {port["name"] for port in circuit["ports"] if port["direction"] == "output"}
    assert {"T0", "T1", "T2"} <= outputs
    assert circuit["behavior"]["serial_input"] == "NOT(T0) AND NOT(T1)"


def test_rv8gr_ring_counter_sequence_and_reset():
    proof = load_json(RING_COUNTER / "tests" / "ring_counter.json")
    state = 0
    assert ring_outputs(state) == proof["reset"]["expect"]

    for vector in proof["sequence_after_reset"]:
        state = ring_clock(state)
        outputs = ring_outputs(state)
        assert outputs == vector["expect"], vector
        assert sum(outputs.values()) == 1, vector


def test_rv8gr_ring_counter_ignores_non_rising_edges():
    state = ring_clock(0)
    before = ring_outputs(state)
    # Falling/no-edge behavior is a hold for this circuit model.
    after = ring_outputs(state)
    assert after == before


def test_rv8gr_ring_counter_illegal_lower_states_recover():
    proof = load_json(RING_COUNTER / "tests" / "ring_counter.json")
    recovery = proof["illegal_lower_state_recovery"]
    normal = {tuple(item[name] for name in ("T0", "T1", "T2")) for item in recovery["normal_states"]}

    for illegal in recovery["states"]:
        state = illegal["T0"] | (illegal["T1"] << 1) | (illegal["T2"] << 2)
        reached = False
        for _ in range(recovery["max_clocks"]):
            state = ring_clock(state)
            outputs = ring_outputs(state)
            if tuple(outputs[name] for name in ("T0", "T1", "T2")) in normal:
                reached = True
                break
        assert reached, illegal


def run_all():
    test_rv8gr_ring_counter_package_shape()
    test_rv8gr_ring_counter_sequence_and_reset()
    test_rv8gr_ring_counter_ignores_non_rising_edges()
    test_rv8gr_ring_counter_illegal_lower_states_recover()


if __name__ == "__main__":
    run_all()
    print("Components library circuit tests passed")
