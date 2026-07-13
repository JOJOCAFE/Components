#!/usr/bin/env python3
"""Keep the First-Draft example-circuit coverage audit complete and honest."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "Language/fixtures/component-first-draft/examples-circuits-coverage.json"
EXAMPLES = ROOT / "examples/circuits"
VALID = {
    "core_now", "later_component_profile", "operation", "board",
    "existing_compatibility_only", "unsupported",
}


def audited_sources() -> set[str]:
    return {
        path.relative_to(ROOT).as_posix()
        for path in EXAMPLES.rglob("*.json")
        if path.parent == EXAMPLES or path.name == "circuit.json"
    }


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    errors: list[str] = []
    if report.get("schema") != "components.component-first-draft-coverage@1":
        errors.append("wrong report schema")
    files = report.get("files")
    if not isinstance(files, dict):
        errors.append("report files must be an object")
        files = {}
    actual = audited_sources()
    recorded = set(files)
    if actual != recorded:
        missing = sorted(actual - recorded)
        extra = sorted(recorded - actual)
        if missing:
            errors.append("unaudited sources: " + ", ".join(missing))
        if extra:
            errors.append("nonexistent recorded sources: " + ", ".join(extra))
    for path, entry in files.items():
        if not isinstance(entry, dict):
            errors.append(f"{path}: report entry must be an object")
            continue
        classifications = [entry[key] for key in ("topology", "execution", "classification") if key in entry]
        if not classifications:
            errors.append(f"{path}: needs a classification")
        for value in classifications:
            if value not in VALID:
                errors.append(f"{path}: invalid classification {value!r}")
        if entry.get("kind") in {"legacy_topology", "leaf_package", "composite_package"}:
            if not entry.get("blockers"):
                errors.append(f"{path}: topology audit needs explicit blockers")
    if len(actual) != 33:
        errors.append(f"scope changed: expected 33 sources, found {len(actual)}")
    if errors:
        print("COMPONENT EXAMPLES COVERAGE CHECK FAIL")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("COMPONENT EXAMPLES COVERAGE CHECK PASS (33 sources, audit only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
