"""Trace output formatters — table, JSON, CSV.

Each formatter takes the trace result dict and returns a string.
"""
from __future__ import annotations

import json
from typing import Any


def format_table(trace: dict[str, Any]) -> str:
    """Format trace as an ASCII table."""
    lines: list[str] = []
    component_id = trace["component_id"]
    chips = trace["chips"]
    probes = trace["probes"]
    steps = trace["steps"]
    rom_data = trace.get("rom_data", [])

    # Header
    lines.append(f"{component_id} ({chips} chips)")
    if rom_data:
        rom_hex = " ".join(f"{b:02X}" for b in rom_data[:16])
        lines.append(f"ROM: [{rom_hex}]")
    lines.append("=" * 60)

    # Determine column widths
    col_widths: dict[str, int] = {}
    for name in probes:
        max_val_width = len(name)
        for snap in steps:
            val = snap["values"].get(name, "?")
            formatted = _format_value(val)
            max_val_width = max(max_val_width, len(formatted))
        col_widths[name] = max(max_val_width, 4)

    # Check if any step has annotations
    has_notes = any(snap.get("note") for snap in steps)
    note_width = 0
    if has_notes:
        note_width = max(len(snap.get("note", "")) for snap in steps)
        note_width = max(note_width, 4)

    # Table header
    step_col = " CLK"
    header = f"{step_col} |"
    for name in probes:
        header += f" {name:>{col_widths[name]}} |"
    if has_notes:
        header += f" {'note':<{note_width}} |"
    lines.append(header)

    # Separator
    sep = "-" * len(step_col) + "-+"
    for name in probes:
        sep += "-" * (col_widths[name] + 2) + "+"
    if has_notes:
        sep += "-" * (note_width + 2) + "+"
    lines.append(sep)

    # Rows
    for snap in steps:
        step = snap["step"]
        row = f" ↑{step:>2} |"
        for name in probes:
            val = snap["values"].get(name, "?")
            formatted = _format_value(val)
            row += f" {formatted:>{col_widths[name]}} |"
        if has_notes:
            note = snap.get("note", "")
            row += f" {note:<{note_width}} |"
        lines.append(row)

    lines.append("=" * 60)
    return "\n".join(lines)


def format_json(trace: dict[str, Any]) -> str:
    """Format trace as JSON (AI-friendly)."""
    return json.dumps(trace, indent=2, default=str)


def format_csv(trace: dict[str, Any]) -> str:
    """Format trace as CSV."""
    probes = trace["probes"]
    steps = trace["steps"]
    lines: list[str] = []

    # Header
    lines.append(",".join(["step", "time_ns"] + probes))

    # Rows
    for snap in steps:
        row = [str(snap["step"]), str(snap["time_ns"])]
        for name in probes:
            val = snap["values"].get(name, "")
            row.append(_format_value(val))
        lines.append(",".join(row))

    return "\n".join(lines)


def diff_traces(actual: dict[str, Any], expected: dict[str, Any]) -> list[dict[str, Any]]:
    """Compare two trace results step-by-step, return list of differences.

    Args:
        actual: trace result from trace_circuit()
        expected: golden reference trace (same format, loaded from JSON)

    Returns:
        List of dicts: {'step': int, 'probe': str, 'expected': Any, 'actual': Any}
    """
    diffs: list[dict[str, Any]] = []
    actual_steps = actual.get("steps", [])
    expected_steps = expected.get("steps", [])
    probe_names = actual.get("probes", [])

    for i, (a_step, e_step) in enumerate(zip(actual_steps, expected_steps)):
        for probe in probe_names:
            a_val = a_step.get("values", {}).get(probe)
            e_val = e_step.get("values", {}).get(probe)
            if a_val != e_val:
                diffs.append({
                    "step": i + 1,
                    "probe": probe,
                    "expected": e_val,
                    "actual": a_val,
                })

    # Check for step count mismatch
    if len(actual_steps) != len(expected_steps):
        diffs.append({
            "step": 0,
            "probe": "_step_count",
            "expected": len(expected_steps),
            "actual": len(actual_steps),
        })

    return diffs


def format_diff(diffs: list[dict[str, Any]]) -> str:
    """Format diff results into a human-readable report.

    Returns:
        Formatted string like:
            DIFF: 3 differences found
              Step 4, ac: expected 0x42, got 0x00
              Step 5, z_flag: expected 1, got 0
    """
    if not diffs:
        return "OK: traces match"

    lines: list[str] = []
    lines.append(f"DIFF: {len(diffs)} difference{'s' if len(diffs) != 1 else ''} found")
    for d in diffs:
        step = d["step"]
        probe = d["probe"]
        expected = d["expected"]
        actual = d["actual"]
        if probe == "_step_count":
            lines.append(f"  Step count mismatch: expected {expected}, got {actual}")
        else:
            e_str, a_str = _format_diff_pair(expected, actual)
            lines.append(f"  Step {step}, {probe}: expected {e_str}, got {a_str}")
    return "\n".join(lines)


def _format_diff_pair(expected: Any, actual: Any) -> tuple[str, str]:
    """Format expected and actual values as a consistent pair."""
    # Both must be int to use hex formatting
    if isinstance(expected, int) and isinstance(actual, int):
        max_val = max(abs(expected), abs(actual))
        if max_val <= 1:
            return str(expected), str(actual)
        # Determine hex width from the larger value
        if max_val <= 0xFF:
            return f"0x{expected:02X}", f"0x{actual:02X}"
        if max_val <= 0xFFFF:
            return f"0x{expected:04X}", f"0x{actual:04X}"
        return f"0x{expected:X}", f"0x{actual:X}"
    # Fallback: format independently
    return _format_diff_value(expected), _format_diff_value(actual)


def _format_diff_value(val: Any) -> str:
    """Format a value for diff output with hex prefix."""
    if val is None:
        return "None"
    if isinstance(val, int):
        if 0 <= val <= 1:
            return str(val)
        return f"0x{val:02X}"
    return str(val)


def _format_value(val: Any) -> str:
    """Format a single probe value for display."""
    if val == "Z":
        return "Z"
    if val == "X":
        return "X"
    if isinstance(val, int):
        if val < 0:
            return str(val)
        if val <= 1:
            return str(val)
        if val <= 0xFF:
            return f"{val:02X}"
        if val <= 0xFFFF:
            return f"{val:04X}"
        return f"{val:X}"
    if isinstance(val, str):
        return val
    return str(val)
