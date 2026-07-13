"""Ownership boundary checks for the first Device + Resource split."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from chiplib.compact_definition import resolve_compact_definition
from chiplib.resource_definition import load_device_resource


ROOT = Path(__file__).resolve().parents[2]


class DefinitionOwnershipTests(unittest.TestCase):
    def test_74hc00_resource_is_presentation_only_and_links_the_active_device(self) -> None:
        package = ROOT / "lib" / "standard" / "74xx" / "74HC00"
        source = json.loads((package / "definition" / "definition.json").read_text(encoding="utf-8"))
        resolved = resolve_compact_definition(source, package)
        resource = load_device_resource(package, "74HC00")
        assert resource is not None

        self.assertEqual(resource["maps"]["device_definition"], "../definition/definition.json")
        self.assertEqual(set(resource), {"schema", "version", "maps", "views"})
        self.assertNotIn("resource", resolved)
        self.assertNotIn("views", resolved)

        dip = json.loads((package / "symbol" / "dip.json").read_text(encoding="utf-8"))
        displayed = [(pin["number"], pin["name"], pin["direction"]) for pin in dip["pins"]]
        device = [(pin["number"], pin["name"], pin["direction"]) for pin in resolved["pins"]]
        self.assertEqual(displayed, device)

    def test_74hc161_resource_preserves_counter_pin_presentation(self) -> None:
        """A Resource shows counter labels, without defining their meaning."""
        package = ROOT / "lib" / "standard" / "74xx" / "74HC161"
        source = json.loads((package / "definition" / "definition.json").read_text(encoding="utf-8"))
        resolved = resolve_compact_definition(source, package)
        resource = load_device_resource(package, "74HC161")
        assert resource is not None

        self.assertEqual(set(resource), {"schema", "version", "maps", "views"})
        self.assertEqual(resource["views"]["dip"]["artifact"], "../symbol/dip.json")
        self.assertNotIn("resource", resolved)
        self.assertNotIn("views", resolved)

        dip = json.loads((package / "symbol" / "dip.json").read_text(encoding="utf-8"))
        pins = {pin["number"]: pin for pin in resolved["pins"]}
        self.assertEqual((dip["part"], dip["pins"]), (resolved["part"], len(pins)))
        self.assertEqual(set(dip["left"] + dip["right"]), set(pins))
        for number_text, label in dip["labels"].items():
            self.assertEqual(pins[int(number_text)]["name"], label)
        self.assertEqual(
            dip["bus_groups"]["D"],
            [pin["number"] for pin in resolved["pins"] if pin.get("bus") == "D"],
        )
        # The Q pins are physically presented top-to-bottom as QA..QD on the
        # DIP's right side, which is the inverse of numeric pin order.
        self.assertEqual(
            set(dip["bus_groups"]["Q"]),
            {pin["number"] for pin in resolved["pins"] if pin.get("bus") == "Q"},
        )
        self.assertEqual((pins[1]["name"], pins[1]["active_low"]), ("/CLR", True))
        self.assertEqual((pins[2]["name"], pins[2]["clock"]), ("CLK", True))
        self.assertEqual((pins[15]["name"], pins[15]["direction"]), ("RCO", "output"))
        self.assertEqual(resolved["logic"]["terminal_count"], {
            "condition": "Q=15 and ENT=1", "output": "RCO",
        })

    def test_resource_schema_rejects_an_attempt_to_override_device_behavior(self) -> None:
        """Presentation maps are closed objects, not a second Device source."""
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary)
            (package / "definition").mkdir()
            (package / "resource").mkdir()
            (package / "symbol").mkdir()
            (package / "definition" / "definition.json").write_text("{}", encoding="utf-8")
            (package / "symbol" / "dip.json").write_text("{}", encoding="utf-8")
            (package / "resource" / "definition.json").write_text(json.dumps({
                "schema": "components.resource", "version": 1,
                "maps": {"part": "Example", "device_definition": "../definition/definition.json"},
                "views": {"dip": {"kind": "symbol.dip", "artifact": "../symbol/dip.json"}},
                "timing": {"default": "0ns"},
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Additional properties"):
                load_device_resource(package, "Example")

    def test_74hc245_resource_preserves_symbol_pin_and_bus_presentation(self) -> None:
        """A Resource may select a view, but may not redefine a transceiver."""
        package = ROOT / "lib" / "standard" / "74xx" / "74HC245"
        source = json.loads((package / "definition" / "definition.json").read_text(encoding="utf-8"))
        resolved = resolve_compact_definition(source, package)
        resource = load_device_resource(package, "74HC245")
        assert resource is not None

        self.assertEqual(set(resource), {"schema", "version", "maps", "views"})
        self.assertEqual(resource["views"]["dip"]["artifact"], "../symbol/dip.json")
        self.assertNotIn("resource", resolved)
        self.assertNotIn("views", resolved)

        dip = json.loads((package / "symbol" / "dip.json").read_text(encoding="utf-8"))
        pins = {pin["number"]: pin for pin in resolved["pins"]}
        self.assertEqual(dip["part"], resolved["part"])
        self.assertEqual(dip["pins"], len(pins))
        self.assertEqual(dip["left"], list(range(1, 11)))
        self.assertEqual(dip["right"], list(range(20, 10, -1)))
        self.assertEqual(set(dip["left"] + dip["right"]), set(pins))
        for number_text, label in dip["labels"].items():
            self.assertEqual(pins[int(number_text)]["name"], label)
        self.assertEqual(
            dip["bus_groups"]["A"],
            [pin["number"] for pin in resolved["pins"] if pin.get("bus") == "A"],
        )
        # The right DIP side is presented top-to-bottom (B8 to B1), while the
        # Device pin list is naturally number-ascending.  Verify membership
        # rather than replacing the presentation order with Device order.
        self.assertEqual(
            set(dip["bus_groups"]["B"]),
            {pin["number"] for pin in resolved["pins"] if pin.get("bus") == "B"},
        )

    def test_74hc157_resource_preserves_mux_pin_presentation(self) -> None:
        """The DIP view may label a mux, but its enable semantics stay Device-owned."""
        package = ROOT / "lib" / "standard" / "74xx" / "74HC157"
        source = json.loads((package / "definition" / "definition.json").read_text(encoding="utf-8"))
        resolved = resolve_compact_definition(source, package)
        resource = load_device_resource(package, "74HC157")
        assert resource is not None

        self.assertEqual(set(resource), {"schema", "version", "maps", "views"})
        self.assertEqual(resource["views"]["dip"]["artifact"], "../symbol/dip.json")
        self.assertNotIn("views", resolved)

        dip = json.loads((package / "symbol" / "dip.json").read_text(encoding="utf-8"))
        pins = {pin["number"]: pin for pin in resolved["pins"]}
        self.assertEqual(dip["part"], resolved["part"])
        self.assertEqual(set(dip["left"] + dip["right"]), set(pins))
        for number_text, label in dip["labels"].items():
            self.assertEqual(pins[int(number_text)]["name"], label)
        for bus in ("A", "B", "Y"):
            self.assertEqual(
                set(dip["bus_groups"][bus]),
                {pin["number"] for pin in resolved["pins"] if pin.get("bus") == bus},
            )
        enable = pins[15]
        self.assertEqual((enable["name"], enable["direction"], enable["active_low"]), ("/G", "input", True))
        self.assertEqual(resolved["logic"]["enable"], {"pin": "/G", "active_low": True})

    def test_74hc574_resource_preserves_clocked_tri_state_pin_presentation(self) -> None:
        """A Resource exposes /OE and CLK labels without defining clock or Z behavior."""
        package = ROOT / "lib" / "standard" / "74xx" / "74HC574"
        source = json.loads((package / "definition" / "definition.json").read_text(encoding="utf-8"))
        resolved = resolve_compact_definition(source, package)
        resource = load_device_resource(package, "74HC574")
        assert resource is not None

        self.assertEqual(set(resource), {"schema", "version", "maps", "views"})
        self.assertEqual(resource["views"]["dip"]["artifact"], "../symbol/dip.json")
        self.assertNotIn("views", resolved)

        dip = json.loads((package / "symbol" / "dip.json").read_text(encoding="utf-8"))
        pins = {pin["number"]: pin for pin in resolved["pins"]}
        self.assertEqual(dip["part"], resolved["part"])
        self.assertEqual(set(dip["left"] + dip["right"]), set(pins))
        for number_text, label in dip["labels"].items():
            self.assertEqual(pins[int(number_text)]["name"], label)
        for bus in ("D", "Q"):
            self.assertEqual(
                set(dip["bus_groups"][bus]),
                {pin["number"] for pin in resolved["pins"] if pin.get("bus") == bus},
            )
        self.assertEqual((pins[1]["name"], pins[1]["active_low"]), ("/OE", True))
        self.assertEqual((pins[11]["name"], pins[11]["clock"]), ("CLK", True))
        self.assertEqual(resolved["logic"]["clock"], {"pin": "CLK", "edge": "rising"})
        self.assertTrue(resolved["logic"]["tristate"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
