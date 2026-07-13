#!/usr/bin/env python3
"""Prove the RV8GR legacy memory bridge is lossless before source conversion."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from chiplib.legacy_compact_adapter import legacy_memory_to_compact_candidate, non_derived_view  # noqa: E402
from chiplib.memory_definition import resolve_compact_memory_definition, validate_compact_memory_definition  # noqa: E402

PARTS = ("62256", "AS6C62256", "CY7C199")


def source_for(part: str) -> Path:
    return ROOT / "lib" / "standard" / "memory" / part / "definition" / "definition.json"


def main() -> int:
    failures: list[str] = []
    for part in PARTS:
        source = source_for(part)
        legacy = json.loads(source.read_text(encoding="utf-8"))
        try:
            candidate = legacy_memory_to_compact_candidate(legacy)
            errors = validate_compact_memory_definition(candidate)
            if errors:
                raise ValueError("; ".join(errors))
            resolved = resolve_compact_memory_definition(candidate, source.parents[1])
        except (KeyError, TypeError, ValueError) as error:
            failures.append(f"{part}: bridge failed: {error}")
            continue
        if non_derived_view(resolved) != non_derived_view(legacy):
            failures.append(f"{part}: non-derived canonical fields differ after compact resolve")
            continue
        print(f"{part}: LOSSLESS")
    if failures:
        print("RV8GR LEGACY MEMORY COMPACT EQUIVALENCE FAILED", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"RV8GR LEGACY MEMORY COMPACT EQUIVALENCE PASS ({len(PARTS)} memory records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
