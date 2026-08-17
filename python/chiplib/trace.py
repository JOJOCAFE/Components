"""Trace engine — clock a circuit and collect probe snapshots per step.

Usage:
    from chiplib.trace import trace_circuit
    snapshots = trace_circuit("path/to/circuit.component", steps=6)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .component_language import parse_component_file, resolve_component
from .component_runtime import ComponentRuntimeSession, ComponentRuntimeError


def _bus_to_int(value: Any) -> int | str:
    """Convert a bus probe value (list of bits) to an integer."""
    if isinstance(value, list):
        return sum(
            ((b & 1) if isinstance(b, int) else 0) << i
            for i, b in enumerate(value)
        )
    return value


def trace_circuit(
    source: str | Path,
    *,
    steps: int = 12,
    probes: list[str] | None = None,
    reset_name: str = "power_on",
) -> dict[str, Any]:
    """Run a circuit for N clock steps, collecting probe snapshots.

    Returns:
        {
            "component_id": str,
            "chips": int,
            "probes": [name, ...],
            "steps": [
                {"step": 1, "time_ns": ..., "values": {name: value, ...}},
                ...
            ],
            "rom_data": [first 16 bytes if ROM present],
        }
    """
    path = Path(source)
    ast = parse_component_file(path)
    if not ast.get("ok"):
        raise ComponentRuntimeError(
            f"parse failed: {ast.get('diagnostics', [])}"
        )

    resolved = resolve_component(ast)
    if not resolved or not resolved.get("ok"):
        raise ComponentRuntimeError(
            f"resolve failed: {resolved.get('diagnostics', []) if resolved else 'None'}"
        )

    session = ComponentRuntimeSession(resolved)

    # Determine which probes to collect
    available_probes = [
        obs["id"] for obs in resolved.get("observations", [])
    ]

    if probes:
        collect = [p for p in probes if p in available_probes or p in
                   {b["id"] for b in resolved.get("buses", [])} |
                   {n["id"] for n in resolved.get("nets", [])}]
    else:
        collect = available_probes

    # Find the clock
    clocks = resolved.get("clocks", [])
    if not clocks:
        raise ComponentRuntimeError("circuit has no clock declaration")
    clock_endpoint = clocks[0]["endpoint"]

    # Execute reset if available
    reset_body = session._get_stimulus_block("reset", reset_name)
    if reset_body:
        session._execute_body(reset_body, "trace_reset")

    # Collect ROM data if present
    rom_data: list[int] = []
    for chip in session.chips.values():
        if hasattr(chip, "data") and len(chip.data) >= 16:
            rom_data = [int(b) for b in chip.data[:16]]
            break

    # Step and collect
    snapshots: list[dict[str, Any]] = []
    for step in range(1, steps + 1):
        # Clock pulse
        session.drive(clock_endpoint, 0)
        session.drive(clock_endpoint, 1)
        session.board.time_ns += 1
        session.board.settle()
        session.drive(clock_endpoint, 0)
        session.board.settle()

        # Probe
        probe_result = session.probe()["probes"]
        values: dict[str, Any] = {}
        for name in collect:
            raw = probe_result.get(name)
            if raw is None:
                # Try direct probe
                try:
                    raw = session._probe_single(name)
                except Exception:
                    raw = "?"
            values[name] = _bus_to_int(raw) if isinstance(raw, list) else raw

        snapshots.append({
            "step": step,
            "time_ns": session.board.time_ns,
            "values": values,
        })

    return {
        "component_id": resolved.get("component_id", path.stem),
        "chips": len(session.chips),
        "skipped": len(session.skipped_instances),
        "probes": collect,
        "steps": snapshots,
        "rom_data": rom_data,
    }
