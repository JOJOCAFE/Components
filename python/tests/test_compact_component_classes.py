"""Focused proof that each non-digital class resolves to the generic contract."""
from __future__ import annotations

import unittest

from chiplib.compact_component_definition import resolve_compact_component, validate_compact_component
from chiplib.db import validate_component_definition


def source(group: str, payload: dict[str, object]) -> dict[str, object]:
    return {"schema": f"db.component.{group}.compact", "version": "0.2", "profile": f"{group}.basic@0.2", "part": f"Demo{group.title()}", "about": {"title": f"Demo {group}", "family": group.title(), "group": group, "kind": "virtual" if group == "virtual" else "physical", "role": group}, "package": {"kind": "two_terminal"}, "pins": {"1": ["A", "passive"], "2": ["B", "passive"]}, "simulation": {"service": f"sim.{group}.demo"}, "ui": {"symbol": "demo"}, group: payload}


class CompactComponentClassesTests(unittest.TestCase):
    def test_each_type_has_a_typed_payload_and_stable_output(self) -> None:
        payloads = {"passive": {"kind": "resistor", "default_ohms": 10000}, "virtual": {"kind": "stimulus", "event_model": "clock"}, "discrete": {"kind": "bjt", "polarity": "npn"}, "support": {"model_scope": "functional only"}}
        for group, payload in payloads.items():
            with self.subTest(group=group):
                compact = source(group, payload)
                self.assertEqual(validate_compact_component(compact), [])
                resolved = resolve_compact_component(compact)
                self.assertTrue(validate_component_definition(resolved)["ok"])
                self.assertEqual(resolved["schema"], "db.component.definition")
                self.assertEqual(resolved[group], payload)

    def test_wrong_group_is_rejected_by_the_typed_schema(self) -> None:
        compact = source("passive", {"kind": "resistor"})
        compact["about"]["group"] = "virtual"  # type: ignore[index]
        self.assertTrue(validate_compact_component(compact))


if __name__ == "__main__":
    unittest.main()
