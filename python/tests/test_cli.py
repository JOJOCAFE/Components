"""CLI smoke tests for schematic JSON designs."""

from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from chiplib import cli


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


def small_circuit_package():
    return {
        "schema": "components.lib.circuit",
        "id": "cli-circuit",
        "chips": [{"ref": "U1", "part": "74HC04"}],
        "wiring": [{"net": "Y", "connections": ["U1.1", "U1.2"]}],
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

        block_out = Path(tmp) / "small.block.json"
        export_block = subprocess.run(
            [sys.executable, "-B", "-m", "chiplib.cli", "export-block-ui", str(path), "-o", str(block_out)],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            capture_output=True,
            check=False,
        )
        assert export_block.returncode == 0, export_block.stderr
        block_ui = json.loads(block_out.read_text(encoding="utf-8"))
        assert block_ui["format"] == "components.block_ui"
        assert block_ui["blocks"][0]["id"] == "U1"

        import_out = Path(tmp) / "from_block.json"
        import_block = subprocess.run(
            [sys.executable, "-B", "-m", "chiplib.cli", "import-block-ui", str(block_out), "-o", str(import_out)],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            capture_output=True,
            check=False,
        )
        assert import_block.returncode == 0, import_block.stderr
        imported = json.loads(import_out.read_text(encoding="utf-8"))
        assert imported["chips"]["U1"]["part"] == "74HC00"
        assert imported["connect"] == small_cli_schematic()["connect"]

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


def test_cli_circuit_faults_reports_good_and_bad_circuits():
    with tempfile.TemporaryDirectory() as tmp:
        good = Path(tmp) / "good.circuit.json"
        good.write_text(json.dumps(small_circuit_package()), encoding="utf-8")
        result = run_cli(good, "circuit-faults")
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert data["checks"]["pin_number_truth"]["status"] == "pass"

        bad = Path(tmp) / "bad.circuit.json"
        circuit = small_circuit_package()
        circuit["wiring"][0]["connections"] = ["U1.99"]
        bad.write_text(json.dumps(circuit), encoding="utf-8")
        result = run_cli(bad, "circuit-faults")
        assert result.returncode == 2
        data = json.loads(result.stdout)
        assert data["ok"] is False
        assert data["checks"]["pin_number_truth"]["status"] == "fail"


def test_cli_db_summary_and_part_lookup():
    summary = subprocess.run(
        [sys.executable, "-B", "-m", "chiplib.cli", "db"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert summary.returncode == 0, summary.stderr
    summary_data = json.loads(summary.stdout)
    assert summary_data["format"] == "db.summary"
    parts = [item["part"] for item in summary_data["components"]]
    assert {"62256", "74HC00", "74HC04", "74HC161", "74HC245", "AT28C256"}.issubset(set(parts))

    part = subprocess.run(
        [sys.executable, "-B", "-m", "chiplib.cli", "db", "74HC00"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert part.returncode == 0, part.stderr
    part_data = json.loads(part.stdout)
    assert part_data["part"] == "74HC00"
    assert part_data["missing_properties"] == []

    audit = subprocess.run(
        [sys.executable, "-B", "-m", "chiplib.cli", "db", "--audit"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert audit.returncode == 0, audit.stderr
    audit_data = json.loads(audit.stdout)
    assert audit_data["format"] == "db.audit"
    assert audit_data["ok"] is True
    assert "legacy_parts_missing_db" in audit_data["coverage"]

    status = subprocess.run(
        [sys.executable, "-B", "-m", "chiplib.cli", "db", "--status"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert status.returncode == 0, status.stderr
    status_data = json.loads(status.stdout)
    assert status_data["format"] == "db.status"
    assert status_data["ok"] is True

    catalog = subprocess.run(
        [sys.executable, "-B", "-m", "chiplib.cli", "db", "--catalog", "--group", "virtual"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert catalog.returncode == 0, catalog.stderr
    catalog_data = json.loads(catalog.stdout)
    assert catalog_data["format"] == "components.db.catalog"
    assert catalog_data["group"] == "virtual"
    assert "Probe" in {item["part"] for item in catalog_data["components"]}

    student_catalog = subprocess.run(
        [sys.executable, "-B", "-m", "chiplib.cli", "db", "--student", "--group", "virtual"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert student_catalog.returncode == 0, student_catalog.stderr
    student_data = json.loads(student_catalog.stdout)
    assert student_data["format"] == "components.db.student_catalog"
    assert student_data["group"] == "virtual"
    probe = next(item for item in student_data["components"] if item["part"] == "Probe")
    assert probe["readiness"] == "usable"
    assert probe["capabilities"]["can_simulate"] is True

    detail = subprocess.run(
        [sys.executable, "-B", "-m", "chiplib.cli", "db", "74HC00", "--detail"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert detail.returncode == 0, detail.stderr
    detail_data = json.loads(detail.stdout)
    assert detail_data["format"] == "components.db.component"
    assert detail_data["db_path"] == "DB/74xx/74HC00/definition/definition.json"

    digital = subprocess.run(
        [sys.executable, "-B", "-m", "chiplib.cli", "db", "74HC245", "--digital"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert digital.returncode == 0, digital.stderr
    definition_data = json.loads(digital.stdout)
    assert definition_data["schema"] == "db.component.digital"
    assert definition_data["part"] == "74HC245"
    assert definition_data["validation"]["ok"] is True
    assert "svg_pinout" in definition_data["generation"]["targets"]

    package = subprocess.run(
        [sys.executable, "-B", "-m", "chiplib.cli", "db", "74HC245", "--package"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert package.returncode == 0, package.stderr
    package_data = json.loads(package.stdout)
    assert package_data["format"] == "db.component.package"
    assert package_data["layers"]["tests"]["truth_table"]["part"] == "74HC245"

    virtual_package = subprocess.run(
        [sys.executable, "-B", "-m", "chiplib.cli", "db", "Probe", "--package"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert virtual_package.returncode == 0, virtual_package.stderr
    virtual_package_data = json.loads(virtual_package.stdout)
    assert virtual_package_data["format"] == "db.component.package"
    assert virtual_package_data["definition"]["schema"] == "db.component.definition"
    assert virtual_package_data["definition"]["validation"]["ok"] is True
    assert virtual_package_data["layers"]["simulation"]["service"] == "sim.probe"

    generated = subprocess.run(
        [sys.executable, "-B", "-m", "chiplib.cli", "db", "74HC245", "--generate"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert generated.returncode == 0, generated.stderr
    generated_data = json.loads(generated.stdout)
    assert generated_data["format"] == "db.component.generated"
    assert generated_data["artifacts"]["verilog_wrapper"]["module"] == "ttl_74hc245"


class FakeDesignService:
    def __init__(self):
        self.calls = []

    def validate(self, json_file: str):
        self.calls.append(("validate", json_file))
        return {"ok": True, "command": "validate"}

    def snapshot(self, json_file: str):
        self.calls.append(("snapshot", json_file))
        return {"command": "snapshot"}

    def run(self, json_file: str, *, steps="all"):
        self.calls.append(("run", json_file, steps))
        return {"ok": True, "command": "run"}

    def probe(self, json_file: str):
        self.calls.append(("probe", json_file))
        return {"command": "probe"}

    def export_json(self, json_file: str):
        self.calls.append(("export_json", json_file))
        return {"command": "export-json"}

    def export_block_ui(self, json_file: str):
        self.calls.append(("export_block_ui", json_file))
        return {"format": "components.block_ui"}

    def import_block_ui(self, json_file: str):
        self.calls.append(("import_block_ui", json_file))
        return {"command": "import-block-ui"}

    def export_netlist(self, json_file: str):
        self.calls.append(("export_netlist", json_file))
        return {"format": "chiplib.netlist"}

    def export_verilog(self, json_file: str):
        self.calls.append(("export_verilog", json_file))
        return {"ok": True, "verilog": "module fake();\n"}


def run_cli_main(fake: FakeDesignService, *args: str):
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        status = cli.main(list(args), design_service=fake)
    return status, stdout.getvalue()


def test_cli_design_commands_route_through_service_boundary():
    fake = FakeDesignService()
    commands = [
        ("validate", ["validate", "small.json"], ("validate", "small.json")),
        ("snapshot", ["snapshot", "small.json"], ("snapshot", "small.json")),
        ("run", ["run", "--steps", "none", "small.json"], ("run", "small.json", [])),
        ("probe", ["probe", "small.json"], ("probe", "small.json")),
        ("export-json", ["export-json", "small.json"], ("export_json", "small.json")),
        ("export-block-ui", ["export-block-ui", "small.json"], ("export_block_ui", "small.json")),
        ("import-block-ui", ["import-block-ui", "small.json"], ("import_block_ui", "small.json")),
        ("export-netlist", ["export-netlist", "small.json"], ("export_netlist", "small.json")),
        ("export-verilog", ["export-verilog", "small.json"], ("export_verilog", "small.json")),
    ]

    for command, args, expected_call in commands:
        status, stdout = run_cli_main(fake, *args)
        assert status == 0, command
        assert stdout, command
        assert fake.calls[-1] == expected_call

    status, stdout = run_cli_main(fake, "export-verilog", "small.json", "--text")
    assert status == 0
    assert stdout == "module fake();\n"
    assert fake.calls[-1] == ("export_verilog", "small.json")


def run_all():
    test_cli_validate_snapshot_run_probe_and_export_json()
    test_cli_db_summary_and_part_lookup()
    test_cli_design_commands_route_through_service_boundary()


if __name__ == "__main__":
    run_all()
    print("Components Python CLI tests passed")
