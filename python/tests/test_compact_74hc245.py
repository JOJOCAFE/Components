"""Lossless high-Z timing proof for the non-active 74HC245 compact pilot."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from chiplib.compact_definition import resolve_compact_definition
from chiplib.db import validate_digital_definition


ROOT = Path(__file__).resolve().parents[2]


class Compact74HC245TimingTests(unittest.TestCase):
    def test_tri_state_pilot_preserves_all_live_timing_rows(self) -> None:
        base = ROOT / "lib" / "standard" / "74xx" / "74HC245"
        source_path = base / "definition" / "definition.json"
        if json.loads(source_path.read_text(encoding="utf-8")).get("schema") != "db.component.digital.compact":
            source_path = base / "definition" / "compact.pilot.json"
        compact = json.loads(source_path.read_text(encoding="utf-8"))
        evidence_path = base / "generated" / "resolved.json" if source_path.name == "definition.json" else base / "definition" / "definition.json"
        current = json.loads(evidence_path.read_text(encoding="utf-8"))
        resolved = resolve_compact_definition(compact, base)

        self.assertTrue(validate_digital_definition(resolved)["ok"])
        # This covers both transfer directions, enable-to-drive, disable-to-Z,
        # transition time, and every voltage/max column; nothing is inferred
        # from an ordinary push-pull delay.
        self.assertEqual(resolved["timing"], current["timing"])
        self.assertEqual(resolved["definition_layers"]["timing"], current["definition_layers"]["timing"])
        self.assertEqual(resolved["pins"], current["pins"])
        self.assertEqual(resolved["logic"], current["logic"])


if __name__ == "__main__":
    unittest.main()
