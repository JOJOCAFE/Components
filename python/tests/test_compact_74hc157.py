"""Lossless multi-path timing proof for the non-active 74HC157 pilot."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from chiplib.compact_definition import resolve_compact_definition
from chiplib.db import validate_digital_definition


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ("pins", "logic", "timing", "verification", "datasheet", "evidence", "status", "generation", "definition_layers", "procurement")


class Compact74HC157Tests(unittest.TestCase):
    def test_multipath_pilot_is_lossless_for_the_live_contract(self) -> None:
        base = ROOT / "lib" / "standard" / "74xx" / "74HC157"
        source_path = base / "definition" / "definition.json"
        if json.loads(source_path.read_text(encoding="utf-8")).get("schema") != "db.component.digital.compact":
            source_path = base / "definition" / "compact.pilot.json"
        compact = json.loads(source_path.read_text(encoding="utf-8"))
        evidence_path = base / "generated" / "resolved.json" if source_path.name == "definition.json" else base / "definition" / "definition.json"
        current = json.loads(evidence_path.read_text(encoding="utf-8"))
        resolved = resolve_compact_definition(compact, base)

        self.assertTrue(validate_digital_definition(resolved)["ok"])
        for key in CONTRACT:
            self.assertEqual(resolved[key], current[key], key)


if __name__ == "__main__":
    unittest.main()
