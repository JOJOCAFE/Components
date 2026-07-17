"""Focused tests for the first source-owning Component Board service path."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from chiplib.api import board_static_file, handle_request
from chiplib.component_edit import source_revision


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "Language" / "fixtures" / "component-v1.1" / "digital_inverter.component").read_text(encoding="utf-8")


def test_board_chip_frame_resource_is_available() -> None:
    frame = board_static_file("resources/74hc-chip-frames-no-pins/74hc04.svg")
    assert frame == ROOT / "board" / "assets" / "74hc-chip-frames-no-pins" / "74hc04.svg"
    root = ElementTree.parse(frame).getroot()
    assert root.tag.endswith("svg")
    assert root.attrib["role"] == "img"
    assert root.find("{http://www.w3.org/2000/svg}title") is not None
    assert board_static_file("resources/74hc-chip-frames-no-pins/../../docs/CHIP_STATUS.md") is None


def test_board_example_resolve_run_and_checked_source_edit() -> None:
    example = handle_request({"command": "component-language-example"})
    assert example["ok"] is True
    source = example["result"]["source"]
    board = handle_request({"command": "component-language-board-view", "input": {"source": source}})
    assert board["ok"] is True
    assert board["result"]["component_id"] == "DigitalInverterFixture"
    u1 = next(block for block in board["result"]["blocks"] if block["id"] == "U1")
    assert u1["resource"] == {
        "kind": "chip-frame-no-pins.svg",
        "asset": "resources/74hc-chip-frames-no-pins/74hc04.svg",
        "source": "board/assets/74hc-chip-frames-no-pins/74hc04.svg",
    }
    assert u1["pins"] == [
        {"number": 1, "name": "1A", "direction": "input"},
        {"number": 2, "name": "1Y", "direction": "output"},
        {"number": 3, "name": "2A", "direction": "input"},
        {"number": 4, "name": "2Y", "direction": "output"},
        {"number": 5, "name": "3A", "direction": "input"},
        {"number": 6, "name": "3Y", "direction": "output"},
        {"number": 7, "name": "GND", "direction": "power"},
        {"number": 8, "name": "4Y", "direction": "output"},
        {"number": 9, "name": "4A", "direction": "input"},
        {"number": 10, "name": "5Y", "direction": "output"},
        {"number": 11, "name": "5A", "direction": "input"},
        {"number": 12, "name": "6Y", "direction": "output"},
        {"number": 13, "name": "6A", "direction": "input"},
        {"number": 14, "name": "VCC", "direction": "power"},
    ]
    assert u1["pin_anchors"] == [
        {"id": "U1.pin-1", "endpoint": "U1.1A", "physical_pin": 1, "port": "1A", "direction": "input", "dip_side": "left", "dip_order": 1},
        {"id": "U1.pin-2", "endpoint": "U1.1Y", "physical_pin": 2, "port": "1Y", "direction": "output", "dip_side": "left", "dip_order": 2},
        {"id": "U1.pin-3", "endpoint": "U1.2A", "physical_pin": 3, "port": "2A", "direction": "input", "dip_side": "left", "dip_order": 3},
        {"id": "U1.pin-4", "endpoint": "U1.2Y", "physical_pin": 4, "port": "2Y", "direction": "output", "dip_side": "left", "dip_order": 4},
        {"id": "U1.pin-5", "endpoint": "U1.3A", "physical_pin": 5, "port": "3A", "direction": "input", "dip_side": "left", "dip_order": 5},
        {"id": "U1.pin-6", "endpoint": "U1.3Y", "physical_pin": 6, "port": "3Y", "direction": "output", "dip_side": "left", "dip_order": 6},
        {"id": "U1.pin-7", "endpoint": "U1.GND", "physical_pin": 7, "port": "GND", "direction": "power", "dip_side": "left", "dip_order": 7},
        {"id": "U1.pin-8", "endpoint": "U1.4Y", "physical_pin": 8, "port": "4Y", "direction": "output", "dip_side": "right", "dip_order": 7},
        {"id": "U1.pin-9", "endpoint": "U1.4A", "physical_pin": 9, "port": "4A", "direction": "input", "dip_side": "right", "dip_order": 6},
        {"id": "U1.pin-10", "endpoint": "U1.5Y", "physical_pin": 10, "port": "5Y", "direction": "output", "dip_side": "right", "dip_order": 5},
        {"id": "U1.pin-11", "endpoint": "U1.5A", "physical_pin": 11, "port": "5A", "direction": "input", "dip_side": "right", "dip_order": 4},
        {"id": "U1.pin-12", "endpoint": "U1.6Y", "physical_pin": 12, "port": "6Y", "direction": "output", "dip_side": "right", "dip_order": 3},
        {"id": "U1.pin-13", "endpoint": "U1.6A", "physical_pin": 13, "port": "6A", "direction": "input", "dip_side": "right", "dip_order": 2},
        {"id": "U1.pin-14", "endpoint": "U1.VCC", "physical_pin": 14, "port": "VCC", "direction": "power", "dip_side": "right", "dip_order": 1},
    ]
    run = handle_request({"command": "component-language-run", "input": {"source": source}, "options": {"test": "inversion"}})
    assert run["ok"] is True
    assert run["result"]["test"]["ok"] is True

    driven = handle_request({"command": "component-language-run", "input": {"source": source, "drives": [{"target": "clock", "value": "1"}]}})
    assert driven["ok"] is True
    assert driven["result"]["probes"]["probes"]["input_level"] == 1
    assert driven["result"]["probes"]["probes"]["inverted_level"] == 0
    assert board_static_file(u1["resource"]["asset"]) == ROOT / "board" / "assets" / "74hc-chip-frames-no-pins" / "74hc04.svg"
    assert board["result"]["wires"][0] == {"id": "edge:vcc->U1.VCC", "from": "vcc", "to": "U1.VCC", "kind": "scalar"}

    edited = handle_request({
        "command": "component-language-edit",
        "input": {"source": source, "source_revision": source_revision(source), "edit": {"kind": "connect", "from": "clock", "to": "Observe.IN"}},
    })
    assert edited["ok"] is True
    assert edited["result"]["ok"] is True
    assert edited["result"]["patch"] == {"kind": "connect", "added_line": "connect clock -> Observe.IN;"}
    assert "connect clock -> Observe.IN;" in edited["result"]["source"]


def test_board_edit_rejects_stale_or_missing_connection_without_mutating_text() -> None:
    stale = handle_request({
        "command": "component-language-edit",
        "input": {"source": SOURCE, "source_revision": "sha256:" + "0" * 64, "edit": {"kind": "connect", "from": "clock", "to": "U1.1A"}},
    })
    assert stale["result"]["ok"] is False
    assert stale["result"]["diagnostics"][0]["code"] == "board.stale_source"
    removed = handle_request({
        "command": "component-language-edit",
        "input": {"source": SOURCE, "source_revision": source_revision(SOURCE), "edit": {"kind": "disconnect", "from": "clock", "to": "Observe.IN"}},
    })
    assert removed["result"]["ok"] is False
    assert removed["result"]["source"] == SOURCE


def test_board_checked_add_commands_create_readable_component_declarations() -> None:
    revision = source_revision(SOURCE)
    device = handle_request({
        "command": "component-language-edit",
        "input": {"source": SOURCE, "source_revision": revision, "edit": {"kind": "add_device", "id": "U2", "part": "digital.74HC04"}},
    })["result"]
    assert device["ok"] is True
    assert device["patch"] == {"kind": "add_device", "added_line": "device U2, digital.74HC04;"}
    net = handle_request({
        "command": "component-language-edit",
        "input": {"source": device["source"], "source_revision": device["source_revision"], "edit": {"kind": "add_net", "id": "data", "signal_kind": "digital"}},
    })["result"]
    assert net["ok"] is True
    bus = handle_request({
        "command": "component-language-edit",
        "input": {"source": net["source"], "source_revision": net["source_revision"], "edit": {"kind": "add_bus", "id": "address", "width": 8, "signal_kind": "digital"}},
    })["result"]
    assert bus["ok"] is True
    assert "device U2, digital.74HC04;" in bus["source"]
    assert "net data : digital;" in bus["source"]
    assert "bus address[8] : digital;" in bus["source"]


def test_board_edit_preview_is_pure_and_requires_fresh_legal_source() -> None:
    revision = source_revision(SOURCE)
    legal = handle_request({
        "command": "component-language-edit-preview",
        "input": {"source": SOURCE, "source_revision": revision, "edit": {"kind": "connect", "from": "clock", "to": "Observe.IN"}},
    })
    preview = legal["result"]
    assert legal["ok"] is True and preview["ok"] is True
    assert preview["format"] == "components.component-edit-preview@1"
    assert preview["source"] == SOURCE
    assert preview["source_revision"] == revision
    assert preview["patch"] == {"kind": "connect", "added_line": "connect clock -> Observe.IN;"}
    assert preview["candidate_source_revision"] != revision
    assert preview["resolved_digest"].startswith("sha256:")

    ownership = handle_request({
        "command": "component-language-edit-preview",
        "input": {"source": SOURCE, "source_revision": revision, "edit": {"kind": "connect", "from": "U1.1Y", "to": "clock"}},
    })["result"]
    assert ownership["ok"] is False
    assert ownership["source"] == SOURCE
    assert "validation.output_ownership" in {item["code"] for item in ownership["diagnostics"]}

    stale = handle_request({
        "command": "component-language-edit-preview",
        "input": {"source": SOURCE, "source_revision": "sha256:" + "0" * 64, "edit": {"kind": "connect", "from": "clock", "to": "Observe.IN"}},
    })["result"]
    assert stale["ok"] is False
    assert stale["source"] == SOURCE
    assert stale["diagnostics"][0]["code"] == "board.stale_source"


def main() -> None:
    test_board_chip_frame_resource_is_available()
    test_board_example_resolve_run_and_checked_source_edit()
    test_board_edit_rejects_stale_or_missing_connection_without_mutating_text()
    test_board_checked_add_commands_create_readable_component_declarations()
    test_board_edit_preview_is_pure_and_requires_fresh_legal_source()
    print("Component Board API tests passed")


if __name__ == "__main__":
    main()
