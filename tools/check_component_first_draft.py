#!/usr/bin/env python3
"""Check factual invariants in first-draft Component language fixtures.

This is intentionally not a parser.  It protects the readable proposal and
its canonical resolved JSON target from drifting away from active resolved
Device facts before parser/resolver work begins.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "Language" / "fixtures" / "component-first-draft"


def add(error_list: list[str], message: str) -> None:
    error_list.append(message)


def pin_set(path: Path) -> set[tuple[str, int, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {(pin["name"], pin["number"], pin["direction"]) for pin in data["pins"]}


def main() -> int:
    errors: list[str] = []
    counter_source = (FIXTURES / "counter_first_draft.component").read_text(encoding="utf-8")
    mux_source = (FIXTURES / "mux_first_draft.component").read_text(encoding="utf-8")
    for source, required in (
        (counter_source, ("device Counter is digital.74HC161;", "probe count_value, count;", "watch least_bit, count[0];", "display count_value as waveform", "test reset_then_count")),
        (mux_source, ("device Mux is digital.74HC157;", "connect a[0] -> Mux.1A;", "connect Mux.4Y -> y[3];", "display output as value")),
    ):
        for token in required:
            if token not in source:
                add(errors, f"source missing required first-draft form: {token}")

    target = json.loads((FIXTURES / "counter_first_draft.resolved.json").read_text(encoding="utf-8"))
    if target.get("schema") != "components.resolved-component@1":
        add(errors, "resolved target has wrong schema")
    if any(edge.get("from") == "count" or edge.get("to") == "count" for edge in target.get("edges", [])):
        add(errors, "resolved target must scalarize bus edges")
    if not all(item.get("read_only") is True for item in target.get("observations", []) + target.get("display_bindings", [])):
        add(errors, "observations and display bindings must be read-only")
    if not all(test.get("bounded") is True for test in target.get("tests", [])):
        add(errors, "tests must be bounded")

    expected = {
        "Clock": ("lib/standard/virtual/ClockSource/generated/resolved.json", [("CLK", 1, "output")]),
        "Counter": ("lib/standard/74xx/74HC161/generated/resolved.json", [("/CLR", 1, "input"), ("CLK", 2, "input"), ("QA", 14, "output"), ("VCC", 16, "power")]),
        "Observe": ("lib/standard/virtual/Probe/generated/resolved.json", [("IN", 1, "input")]),
    }
    locks = {entry.get("instance"): entry for entry in target.get("library_lock", [])}
    for instance, (relative, facts) in expected.items():
        lock = locks.get(instance)
        if not lock or lock.get("resolved_definition") != relative:
            add(errors, f"{instance}: wrong or absent library lock")
            continue
        available = pin_set(ROOT / relative)
        for fact in facts:
            if fact not in available:
                add(errors, f"{instance}: resolved Device lacks pin fact {fact!r}")

    if errors:
        print("COMPONENT FIRST-DRAFT CHECK FAIL")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("COMPONENT FIRST-DRAFT CHECK PASS (2 source examples, 1 resolved target)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
