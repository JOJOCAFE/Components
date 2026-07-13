#!/usr/bin/env python3
"""Check v1.1 Component-language fixture facts against active compact records.

This intentionally checks no proposed Component syntax.  It prevents fixture
documentation from drifting from the generated Device records that a future
resolver must consume.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "Language" / "fixtures" / "component-v1.1"


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def check_positive_fixture(path: Path, errors: list[str]) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "components.component-fixture@1":
        fail(f"{path.name}: wrong schema", errors)
        return
    source = path.with_name(data.get("source", ""))
    if not source.is_file():
        fail(f"{path.name}: missing declared source {source.name}", errors)
    for record in data.get("library_lock", []):
        resolved_path = ROOT / record["resolved_definition"]
        if not resolved_path.is_file():
            fail(f"{path.name}: missing {record['resolved_definition']}", errors)
            continue
        definition = json.loads(resolved_path.read_text(encoding="utf-8"))
        pins = {(pin["name"], pin["number"], pin["direction"]) for pin in definition.get("pins", [])}
        for expected in record.get("expected_pins", []):
            key = (expected["name"], expected["number"], expected["direction"])
            if key not in pins:
                fail(f"{path.name}: {record['instance']} expected pin {key!r} not in {record['resolved_definition']}", errors)
    for probe in data.get("probes", []):
        if probe.get("read_only") is not True:
            fail(f"{path.name}: probe {probe.get('id')} must be read-only", errors)
    for display in data.get("displays", []):
        if display.get("read_only") is not True:
            fail(f"{path.name}: display {display.get('target')} must be read-only", errors)


def check_negative_fixtures(path: Path, errors: list[str]) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "components.component-negative-fixtures@1":
        fail("negative_cases.json: wrong schema", errors)
    for case in data.get("cases", []):
        if not case.get("id") or not case.get("source_fragment") or not case.get("expected_diagnostic"):
            fail(f"negative_cases.json: incomplete case {case!r}", errors)


def main() -> int:
    errors: list[str] = []
    for fixture in sorted(FIXTURE_ROOT.glob("*.expected.json")):
        check_positive_fixture(fixture, errors)
    check_negative_fixtures(FIXTURE_ROOT / "negative_cases.json", errors)
    if errors:
        print("COMPONENT LANGUAGE FIXTURE CHECK FAIL")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("COMPONENT LANGUAGE FIXTURE CHECK PASS (2 positive, 5 negative fixtures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
