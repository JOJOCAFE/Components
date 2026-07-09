"""Executable contract tests for the planned schematic Design API."""

from chiplib import Board
from chiplib.design import Design


def small_schematic():
    return {
        "name": "small-nand-schematic",
        "chips": [
            {"ref": "U1", "part": "74HC00"},
        ],
        "buses": [
            {"name": "DATA", "width": 8},
        ],
        "aliases": {
            "A": "U1:1",
            "B": "U1:2",
            "Y": "U1:3",
            "DATA0": "DATA:0",
        },
        "connections": [
            "A -> DATA:1",
            "B -> DATA:2",
            "U1:3 -> DATA:0",
            "VCC -> U1:14",
            "GND -> U1:7",
        ],
        "pullups": [
            "DATA:0",
            "DATA0",
        ],
        "pulldowns": [
            "DATA:7",
        ],
        "inputs": {
            "power_on": {
                "A": 1,
                "B": 0,
            },
        },
        "input_sets": [
            {
                "name": "front_panel",
                "channels": [
                    {"index": 0, "name": "SW_A", "target": "A", "power_on": 1},
                    {"index": 1, "name": "SW_B", "target": "B", "power_on": 0},
                ],
            },
        ],
        "probes": [
            {
                "set": "logic",
                "channels": [
                    {"name": "nand_y_pin", "target": "Y"},
                    {"name": "data0_bus", "target": "DATA:0"},
                ],
            },
        ],
    }


def require_design_io(design):
    """Return optional IO controllers using the planned Design API."""
    if hasattr(design, "to_io"):
        return design.to_io()
    if hasattr(design, "io"):
        return design.io()
    raise AssertionError("Design should expose named input_sets and probes through to_io() or io()")


def assert_snapshot_has_top_level_sections(snapshot):
    for key in ("chips", "buses", "nets", "rails", "sources"):
        assert key in snapshot, f"snapshot missing {key!r}"


def test_from_dict_to_dict_round_trip_preserves_schematic_contract():
    schematic = small_schematic()

    design = Design.from_dict(schematic)
    data = design.to_dict()
    assert data["name"] == schematic["name"]
    assert data["chips"]["U1"]["part"] == "74HC00"
    assert data["buses"]["DATA"]["width"] == 8
    assert data["connect"] == schematic["connections"]
    assert data["inputs"]["power_on"] == ["A = 1", "B = 0"]
    assert data["input_sets"]["front_panel"]["channels"][0]["name"] == "SW_A"
    assert data["probes"]["logic"]["channels"][1]["target"] == "DATA:0"


def test_design_to_board_materializes_aliases_buses_connections_power_and_pulls():
    design = Design.from_dict(small_schematic())

    board = design.to_board()
    assert isinstance(board, Board)

    snapshot = board.snapshot()
    assert_snapshot_has_top_level_sections(snapshot)

    chip_refs = {chip["ref"] for chip in snapshot["chips"]}
    assert chip_refs == {"U1"}

    buses = {bus["name"]: bus for bus in snapshot["buses"]}
    assert buses["DATA"]["width"] == 8

    data0 = buses["DATA"]["lines"][0]
    data1 = buses["DATA"]["lines"][1]
    data2 = buses["DATA"]["lines"][2]
    data7 = buses["DATA"]["lines"][7]

    assert data0["tag"] == "bus:DATA[0]"
    assert data1["tag"] == "bus:DATA[1]"
    assert data2["tag"] == "bus:DATA[2]"
    assert any(pin["chip"] == "U1" and pin["number"] == 3 for pin in data0["pins"])
    assert any(pin["chip"] == "U1" and pin["number"] == 1 for pin in data1["pins"])
    assert any(pin["chip"] == "U1" and pin["number"] == 2 for pin in data2["pins"])
    assert data0["value"] == 1
    assert data7["value"] == 0

    rails = {(rail["name"], rail["value"]) for rail in snapshot["rails"]}
    assert ("VCC", 1) in rails
    assert ("GND", 0) in rails

    source_names = {source["name"] for source in snapshot["sources"]}
    assert "rail:VCC->U1:14" in source_names
    assert "rail:GND->U1:7" in source_names

    net_by_name = {net["name"]: net for net in snapshot["nets"]}
    assert [pull["value"] for pull in net_by_name["bus:DATA[0]"]["pulls"]] == [1, 1]
    assert net_by_name["bus:DATA[7]"]["pulls"] == [{"source": "bus:DATA[7]", "value": 0}]


def test_design_exposes_power_on_inputs_input_sets_and_named_probe_sets():
    design = Design.from_dict(small_schematic())
    board = design.to_board()

    io = require_design_io(design)
    stimulus = io["stimulus"]
    probes = io["probes"]

    board.settle()
    stimulus_snapshot = stimulus.snapshot()
    probe_snapshot = probes.snapshot()

    input_sets = {item["name"]: item for item in stimulus_snapshot["input_sets"]}
    assert "front_panel" in input_sets

    front_panel_inputs = {
        channel["name"]: channel
        for channel in input_sets["front_panel"]["inputs"]
        if channel["name"] in {"SW_A", "SW_B"}
    }
    assert front_panel_inputs["SW_A"]["index"] == 0
    assert front_panel_inputs["SW_A"]["value"] == 1
    assert front_panel_inputs["SW_A"]["targets"] == [{"chip": "U1", "pin": 1}]
    assert front_panel_inputs["SW_B"]["index"] == 1
    assert front_panel_inputs["SW_B"]["value"] == 0
    assert front_panel_inputs["SW_B"]["targets"] == [{"chip": "U1", "pin": 2}]

    probe_sets = {item["name"]: item for item in probe_snapshot["sets"]}
    assert "logic" in probe_sets
    logic_channels = {channel["name"]: channel for channel in probe_sets["logic"]["channels"]}
    assert logic_channels["nand_y_pin"]["target_kind"] == "pin"
    assert logic_channels["nand_y_pin"]["target"] == "U1.1Y"
    assert logic_channels["data0_bus"]["target_kind"] == "bus"
    assert logic_channels["data0_bus"]["target"] == "bus:DATA[0]"


def run_all():
    test_from_dict_to_dict_round_trip_preserves_schematic_contract()
    test_design_to_board_materializes_aliases_buses_connections_power_and_pulls()
    test_design_exposes_power_on_inputs_input_sets_and_named_probe_sets()


if __name__ == "__main__":
    run_all()
    print("Components Python design tests passed")
