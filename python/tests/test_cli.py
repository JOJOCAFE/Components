"""CLI smoke tests for schematic JSON designs."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


def small_cli_schematic():
    return {
        "name": "cli-small",
        "chips": {"U1": {"part": "74HC00"}},
        "buses": {"DATA": {"width": 2}},
        "aliases": {"A": "U1:1", "B": "U1:2", "Y": "U1:3"},
        "connect": [
            "A -> DATA:0",
            "B -> DATA:1",
            "VCC -> U1:14",
            "GND -> U1:7"
        ],
        "inputs": {"power_on": ["A = 1", "B = 1"]},
        "probes": {"logic": ["Y", "DATA:0"]},
        "steps": ["apply power_on", "settle", "probe"]
    }


def run_cli(path: Path, *args: str):
    return subprocess.run(
        [sys.executable, "-B", "-m", "chiplib.cli", *args, str(path)],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_validate_snapshot_run_probe_and_export_json():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "small.json"
        path.write_text(json.dumps(small_cli_schematic()), encoding="utf-8")

        validate = run_cli(path, "validate")
        assert validate.returncode == 0, validate.stderr
        assert json.loads(validate.stdout)["ok"] is True

        snapshot = run_cli(path, "snapshot")
        assert snapshot.returncode == 0, snapshot.stderr
        snapshot_data = json.loads(snapshot.stdout)
        assert snapshot_data["board"]["chips"][0]["ref"] == "U1"

        run = run_cli(path, "run")
        assert run.returncode == 0, run.stderr
        run_data = json.loads(run.stdout)
        assert run_data["ok"] is True
        assert run_data["log"][0]["action"] == "apply"

        probe = run_cli(path, "probe")
        assert probe.returncode == 0, probe.stderr
        probe_data = json.loads(probe.stdout)
        assert probe_data["sets"][1]["name"] == "logic"

        out = Path(tmp) / "canonical.json"
        export = subprocess.run(
            [sys.executable, "-B", "-m", "chiplib.cli", "export-json", str(path), "-o", str(out)],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            capture_output=True,
            check=False,
        )
        assert export.returncode == 0, export.stderr
        assert json.loads(out.read_text(encoding="utf-8"))["name"] == "cli-small"

        netlist_out = Path(tmp) / "small.net.json"
        export_netlist = subprocess.run(
            [sys.executable, "-B", "-m", "chiplib.cli", "export-netlist", str(path), "-o", str(netlist_out)],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            capture_output=True,
            check=False,
        )
        assert export_netlist.returncode == 0, export_netlist.stderr
        netlist = json.loads(netlist_out.read_text(encoding="utf-8"))
        assert netlist["format"] == "chiplib.netlist"
        assert netlist["chips"][0]["ref"] == "U1"

        verilog = run_cli(path, "export-verilog")
        assert verilog.returncode == 0, verilog.stderr
        verilog_data = json.loads(verilog.stdout)
        assert verilog_data["ok"] is True
        assert "ttl_74hc00" in verilog_data["verilog"]
        assert " U1 (" in verilog_data["verilog"]

        verilog_text_out = Path(tmp) / "small.v"
        export_verilog_text = subprocess.run(
            [sys.executable, "-B", "-m", "chiplib.cli", "export-verilog", str(path), "--text", "-o", str(verilog_text_out)],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            capture_output=True,
            check=False,
        )
        assert export_verilog_text.returncode == 0, export_verilog_text.stderr
        assert "module cli_small();" in verilog_text_out.read_text(encoding="utf-8")


def run_all():
    test_cli_validate_snapshot_run_probe_and_export_json()


if __name__ == "__main__":
    run_all()
    print("Components Python CLI tests passed")
