#!/usr/bin/env python3
"""Audit, but never rewrite, the RV8GR compact-definition migration set.

The board uses sixteen physical part types.  The readiness set deliberately
adds the two compatible SRAM options used by the RV8GR memory contract.  This
script makes the 18-part boundary explicit and reports whether each package
has the artifacts required before its legacy definition may be replaced by a
compact source:

* a compact human source and a fresh generated resolved record;
* the existing standalone Python and Verilog models plus the five package
  vector categories; and
* a presentation Resource only when one was intentionally authored.

It is an inventory gate, not a converter.  In particular it never silently
collapses datasheet timing paths into a default delay.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from chiplib.compact_definition import COMPACT_SCHEMA  # noqa: E402
from chiplib.legacy_compact_adapter import (  # noqa: E402
    legacy_memory_to_compact_candidate,
    legacy_to_compact_candidate,
    non_derived_view,
)
from chiplib.memory_definition import MEMORY_SCHEMA  # noqa: E402
from chiplib.compact_definition import resolve_compact_definition  # noqa: E402
from chiplib.memory_definition import resolve_compact_memory_definition  # noqa: E402


# 16 physical board-used types plus the two SRAM alternatives named by the
# RV8GR memory contract.  Keep this separate from virtual test helpers.
RV8GR_READY_PARTS = (
    "74HC00", "74HC04", "74HC21", "74HC32", "74HC74", "74HC86",
    "74HC157", "74HC161", "74HC164", "74HC245", "74HC283", "74HC541",
    "74HC574", "74HC688", "62256", "AT28C256", "AS6C62256", "CY7C199",
)
COMPACT_SCHEMAS = {COMPACT_SCHEMA, MEMORY_SCHEMA}
REQUIRED_PACKAGE_FILES = (
    "simulation/model.py", "simulation/model.v", "simulation/netlist.json",
    "tests/truth_table.json", "tests/timing.json", "tests/propagation.json",
    "tests/tri_state.json", "tests/bus_fight.json",
)


def package_for(part: str) -> Path:
    candidates = list((ROOT / "lib" / "standard").glob(f"**/{part}/definition/definition.json"))
    if len(candidates) != 1:
        raise ValueError(f"{part}: expected one definition source, found {len(candidates)}")
    return candidates[0].parents[1]


def audit_part(part: str) -> tuple[str, list[str]]:
    package = package_for(part)
    source = package / "definition" / "definition.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    compact = data.get("schema") in COMPACT_SCHEMAS
    missing = [str(path) for path in REQUIRED_PACKAGE_FILES if not (package / path).is_file()]
    if compact and not (package / "generated" / "resolved.json").is_file():
        missing.append("generated/resolved.json")
    if compact:
        state = "compact-ready" if not missing else "compact-incomplete"
    else:
        try:
            if data.get("metadata", {}).get("group") == "memory":
                resolved = resolve_compact_memory_definition(
                    legacy_memory_to_compact_candidate(data), package
                )
            else:
                resolved = resolve_compact_definition(legacy_to_compact_candidate(data), package)
            state = "legacy-bridge-ready" if non_derived_view(resolved) == non_derived_view(data) else "legacy-mismatch"
        except (KeyError, TypeError, ValueError):
            state = "legacy-blocked"
    return state, missing


def main() -> int:
    print("part       state              package artifacts missing")
    bridge_ready = 0
    blocked = 0
    for part in RV8GR_READY_PARTS:
        state, missing = audit_part(part)
        if state == "legacy-bridge-ready":
            bridge_ready += 1
        if state in {"legacy-blocked", "legacy-mismatch"}:
            blocked += 1
        print(f"{part:<10} {state:<18} {', '.join(missing) if missing else '-'}")
    compact_ready = len(RV8GR_READY_PARTS) - bridge_ready - blocked
    print(f"\nRV8GR definition migration audit: {compact_ready} compact-ready, {bridge_ready} legacy-bridge-ready, {blocked} legacy-blocked.")
    print("Legacy-bridge-ready means the lossless adapter passed but the human compact source and generated record are not yet committed. Legacy-blocked means extraction still failed; neither state is a runtime failure.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
