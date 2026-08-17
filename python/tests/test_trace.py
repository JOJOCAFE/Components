"""Tests for the CLI trace viewer."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from chiplib.trace import trace_circuit
from chiplib.trace_format import format_table, format_json, format_csv


ROOT = Path(__file__).resolve().parent.parent.parent
CIRCUITS = ROOT / "examples" / "circuits"


def test_ring_counter_phases():
    """Ring counter produces T0→T1→T2→T0→T1→T2."""
    result = trace_circuit(
        CIRCUITS / "RV8GR_RingCounter" / "circuit.component",
        steps=6,
        probes=["phase_t0", "phase_t1", "phase_t2"],
    )
    assert result["component_id"] == "RV8GR_RingCounter"
    assert result["chips"] == 2
    assert len(result["steps"]) == 6

    expected = [
        {"phase_t0": 1, "phase_t1": 0, "phase_t2": 0},
        {"phase_t0": 0, "phase_t1": 1, "phase_t2": 0},
        {"phase_t0": 0, "phase_t1": 0, "phase_t2": 1},
        {"phase_t0": 1, "phase_t1": 0, "phase_t2": 0},
        {"phase_t0": 0, "phase_t1": 1, "phase_t2": 0},
        {"phase_t0": 0, "phase_t1": 0, "phase_t2": 1},
    ]
    for i, step in enumerate(result["steps"]):
        assert step["values"] == expected[i], f"step {i+1}: {step['values']} != {expected[i]}"


def test_fetch_cycle_rom_data():
    """FetchCycleTrace shows ROM data on DBUS/IBUS."""
    result = trace_circuit(
        CIRCUITS / "RV8GR_FetchCycleTrace" / "circuit.component",
        steps=1,
        probes=["dbus_data", "ibus_data"],
    )
    assert result["chips"] >= 5
    assert result["rom_data"][:2] == [0x30, 0x42]
    # ROM outputs $30 at address 0 (DBUS and IBUS via U7)
    step1 = result["steps"][0]["values"]
    assert step1["dbus_data"] == 0x30
    assert step1["ibus_data"] == 0x30


def test_table_format():
    """Table formatter produces readable output."""
    result = trace_circuit(
        CIRCUITS / "RV8GR_RingCounter" / "circuit.component",
        steps=3,
        probes=["phase_t0", "phase_t1", "phase_t2"],
    )
    table = format_table(result)
    assert "RV8GR_RingCounter" in table
    assert "phase_t0" in table
    assert "↑ 1" in table
    assert "↑ 3" in table


def test_json_format():
    """JSON formatter produces valid, parseable JSON."""
    result = trace_circuit(
        CIRCUITS / "RV8GR_RingCounter" / "circuit.component",
        steps=2,
    )
    output = format_json(result)
    parsed = json.loads(output)
    assert parsed["component_id"] == "RV8GR_RingCounter"
    assert len(parsed["steps"]) == 2


def test_csv_format():
    """CSV formatter produces parseable output."""
    result = trace_circuit(
        CIRCUITS / "RV8GR_RingCounter" / "circuit.component",
        steps=2,
        probes=["phase_t0", "phase_t1", "phase_t2"],
    )
    output = format_csv(result)
    lines = output.strip().split("\n")
    assert lines[0] == "step,time_ns,phase_t0,phase_t1,phase_t2"
    assert len(lines) == 3  # header + 2 rows


def test_all_circuits_trace():
    """Every circuit with a clock can produce at least 1 step without error."""
    errors = []
    for component_file in sorted(CIRCUITS.glob("*/circuit.component")):
        try:
            result = trace_circuit(component_file, steps=1)
            assert len(result["steps"]) == 1
        except Exception as e:
            if "no clock" in str(e):
                continue  # circuits without clocks can't be traced
            errors.append(f"{component_file.parent.name}: {e}")
    assert not errors, f"Trace failed for: {errors}"


if __name__ == "__main__":
    test_ring_counter_phases()
    print("✓ ring_counter_phases")
    test_fetch_cycle_rom_data()
    print("✓ fetch_cycle_rom_data")
    test_table_format()
    print("✓ table_format")
    test_json_format()
    print("✓ json_format")
    test_csv_format()
    print("✓ csv_format")
    test_all_circuits_trace()
    print("✓ all_circuits_trace")
    print("\nComponents trace tests passed")
