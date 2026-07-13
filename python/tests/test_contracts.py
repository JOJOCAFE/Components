"""Contract tests for service-ready example schematic fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from chiplib.design import Design
from chiplib.netlist import _verilog_mapping
from chiplib.services import VerilogExportService


ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = [
    "nand",
    "counter",
    "bus_transceiver",
    "memory_read",
    "tiny_cpu_slice",
]


def load_example(name: str) -> Design:
    path = ROOT / "examples" / "circuits" / f"{name}.json"
    return Design.from_dict(json.loads(path.read_text(encoding="utf-8")))


def test_service_ready_examples_validate_snapshot_run_netlist_and_export_verilog():
    service = VerilogExportService()
    for name in EXAMPLES:
        design = load_example(name)
        validation = design.validate()
        assert validation["ok"] is True, (name, validation)

        design = load_example(name)
        design.to_board()
        snapshot = design.snapshot()
        assert snapshot["validate"]["ok"] is True, name
        assert snapshot["board"]["chips"], name
        assert snapshot["board"]["errors"] == [], name

        run = load_example(name).run()
        assert run["ok"] is True, name
        assert run["log"], name

        netlist = load_example(name).to_netlist()
        assert netlist["format"] == "chiplib.netlist", name
        assert netlist["version"] == 1, name
        assert netlist["validation"]["ok"] is True, name
        assert netlist["board_errors"] == [], name

        exported = service.export(load_example(name))
        assert exported["ok"] is True, (name, exported["unsupported"])
        assert exported["warnings"] == [], name
        assert exported["required_files"], name
        assert exported["verilog"].startswith("`timescale 1ns/1ps"), name
        assert f"module {name}();" in exported["verilog"], name
        assert "// Embedded pinout documentation." in exported["verilog"], name
        assert "// | Pin | Name |" in exported["verilog"], name
        assert exported["testbench"].startswith("`timescale 1ns/1ps"), name


def test_design_to_verilog_uses_internal_service_boundary():
    design = load_example("nand")
    exported = design.to_verilog()

    assert exported["ok"] is True
    assert exported["warnings"] == []
    assert "lib/standard/74xx/74HC00/simulation/model.py" in exported["required_files"]
    assert "lib/standard/74xx/74HC00/simulation/model.v" in exported["required_files"]
    assert "lib/standard/74xx/74HC00/simulation/netlist.json" in exported["required_files"]
    assert "python/chiplib/core.py" in exported["required_files"]
    assert "ttl_74hc00" in exported["verilog"]


def test_seed_chip_exports_include_portable_local_models():
    design = load_example("counter")
    netlist = design.to_netlist()
    chip = netlist["chips"][0]
    assert chip["part"] == "74HC161"
    assert any(item["runtime"] == "python" and item["copy_as"] == "model.py" for item in chip["portable_files"])
    assert any(item["kind"] == "python_runtime" and item["copy_as"] == "chiplib/core.py" for item in chip["portable_files"])

    exported = VerilogExportService().export(design)
    assert "lib/standard/74xx/74HC161/simulation/model.py" in exported["required_files"]
    assert "python/chiplib/core.py" in exported["required_files"]
    assert "lib/standard/74xx/74HC161/simulation/model.v" in exported["required_files"]
    assert "lib/standard/74xx/74HC161/simulation/netlist.json" in exported["required_files"]


def test_system_exports_share_one_python_core_runtime():
    exported = VerilogExportService().export(load_example("tiny_cpu_slice"))
    assert exported["required_files"].count("python/chiplib/core.py") == 1
    assert "lib/standard/74xx/74HC161/simulation/model.py" in exported["required_files"]
    assert "lib/standard/74xx/74HC00/simulation/model.py" in exported["required_files"]
    assert "lib/standard/memory/62256/simulation/model.py" in exported["required_files"]


def test_sram_wrapper_exports_include_base_memory_verilog_dependency():
    for part in ("AS6C62256", "CY7C199"):
        exported = VerilogExportService().export(Design.from_dict({
            "name": f"{part.lower()}-wrapper",
            "chips": {"U1": {"part": part}},
        }))
        assert exported["ok"] is True, part
        assert f"lib/standard/memory/{part}/simulation/model.v" in exported["required_files"], part
        assert "lib/standard/memory/62256/simulation/model.v" in exported["required_files"], part


def test_seed_verilog_mapping_comes_from_simulation_netlist_shape():
    mapping = _verilog_mapping("74HC245")
    assert mapping is not None
    assert mapping["module"] == "ttl_74hc245"
    assert mapping["output_pins"] == [2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18]


def run_all():
    test_service_ready_examples_validate_snapshot_run_netlist_and_export_verilog()
    test_design_to_verilog_uses_internal_service_boundary()
    test_seed_chip_exports_include_portable_local_models()
    test_system_exports_share_one_python_core_runtime()
    test_seed_verilog_mapping_comes_from_simulation_netlist_shape()


if __name__ == "__main__":
    run_all()
    print("Components contract tests passed")
