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
        "run_config": {"default_backend": "verilog", "selected_backend": "verilog"},
        "layout": {
            "blocks": {"U1": {"x": 120, "y": 80}, "DATA": {"x": 40, "y": 200}},
            "wires": {"W1": {"points": [[120, 90], [40, 200]]}},
        },
    }


def test_design_exports_block_ui_with_blocks_wires_and_layout():
    design = Design.from_dict(small_design())

    block_ui = design.to_block_ui()
    blocks = {block["id"]: block for block in block_ui["blocks"]}
    nets = {net["name"]: net for net in block_ui["nets"]}

    assert block_ui["format"] == "components.block_ui"
    assert block_ui["version"] == 1
    assert block_ui["design"]["name"] == "block-small"
    assert blocks["U1"]["type"] == "chip"
    assert blocks["U1"]["part"] == "74HC00"
    assert blocks["U1"]["shape"] == "dip"
    assert blocks["U1"]["package"] == {"kind": "DIP", "pins": 14}
    assert blocks["U1"]["pins"][0]["ref"] == "U1:1"
    assert blocks["U1"]["pins"][0]["name"] == "1A"
    assert blocks["U1"]["pins"][0]["side"] == "left"
    assert blocks["U1"]["pins"][0]["side_index"] == 0
    assert blocks["U1"]["pins"][0]["dip_position"] == {"side": "left", "index": 0, "count": 7}
    assert blocks["U1"]["pins"][-1]["ref"] == "U1:14"
    assert blocks["U1"]["pins"][-1]["side"] == "right"
    assert blocks["U1"]["pins"][-1]["side_index"] == 0
    assert blocks["U1"]["layout"] == {"x": 120, "y": 80}
    assert blocks["DATA"]["type"] == "bus"
    assert blocks["DATA"]["width"] == 2
    assert blocks["DATA"]["pins"][0]["ref"] == "DATA:0"
    assert blocks["VCC"]["type"] == "rail"
    assert blocks["VCC"]["pins"] == [{"id": "VCC", "ref": "VCC", "kind": "rail", "rail": "VCC", "net": "VCC"}]
    assert block_ui["wires"][0]["rule"] == "A -> DATA:0"
    assert block_ui["wires"][0]["endpoints"] == ["A", "DATA:0"]
    assert block_ui["wires"][0]["endpoint_details"][0]["kind"] == "pin"
    assert block_ui["wires"][0]["endpoint_details"][0]["resolved_ref"] == "U1:1"
    assert block_ui["wires"][0]["endpoint_details"][0]["net"] == "bus:DATA[0]"
    assert block_ui["wires"][0]["layout"] == {"points": [[120, 90], [40, 200]]}
    assert nets["bus:DATA[0]"]["kind"] == "bus"
    assert {"ref": "U1:1", "kind": "pin", "chip": "U1", "pin": 1, "name": "1A", "direction": "in"} in nets["bus:DATA[0]"]["endpoints"]
    assert block_ui["run_config"]["default_backend"] == "verilog"
    assert block_ui["run_config"]["selected_backend"] == "verilog"
    assert block_ui["run_config"]["backends"]["python"]["input_format"] == "schematic"
    assert block_ui["run_config"]["backends"]["verilog"]["netlist_format"] == "chiplib.netlist"
    assert block_ui["run_config"]["probes"] == ["logic"]
    assert block_ui["editor"]["schema"] == "components.block_ui.editor"
    assert block_ui["editor"]["source_of_truth"] == "normalized_design"
    assert block_ui["editor"]["palette"]["missing_data_policy"] == "show_status_warning"
    assert "74xx" in block_ui["editor"]["palette"]["default_groups"]
    assert {"tool": "export_block_ui", "cli_equivalent": "export-block-ui JSON_FILE"} in block_ui["editor"]["mcp_ready_tools"]
    assert block_ui["editor"]["current_design"]["chips"] == ["U1"]
    assert block_ui["editor"]["current_design"]["buses"] == ["DATA"]


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
    assert imported["run_config"]["default_backend"] == "verilog"
    assert imported["run_config"]["selected_backend"] == "verilog"
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


def test_block_ui_import_accepts_visual_endpoint_wires():
    block_ui = {
        "format": "components.block_ui",
        "version": 1,
        "design": {"name": "visual-wire"},
        "blocks": [
            {"id": "U1", "type": "chip", "part": "74HC00", "layout": {"x": 10, "y": 20}},
            {"id": "SIG", "type": "bus", "width": 1, "layout": {"x": 80, "y": 20}},
            {"id": "VCC", "type": "rail", "value": 1},
            {"id": "GND", "type": "rail", "value": 0},
        ],
        "wires": [
            {
                "id": "W1",
                "endpoint_details": [
                    {"kind": "pin", "block": "U1", "number": 1},
                    {"kind": "bus", "block": "SIG", "terminal": 0},
                ],
                "layout": {"points": [[10, 20], [80, 20]]},
            },
            {"id": "W2", "endpoints": [{"kind": "rail", "rail": "VCC"}, {"kind": "pin", "chip": "U1", "pin": 14}]},
            {"id": "W3", "endpoints": ["GND", "U1:7"]},
        ],
    }

    imported = Design.from_block_ui(block_ui).to_dict()

    assert imported["connect"] == ["U1:1 -> SIG:0", "VCC -> U1:14", "GND -> U1:7"]
    assert imported["layout"]["blocks"]["U1"] == {"x": 10, "y": 20}
    assert imported["layout"]["wires"]["W1"] == {"points": [[10, 20], [80, 20]]}


def test_block_ui_editor_metadata_lists_safe_actions_and_gates():
    block_ui = Design.from_dict(small_design()).to_block_ui()
    editor = block_ui["editor"]
    actions = {action["name"]: action for action in editor["actions"]}

    assert {"place_chip", "place_bus", "connect", "add_probe", "run"} <= set(actions)
    assert actions["connect"]["requires"] == ["endpoint_a", "endpoint_b"]
    assert {"validate", "snapshot", "run", "probe", "export-netlist", "export-verilog"} <= set(editor["validation_gates"])
    assert {"component_catalog", "component_detail", "validate_design", "run_design"} <= {
        item["tool"] for item in editor["mcp_ready_tools"]
    }
    rules = " ".join(editor["student_rules"])
    assert "real package pins" in rules
    assert "missing datasheet" in rules


def run_all():
    test_design_exports_block_ui_with_blocks_wires_and_layout()
    test_block_ui_import_preserves_design_fields_and_layout()
    test_module_helpers_round_trip_block_ui_contract()
    test_block_ui_import_accepts_visual_endpoint_wires()
    test_block_ui_editor_metadata_lists_safe_actions_and_gates()


if __name__ == "__main__":
    run_all()
    print("Components block UI tests passed")
