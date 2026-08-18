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


# RV8GR instruction decode table (opcode byte → mnemonic)
_RV8GR_OPCODES = {
    0x00: "NOP",
    0x10: "ADDI", 0x18: "ADD",
    0x90: "SUBI", 0x98: "SUB",
    0x70: "XORI", 0x78: "XOR",
    0x30: "LI",   0x38: "LB",
    0x04: "SB",
    0x02: "BEQ",  0x82: "BNE",
    0x01: "J",
    0x20: "SETPG", 0x28: "SETPG_R",
    0x40: "SETDP",
    0x08: "EI",   0x48: "DI",
}


def _decode_instruction(irh: int, irl: int) -> str:
    """Decode IRH+IRL into a human-readable instruction string."""
    mnemonic = _RV8GR_OPCODES.get(irh)
    if mnemonic is None:
        # Check if it's a forbidden opcode (SRC+STR)
        if (irh & 0x0C) == 0x0C:
            return f"FORBIDDEN ${irh:02X}"
        return f"?${irh:02X}"
    if mnemonic in ("NOP",):
        return mnemonic
    if mnemonic in ("EI", "DI"):
        return mnemonic
    return f"{mnemonic} ${irl:02X}"


def _bus_to_int(value: Any) -> int | str:
    """Convert a bus probe value (list of bits) to an integer."""
    if isinstance(value, list):
        return sum(
            ((b & 1) if isinstance(b, int) else 0) << i
            for i, b in enumerate(value)
        )
    return value


def _execute_body_deferred(session: ComponentRuntimeSession, body: str) -> None:
    """Execute a body block with all drives deferred (no clock edge detection).

    This allows phase signals to be set up and combinational logic to settle
    before latches fire on rising edges.
    """
    import re
    statements = re.findall(r"[^;{}\n]+", body)
    for raw in statements:
        stmt = raw.strip()
        if not stmt or stmt.startswith("//") or stmt.startswith("--"):
            continue
        if stmt.startswith("set "):
            m = re.fullmatch(r"set\s+([^\s=]+)\s*=\s*(.+)", stmt)
            if m:
                target, val_str = m.group(1), m.group(2).strip()
                val = int(val_str, 0) if val_str not in ("Z", "X") else val_str
                session.drive(target, val, defer_clocks=True)
        elif stmt == "settle":
            session.board.settle()


def trace_circuit(
    source: str | Path,
    *,
    steps: int = 12,
    probes: list[str] | None = None,
    reset_name: str = "power_on",
    rom_file: str | Path | None = None,
    rom_data: bytes | None = None,
    annotate: bool = False,
) -> dict[str, Any]:
    """Run a circuit for N clock steps, collecting probe snapshots.

    Args:
        source: path to .component file
        steps: number of clock pulses
        probes: specific probe names (default: all declared observations)
        reset_name: name of reset stimulus block
        rom_file: path to .bin file to preload into ROM
        rom_data: raw bytes to preload into ROM (alternative to rom_file)
        annotate: if True, decode IRH into instruction mnemonics

    Returns:
        {
            "component_id": str,
            "chips": int,
            "probes": [name, ...],
            "steps": [
                {"step": 1, "time_ns": ..., "values": {name: value}, "note": "..."},
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

    # Load ROM from file or raw data
    if rom_file or rom_data:
        _load_rom(session, rom_file=rom_file, rom_data=rom_data)

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

    # Detect phase presets for auto-cycling (T0→T1→T2)
    # Circuits without a ring counter expose phase_t0/phase_t1/phase_t2 inputs
    phase_presets: list[list[dict]] | None = None
    phase_names = ["phase_t0", "phase_t1", "phase_t2"]
    found_phases = []
    for pname in phase_names:
        body = session._get_stimulus_block("input", pname)
        if body:
            found_phases.append(body)
    if len(found_phases) == 3:
        phase_presets = found_phases

    # Collect ROM data for display
    rom_preview: list[int] = []
    for chip in session.chips.values():
        if hasattr(chip, "data") and len(chip.data) >= 16:
            rom_preview = [int(b) for b in chip.data[:16]]
            break

    # Step and collect
    snapshots: list[dict[str, Any]] = []
    for step in range(1, steps + 1):
        # Apply phase preset if available (T0→T1→T2 rotating)
        if phase_presets:
            phase_idx = (step - 1) % 3
            # Drive phase signals with deferred clocks to prevent premature latching.
            # In real hardware: CLK→ring counter→T0 rises→IBUS settles→U5 latches.
            # We simulate this by: set phase signals (defer), settle bus, then fire edges.
            prev_clocks = session._sample_clock_nets()
            _execute_body_deferred(session, phase_presets[phase_idx])
            session.board.settle()
            # Now IBUS/DBUS have settled with the new phase signals.
            # Fire any pending clock edges (T0→U5, T1→U6).
            session._detect_and_fire_clock_edges(prev_clocks)

        # Clock pulse (advances PC counter on rising edge of CLK)
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
                try:
                    raw = session._probe_single(name)
                except Exception:
                    raw = "?"
            values[name] = _bus_to_int(raw) if isinstance(raw, list) else raw

        # Annotation (instruction decode)
        note = ""
        if annotate:
            irh_val = _get_probe_int(session, probe_result, "ir_high", "irh")
            irl_val = _get_probe_int(session, probe_result, "ir_low", "irl")
            if phase_presets:
                phase_idx = (step - 1) % 3
                phase_label = ["T0", "T1", "T2"][phase_idx]
                if phase_idx == 0 and irh_val is not None:
                    mnemonic = _RV8GR_OPCODES.get(irh_val, f"?${irh_val:02X}")
                    note = f"{phase_label}: fetch ${irh_val:02X} ({mnemonic})"
                elif phase_idx == 1 and irl_val is not None:
                    note = f"{phase_label}: fetch ${irl_val:02X}"
                elif phase_idx == 2 and irh_val is not None:
                    note = f"{phase_label}: {_decode_instruction(irh_val, irl_val or 0)}"
            elif irh_val is not None:
                note = _decode_instruction(irh_val, irl_val or 0)

        snap: dict[str, Any] = {
            "step": step,
            "time_ns": session.board.time_ns,
            "values": values,
        }
        if note:
            snap["note"] = note
        snapshots.append(snap)

    return {
        "component_id": resolved.get("component_id", path.stem),
        "chips": len(session.chips),
        "skipped": len(session.skipped_instances),
        "probes": collect,
        "steps": snapshots,
        "rom_data": rom_preview,
    }


def _load_rom(session: ComponentRuntimeSession, *,
              rom_file: str | Path | None = None,
              rom_data: bytes | None = None) -> None:
    """Load binary data into the first ROM/memory chip found."""
    data = rom_data
    if rom_file and data is None:
        data = Path(rom_file).read_bytes()
    if data is None:
        return
    # Find a chip with a .data attribute (ROM or RAM)
    for chip in session.chips.values():
        if hasattr(chip, "data") and len(chip.data) >= 1024:
            for i, b in enumerate(data):
                if i < len(chip.data):
                    chip.data[i] = b
            break


def _get_probe_int(session: ComponentRuntimeSession, probe_result: dict,
                   *names: str) -> int | None:
    """Get an integer value from probes, trying multiple names."""
    for name in names:
        raw = probe_result.get(name)
        if raw is None:
            try:
                raw = session._probe_single(name)
            except Exception:
                continue
        if isinstance(raw, list):
            return sum(((b & 1) if isinstance(b, int) else 0) << i for i, b in enumerate(raw))
        if isinstance(raw, int):
            return raw
    return None
