#!/usr/bin/env python3
"""Prove the RV8GR legacy-definition bridge is lossless before conversion."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from chiplib.compact_definition import resolve_compact_definition  # noqa: E402
from chiplib.legacy_compact_adapter import legacy_to_compact_candidate, non_derived_view  # noqa: E402

PARTS = ("74HC21", "74HC32", "74HC74", "74HC86", "74HC164", "74HC283", "74HC541", "74HC688")


def source_for(part: str) -> Path:
    matches = list((ROOT / "lib" / "standard").glob(f"**/{part}/definition/definition.json"))
    if len(matches) != 1:
        raise ValueError(f"{part}: expected exactly one definition source")
    return matches[0]


def main() -> int:
    failures: list[str] = []
    for part in PARTS:
        source = source_for(part)
        legacy = json.loads(source.read_text(encoding="utf-8"))
        try:
            candidate = legacy_to_compact_candidate(legacy)
            resolved = resolve_compact_definition(candidate, source.parents[1])
        except (KeyError, TypeError, ValueError) as error:
            failures.append(f"{part}: bridge failed: {error}")
            continue
        if non_derived_view(resolved) != non_derived_view(legacy):
            failures.append(f"{part}: non-derived canonical fields differ after compact resolve")
            continue
        print(f"{part}: LOSSLESS")
    if failures:
        print("RV8GR LEGACY COMPACT EQUIVALENCE FAILED", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"RV8GR LEGACY COMPACT EQUIVALENCE PASS ({len(PARTS)} digital records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
