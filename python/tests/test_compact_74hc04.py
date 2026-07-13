"""Lossless activation proof for the 74HC04 compact Device source."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from chiplib.compact_definition import resolve_compact_definition
from chiplib.db import validate_digital_definition


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    "pins", "logic", "timing", "verification", "datasheet", "evidence",
    "status", "generation", "definition_layers", "metadata", "package",
    "procurement",
)


class Compact74HC04Tests(unittest.TestCase):
    def test_active_source_resolves_losslessly_to_generated_runtime(self) -> None:
        base = ROOT / "lib" / "standard" / "74xx" / "74HC04"
        source = json.loads((base / "definition" / "definition.json").read_text(encoding="utf-8"))
        generated = json.loads((base / "generated" / "resolved.json").read_text(encoding="utf-8"))
        resolved = resolve_compact_definition(source, base)

        self.assertTrue(validate_digital_definition(resolved)["ok"])
        for key in CONTRACT:
            self.assertEqual(resolved[key], generated[key], key)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
