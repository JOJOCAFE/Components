"""Keep functional-pinout SVG nodes addressable without making them truth."""
from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[2]
PINOUTS = ROOT / "board" / "assets" / "74hc-functional-pinouts"
NO_PIN_FRAMES = ROOT / "board" / "assets" / "74hc-chip-frames-no-pins"


def _pin_nodes(path: Path):
    root = ElementTree.parse(path).getroot()
    return [
        node for node in root.iter()
        if node.tag.rsplit("}", 1)[-1] == "rect"
        and "pin" in node.get("class", "").split()
    ]


def test_every_74hc_svg_pin_node_has_command_lookup_metadata():
    for path in sorted(PINOUTS.glob("74hc*.svg")):
        pins = _pin_nodes(path)
        assert pins, f"{path.name} has no pin nodes"
        seen_numbers = set()
        for pin in pins:
            number = pin.get("data-pin-number")
            name = pin.get("data-pin-name")
            assert number and number.isdecimal(), f"{path.name}: missing pin number"
            assert name, f"{path.name}: missing pin name for pin {number}"
            assert pin.get("data-component-pin") == f"pin-{number}"
            assert pin.get("data-component-selector") == f"@{number}"
            assert pin.get("data-component-port") == name
            assert number not in seen_numbers, f"{path.name}: duplicate pin {number}"
            seen_numbers.add(number)


def test_74hc04_node_metadata_supports_named_and_physical_lookup():
    pins = _pin_nodes(PINOUTS / "74hc04.svg")
    by_number = {pin.get("data-pin-number"): pin for pin in pins}
    assert by_number["2"].get("data-pin-name") == "1Y"
    assert by_number["2"].get("data-component-pin") == "pin-2"
    assert by_number["2"].get("data-component-selector") == "@2"


def test_no_pin_chip_frames_remove_lead_stubs_but_keep_definition_metadata():
    frames = sorted(NO_PIN_FRAMES.glob("74hc*.svg"))
    assert frames
    for path in frames:
        text = path.read_text(encoding="utf-8")
        assert 'class="lead"' not in text
        assert 'class="node"' in text
        assert 'class="pin"' in text
        assert 'class="name"' in text
        assert ">1:1A</text>" in text
        assert 'class="number"' not in text
        assert 'id="connector0node"' in text
        assert 'data-pin-number="1"' in text
        assert 'data-pin-name="1A"' in text
        assert 'data-component-selector="@1"' in text
