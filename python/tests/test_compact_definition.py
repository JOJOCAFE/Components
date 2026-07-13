"""Regression tests for additive human-definition resolution."""

from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from chiplib.compact_definition import COMPACT_SCHEMA, resolve_compact_definition
from chiplib.db import validate_digital_definition


ROOT = Path(__file__).resolve().parents[2]


class CompactDefinitionTests(unittest.TestCase):
    def test_human_facing_pin_map_resolves_to_the_stable_runtime_contract(self) -> None:
        source = {
            "schema": COMPACT_SCHEMA,
            "version": "0.2",
            "profile": "74hc.digital@0.2",
            "part": "CompactNand",
            "about": {"title": "Quad 2-input NAND gate", "family": "74HC", "group": "74xx", "role": "nand_gate"},
            "package": {"kind": "DIP", "default": "N"},
            "pins": {"1": ["1A", "in"], "2": ["1B", "in"], "3": ["1Y", "out"], "7": ["GND", "power"], "14": ["VCC", "power"]},
            "logic": {"type": "quad_2_input_nand"},
            "timing": {"default": "12ns", "datasheet": {"path": "A_or_B_to_Y", "load_pf": 50, "vcc_v": 4.5, "typical_ns": "9ns", "max_ns_25c": "18ns", "max_ns_minus40_to_85c": "23ns"}},
            "model": {"python": "HC00", "verilog": "ttl_74hc00"},
            "verify": ["truth_table", "timing", "propagation"],
            "sources": [{"label": "Texas Instruments SN74HC00", "package": "N, 14-pin PDIP", "url": "https://www.ti.com/lit/ds/symlink/sn74hc00.pdf"}],
            "variants": [["SN74HC00N", "Texas Instruments"]],
            "procurement": {"recommended_for_new_design": True, "availability_class": "active", "stock_basis": "broad-stock", "last_checked": "2026-07-13"},
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "simulation").mkdir()
            (root / "tests").mkdir()
            (root / "simulation" / "model.py").touch()
            (root / "simulation" / "model.v").touch()
            (root / "simulation" / "netlist.json").write_text("{}", encoding="utf-8")
            definition = resolve_compact_definition(source, root)
        self.assertEqual(definition["schema"], "db.component.digital")
        self.assertEqual(definition["pins"][0], {"number": 1, "name": "1A", "direction": "input"})
        self.assertEqual(definition["pins"][-1]["rail"], "VCC")
        self.assertEqual(definition["timing"]["timing_parameters"]["parameters"]["tPLH"]["source_field"], "timing.datasheet")
        self.assertEqual(definition["definition_layers"]["timing"]["timing_parameters"]["parameters"]["tPLH"]["source_field"], "definition_layers.timing.delay")
        validation = validate_digital_definition(definition)
        self.assertEqual([error["code"] for error in validation["errors"]], ["digital_manifest_missing"])

    def test_74hc00_pilot_resolves_with_the_existing_package_contract(self) -> None:
        base = ROOT / "lib" / "standard" / "74xx" / "74HC00"
        source_path = base / "definition" / "definition.json"
        if json.loads(source_path.read_text(encoding="utf-8")).get("schema") != COMPACT_SCHEMA:
            source_path = base / "definition" / "compact.pilot.json"
        source = json.loads(source_path.read_text(encoding="utf-8"))
        definition = resolve_compact_definition(source, base)
        evidence_path = base / "generated" / "resolved.json" if source_path.name == "definition.json" else base / "definition" / "definition.json"
        current = json.loads(evidence_path.read_text(encoding="utf-8"))
        self.assertTrue(validate_digital_definition(definition)["ok"])
        for key in ("part", "metadata", "package", "pins", "logic"):
            self.assertEqual(definition[key], current[key], key)
        self.assertEqual(definition["generation"]["python"]["file"], current["generation"]["python"]["file"])
        self.assertEqual(definition["generation"]["verilog"]["module"], current["generation"]["verilog"]["module"])


if __name__ == "__main__":
    unittest.main()
