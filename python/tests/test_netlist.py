"""Tests for normalized netlist and first-pass Verilog export."""

from pathlib import Path
import shutil
import subprocess
import tempfile

from chiplib.design import Design


def netlist_schematic():
    return {
        "name": "netlist-small",
        "chips": {
            "U1": {"part": "74HC00", "label": "NAND"},
            "U2": {"part": "74HC04", "label": "INV"},
        },
        "buses": {"DATA": {"width": 4}},
        "aliases": {"A": "U1:1", "B": "U1:2", "Y": "U1:3", "INV_IN": "U2:1"},
        "connect": [
            "A -> DATA:0",
            "B -> DATA:1",
            "Y -> INV_IN",
            "U2:2 -> DATA:2",
            "VCC -> U1:14, U2:14",
            "GND -> U1:7, U2:7",
        ],
        "pullups": ["DATA:0"],
        "pulldowns": ["DATA:3"],
        "inputs": {"power_on": ["A = 1", "B = 1"]},
        "input_sets": {
            "front_panel": {
                "channels": [
                    {"index": 0, "name": "SW_A", "to": "A", "initial": 1},
                    {"index": 1, "name": "SW_B", "to": "B", "initial": 1},
                ]
            }
        },
        "probes": {"logic": [{"name": "nand_y", "target": "Y"}, {"name": "data2", "target": "DATA:2"}]},
        "displays": {"leds": {"type": "led_bank", "signals": ["DATA:0", "DATA:1", "DATA:2"]}},
        "steps": ["apply power_on", "settle", "probe"],
    }


def test_design_to_netlist_exports_chips_nets_buses_metadata_and_validation():
    design = Design.from_dict(netlist_schematic())

    netlist = design.to_netlist()
    assert netlist["format"] == "chiplib.netlist"
    assert netlist["version"] == 1
    assert netlist["validation"]["ok"] is True

    chips = {chip["ref"]: chip for chip in netlist["chips"]}
    assert chips["U1"]["part"] == "74HC00"
    assert chips["U1"]["pins"][0]["number"] == 1
    assert chips["U1"]["pins"][0]["name"] == "1A"

    buses = {bus["name"]: bus for bus in netlist["buses"]}
    assert buses["DATA"]["width"] == 4

    nets = {net["name"]: net for net in netlist["nets"]}
    assert nets["bus:DATA[0]"]["kind"] == "bus"
    assert nets["bus:DATA[0]"]["bus"] == "DATA"
    assert nets["bus:DATA[0]"]["index"] == 0
    assert {"chip": "U1", "pin": 1, "name": "1A", "direction": "in", "ref": "U1:1"} in nets["bus:DATA[0]"]["pins"]
    assert nets["bus:DATA[0]"]["pulls"] == [{"source": "bus:DATA[0]", "value": 1}]
    assert nets["bus:DATA[3]"]["pulls"] == [{"source": "bus:DATA[3]", "value": 0}]
    assert any(source["name"] == "rail:VCC->U1:14" for source in nets["U1:14"]["sources"])

    assert netlist["input_sets"]["front_panel"]["channels"][0]["name"] == "SW_A"
    assert netlist["probes"]["logic"][0]["name"] == "nand_y"
    assert netlist["displays"]["leds"]["type"] == "led_bank"


def test_design_from_netlist_round_trips_canonical_design_json():
    design = Design.from_dict(netlist_schematic())
    restored = Design.from_netlist(design.to_netlist())

    assert restored.to_dict() == design.to_dict()
    assert restored.to_netlist()["name"] == "netlist-small"


def test_design_to_verilog_exports_known_gate_instances_and_testbench():
    design = Design.from_dict(netlist_schematic())

    exported = design.to_verilog()
    verilog = exported["verilog"]
    assert exported["ok"] is True
    assert exported["unsupported"] == []
    assert "module netlist_small();" in verilog
    assert "ttl_74hc00" in verilog
    assert " U1 (" in verilog
    assert ".A({" in verilog
    assert "ttl_74hc04" in verilog
    assert " U2 (" in verilog
    assert "module tb_netlist_small();" in exported["testbench"]


