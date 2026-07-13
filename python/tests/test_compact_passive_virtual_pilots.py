"""Lossless active typed compact definitions for passive and virtual Devices.

The compact source is the human-editable Device record and generated/resolved
is the canonical runtime cache.  UI strings remain legacy compatibility data;
there is no Resource file because neither package currently ships a separate
symbol/footprint artifact that can be mapped without guessing.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from chiplib.compact_component_definition import resolve_compact_component, validate_compact_component
from chiplib.db import audit_db, validate_component_definition
from chiplib.virtual_runtime import ClockSourceAdapter, ProbeAdapter, create_virtual_adapter


ROOT = Path(__file__).resolve().parents[2]


class CompactPassiveVirtualPilotTests(unittest.TestCase):
    def _assert_active_device(self, group: str, part: str) -> dict[str, object]:
        base = ROOT / "lib" / "standard" / group / part
        source = json.loads((base / "definition" / "definition.json").read_text(encoding="utf-8"))
        generated = json.loads((base / "generated" / "resolved.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_compact_component(source), [])
        resolved = resolve_compact_component(source)
        self.assertTrue(validate_component_definition(resolved)["ok"])
        self.assertEqual(resolved, generated)
        for key in ("schema", "version", "id", "part", "title", "family", "group", "kind", "role", "package", "status", "pins", "simulation", "ui", "definition_layers"):
            self.assertEqual(resolved[key], generated[key], key)
        return resolved

    def test_resistor_active_source_preserves_two_terminal_and_service_contract(self) -> None:
        resolved = self._assert_active_device("passive", "Resistor")
        self.assertEqual(resolved["passive"], {"kind": "resistor", "default_ohms": 10000})
        self.assertFalse((ROOT / "lib" / "standard" / "passive" / "Resistor" / "resource").exists())

    def test_capacitor_active_source_preserves_two_terminal_and_service_contract(self) -> None:
        resolved = self._assert_active_device("passive", "Capacitor")
        self.assertEqual(resolved["passive"], {"kind": "capacitor", "default_farads": 1e-06})
        self.assertFalse((ROOT / "lib" / "standard" / "passive" / "Capacitor" / "resource").exists())

    def test_clock_source_active_source_preserves_runtime_instrument_contract(self) -> None:
        resolved = self._assert_active_device("virtual", "ClockSource")
        self.assertEqual(resolved["virtual"], {"kind": "clock_source", "event_model": "periodic", "default_period_ns": 100})
        self.assertIsInstance(create_virtual_adapter("ClockSource", "VCLK"), ClockSourceAdapter)
        self.assertFalse((ROOT / "lib" / "standard" / "virtual" / "ClockSource" / "resource").exists())

    def test_probe_active_source_preserves_legacy_contract_and_runtime_behavior(self) -> None:
        resolved = self._assert_active_device("virtual", "Probe")
        # This projection is the complete pre-migration Probe record.  The
        # typed ``virtual`` payload is additive authoring metadata; every
        # legacy DB field remains byte-for-byte meaning-equivalent.
        legacy = {
            "schema": "db.component.definition", "version": 1,
            "id": "Probe", "part": "Probe", "group": "virtual",
            "kind": "virtual", "role": "probe", "title": "Single logic probe",
            "family": "Virtual", "package": {"kind": "virtual", "pins": 1},
            "status": {"datasheet": "not_applicable", "pinout": "modeled", "python_behavior": "modeled", "verilog_model": "not_applicable", "verilog_export": "not_applicable", "tests": "modeled"},
            "pins": [{"number": 1, "name": "IN", "direction": "input"}],
            "simulation": {"service": "sim.probe"},
            "ui": {"widget": "probe", "symbol": "probe"},
        }
        for key, value in legacy.items():
            self.assertEqual(resolved[key], value, key)
        probe = create_virtual_adapter("Probe", "P1")
        self.assertIsInstance(probe, ProbeAdapter)
        self.assertEqual(probe.sample("Z", time_ps=25), {"time_ps": 25, "value": "Z", "modeled_only": True})
        self.assertFalse((ROOT / "lib" / "standard" / "virtual" / "Probe" / "resource").exists())

    def test_active_legacy_packages_still_pass_db_audit(self) -> None:
        self.assertTrue(audit_db()["ok"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
