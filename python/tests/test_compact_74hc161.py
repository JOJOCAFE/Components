"""Lossless clocked-timing proof for the non-active 74HC161 compact pilot."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from chiplib.compact_definition import resolve_compact_definition
from chiplib.db import validate_digital_definition


ROOT = Path(__file__).resolve().parents[2]


class Compact74HC161TimingTests(unittest.TestCase):
    def test_clocked_pilot_resolves_to_the_existing_timing_contract(self) -> None:
        base = ROOT / "lib" / "standard" / "74xx" / "74HC161"
        source_path = base / "definition" / "definition.json"
        if json.loads(source_path.read_text(encoding="utf-8")).get("schema") != "db.component.digital.compact":
            source_path = base / "definition" / "compact.pilot.json"
        compact = json.loads(source_path.read_text(encoding="utf-8"))
        evidence_path = base / "generated" / "resolved.json" if source_path.name == "definition.json" else base / "definition" / "definition.json"
        current = json.loads(evidence_path.read_text(encoding="utf-8"))
        resolved = resolve_compact_definition(compact, base)

        self.assertTrue(validate_digital_definition(resolved)["ok"])
        # These assertions deliberately cover all five switching rows and every
        # setup/hold/pulse/frequency source value via the canonical contracts.
        self.assertEqual(resolved["timing"], current["timing"])
        self.assertEqual(resolved["definition_layers"]["timing"], current["definition_layers"]["timing"])
        self.assertEqual(resolved["pins"], current["pins"])
        self.assertEqual(resolved["logic"], current["logic"])


if __name__ == "__main__":
    unittest.main()
