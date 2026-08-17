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


def _format_value(val: Any) -> str:
    """Format a single probe value for display."""
    if val == "Z" or val == 2:
        return "Z"
    if val == "X" or val == 3:
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
