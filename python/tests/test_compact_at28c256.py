"""Lossless asynchronous-memory proof for the active AT28C256 Device source."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from chiplib.db import validate_digital_definition
from chiplib.memory_definition import resolve_compact_memory_definition, validate_compact_memory_definition


ROOT = Path(__file__).resolve().parents[2]


class CompactAT28C256Tests(unittest.TestCase):
    def test_active_async_memory_source_resolves_to_its_canonical_contract(self) -> None:
        base = ROOT / "lib" / "standard" / "memory" / "AT28C256"
        source = json.loads((base / "definition" / "definition.json").read_text(encoding="utf-8"))
        current = json.loads((base / "generated" / "resolved.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_compact_memory_definition(source), [])
        resolved = resolve_compact_memory_definition(source, base)

        self.assertTrue(validate_digital_definition(resolved)["ok"])
        for key in ("pins", "logic", "timing", "verification", "datasheet", "evidence", "status", "procurement", "generation", "metadata", "package"):
            self.assertEqual(resolved[key], current[key], key)
        self.assertEqual(resolved["definition_layers"], current["definition_layers"])
        self.assertEqual(resolved, current)
        self.assertEqual(resolved["authoring"]["schema"], "db.component.memory.compact")


if __name__ == "__main__":
    unittest.main()
