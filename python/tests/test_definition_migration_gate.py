"""Regression gate for active/pilot compact Device inventory and freshness."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("check_definition_migration", ROOT / "tools" / "check_definition_migration.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class DefinitionMigrationGateTests(unittest.TestCase):
    def test_inventory_is_explicit_and_all_records_are_fresh(self) -> None:
        records = MODULE.collect_records(ROOT)
        self.assertEqual(
            [(record.part, record.device_class, record.state) for record in records],
            [("74HC00", "digital", "active"), ("74HC04", "digital", "active"),
             ("74HC157", "digital", "active"),
             ("74HC161", "digital", "active"), ("74HC245", "digital", "active"),
             ("74HC574", "digital", "active"), ("AT28C256", "memory", "active"),
             ("Capacitor", "passive", "active"), ("Resistor", "passive", "active"),
             ("ClockSource", "virtual", "active"),
             ("Probe", "virtual", "active")],
        )
        self.assertEqual([failure for record in records for failure in MODULE.validate_record(record)], [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