def test_design_to_verilog_reports_unsupported_parts():
    design = Design.from_dict({
        "name": "unsupported",
        "chips": {"U1": {"part": "74HC14"}},
    })

    exported = design.to_verilog()
    assert exported["ok"] is False
    assert exported["unsupported"] == [{"ref": "U1", "part": "74HC14", "reason": "no Verilog port mapping"}]


def test_design_from_kicad_netlist_imports_chip_values_and_connection_rules():
    text = """(export (version "E")
  (components
    (comp (ref "U1")
      (value "74HC00")
    )
    (comp (ref "U2")
      (value "74HC04")
    )
  )
  (nets
    (net (code "1") (name "SIG")
      (node (ref "U1") (pin "3"))
      (node (ref "U2") (pin "1"))
    )
    (net (code "2") (name "VCC")
      (node (ref "U1") (pin "14"))
      (node (ref "U2") (pin "14"))
    )
  )
)"""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "small.net"
        path.write_text(text, encoding="utf-8")
        design = Design.from_kicad_netlist(path, name="small_kicad")

    assert design.name == "small_kicad"
    assert design.chips == {"U1": {"part": "74HC00"}, "U2": {"part": "74HC04"}}
    assert design.connections == ["SIG -> U1:3, U2:1", "VCC -> U1:14, U2:14"]
    assert design.validate()["ok"] is True


def test_rv8gr_v2_kicad_netlist_smoke_when_available():
    path = Path(__file__).resolve().parents[3] / "RV8/RV8GR-V2/Kicad/RV8GR-V2.net"
    if not path.exists():
        return

    design = Design.from_kicad_netlist(path, name="rv8gr_v2_kicad_smoke")
    validation = design.validate()
    netlist = design.to_netlist()
    verilog = design.to_verilog()

    assert validation["ok"] is True
    assert len(design.chips) == 36
    assert len(design.connections) == 159
    assert len(netlist["chips"]) == 36
    assert netlist["board_errors"] == []
    assert verilog["ok"] is True
    assert verilog["unsupported"] == []
    for module in (
        "ttl_74hc157",
        "ttl_74hc161",
        "ttl_74hc164",
        "ttl_74hc21",
        "ttl_74hc245",
        "ttl_74hc283",
        "ttl_74hc541",
        "ttl_74hc574",
        "ttl_74hc688",
        "ttl_74hc74",
        "mem_62256",
        "mem_at28c256",
    ):
        assert module in verilog["verilog"]

    iverilog = shutil.which("iverilog")
    if iverilog is None:
        return
    with tempfile.TemporaryDirectory() as tmp:
        top = Path(tmp) / "rv8gr_v2_chip_level.v"
        top.write_text(verilog["verilog"] + "\n" + verilog["testbench"], encoding="utf-8")
        root = Path(__file__).resolve().parents[2]
        cmd = [
            iverilog,
            "-g2012",
            "-Wall",
            "-o",
            str(Path(tmp) / "rv8gr_v2_chip_level.vvp"),
            *[str(root / "74HC" / name) for name in (
                "74hc00.v",
                "74hc04.v",
                "74hc21.v",
                "74hc32.v",
                "74hc74.v",
                "74hc86.v",
                "74hc157.v",
                "74hc161.v",
                "74hc164.v",
                "74hc245.v",
                "74hc283.v",
                "74hc541.v",
                "74hc574.v",
                "74hc688.v",
            )],
            str(root / "Memory" / "62256.v"),
            str(root / "Memory" / "at28c256.v"),
            str(top),
        ]
        compiled = subprocess.run(cmd, text=True, capture_output=True, check=False)
        assert compiled.returncode == 0, compiled.stderr


def run_all():
    test_design_to_netlist_exports_chips_nets_buses_metadata_and_validation()
    test_design_from_netlist_round_trips_canonical_design_json()
    test_design_to_verilog_exports_known_gate_instances_and_testbench()
    test_design_to_verilog_reports_unsupported_parts()
    test_design_from_kicad_netlist_imports_chip_values_and_connection_rules()
    test_rv8gr_v2_kicad_netlist_smoke_when_available()


if __name__ == "__main__":
    run_all()
    print("Components Python netlist tests passed")
