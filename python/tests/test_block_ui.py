"""Block-UI import/export tests over the normalized Design contract."""

from __future__ import annotations

from chiplib import Design, design_from_block_ui, design_to_block_ui


def small_design():
    return {
        "name": "block-small",
        "description": "student NAND sketch",
        "chips": {"U1": {"part": "74HC00", "label": "NAND"}},
        "buses": {"DATA": {"width": 2, "label": "Data bus"}},
        "aliases": {"A": "U1:1", "B": "U1:2", "Y": "U1:3"},
        "rails": {"VCC": 1, "GND": 0},
        "connect": [
            "A -> DATA:0",
            "B -> DATA:1",
            "Y -> DATA:0",
            "VCC -> U1:14",
            "GND -> U1:7",
        ],
        "inputs": {"power_on": ["A = 1", "B = 1"]},
        "probes": {"logic": ["Y", "DATA:0"]},
        "layout": {
            "blocks": {"U1": {"x": 120, "y": 80}, "DATA": {"x": 40, "y": 200}},
            "wires": {"W1": {"points": [[120, 90], [40, 200]]}},
        },
    }


def test_design_exports_block_ui_with_blocks_wires_and_layout():
    design = Design.from_dict(small_design())

    block_ui = design.to_block_ui()
    blocks = {block["id"]: block for block in block_ui["blocks"]}

    assert block_ui["format"] == "components.block_ui"
    assert block_ui["version"] == 1
    assert block_ui["design"]["name"] == "block-small"
    assert blocks["U1"]["type"] == "chip"
    assert blocks["U1"]["part"] == "74HC00"
    assert blocks["U1"]["layout"] == {"x": 120, "y": 80}
    assert blocks["DATA"]["type"] == "bus"
    assert blocks["DATA"]["width"] == 2
    assert blocks["VCC"]["type"] == "rail"
    assert block_ui["wires"][0]["rule"] == "A -> DATA:0"
    assert block_ui["wires"][0]["endpoints"] == ["A", "DATA:0"]
    assert block_ui["wires"][0]["layout"] == {"points": [[120, 90], [40, 200]]}


def test_block_ui_import_preserves_design_fields_and_layout():
    block_ui = Design.from_dict(small_design()).to_block_ui()

    imported = Design.from_block_ui(block_ui).to_dict()

    assert imported["name"] == "block-small"
    assert imported["description"] == "student NAND sketch"
    assert imported["chips"]["U1"]["part"] == "74HC00"
    assert imported["chips"]["U1"]["label"] == "NAND"
    assert imported["buses"]["DATA"]["width"] == 2
    assert imported["connect"] == small_design()["connect"]
    assert imported["inputs"] == small_design()["inputs"]
    assert imported["probes"] == small_design()["probes"]
    assert imported["layout"]["blocks"]["U1"] == {"x": 120, "y": 80}
    assert imported["layout"]["wires"]["W1"] == {"points": [[120, 90], [40, 200]]}


def test_module_helpers_round_trip_block_ui_contract():
    design = Design.from_dict(small_design())

    block_ui = design_to_block_ui(design)
    imported = design_from_block_ui(block_ui)
    exported_again = imported.to_block_ui()

    assert exported_again["blocks"] == block_ui["blocks"]
    assert exported_again["wires"] == block_ui["wires"]
    assert imported.validate()["ok"] is True


def run_all():
    test_design_exports_block_ui_with_blocks_wires_and_layout()
    test_block_ui_import_preserves_design_fields_and_layout()
    test_module_helpers_round_trip_block_ui_contract()


if __name__ == "__main__":
    run_all()
    print("Components block UI tests passed")
