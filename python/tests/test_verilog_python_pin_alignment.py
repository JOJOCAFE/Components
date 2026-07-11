"""Cross-check package-local Verilog exports against Python chip pin models."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

from chiplib.db import load_digital_definition


ROOT = Path(__file__).resolve().parents[2]
DB_ROOT = ROOT / "DB"
MODEL_GROUPS = {"74xx", "Memory"}
LEGACY_VERILOG_74XX = ROOT / "Verilog" / "74xx"

PY_TO_DB_DIRECTION = {
    "in": "input",
    "out": "output",
    "bidir": "bidirectional",
    "power": "power",
    "nc": "nc",
    "passive": "passive",
}

EXPORT_COMPATIBLE_DIRECTIONS = {
    "input": {"input", "bidirectional"},
    "output": {"output", "bidirectional"},
    "inout": {"bidirectional"},
    "bidirectional": {"bidirectional"},
}


def _package_dirs() -> list[Path]:
    return sorted(
        path.parent.parent
        for path in DB_ROOT.glob("*/*/simulation/model.v")
        if path.parent.parent.parent.name in MODEL_GROUPS
        and (path.parent / "model.py").exists()
        and (path.parent / "netlist.json").exists()
        and (path.parent.parent / "definition" / "definition.json").exists()
    )


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_python_chip(part_dir: Path):
    model_path = part_dir / "simulation" / "model.py"
    module_name = f"_pin_alignment_{part_dir.parent.name.lower()}_{part_dir.name.lower()}"
    spec = importlib.util.spec_from_file_location(module_name, model_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.create("U")


def _strip_verilog_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"//.*", "", text)


def _split_top_level_commas(text: str) -> list[str]:
    items: list[str] = []
    start = 0
    depth = 0
    for index, char in enumerate(text):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth = max(0, depth - 1)
        elif char == "," and depth == 0:
            items.append(text[start:index])
            start = index + 1
    items.append(text[start:])
    return items


def _find_module_header(text: str) -> tuple[str, str]:
    match = re.search(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)\b", text)
    assert match is not None, "Verilog model has no module declaration"
    index = match.end()

    while index < len(text) and text[index].isspace():
        index += 1
    if index < len(text) and text[index] == "#":
        index += 1
        while index < len(text) and text[index].isspace():
            index += 1
        assert index < len(text) and text[index] == "(", "Malformed Verilog parameter block"
        depth = 0
        while index < len(text):
            if text[index] == "(":
                depth += 1
            elif text[index] == ")":
                depth -= 1
                if depth == 0:
                    index += 1
                    break
            index += 1

    while index < len(text) and text[index].isspace():
        index += 1
    assert index < len(text) and text[index] == "(", "Verilog module has no port list"

    start = index + 1
    depth = 1
    index += 1
    while index < len(text) and depth:
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
        index += 1
    assert depth == 0, "Unclosed Verilog module port list"
    return match.group(1), text[start:index - 1]


def _verilog_module_ports(path: Path) -> tuple[str, set[str]]:
    text = _strip_verilog_comments(path.read_text(encoding="utf-8"))
    module_name, header = _find_module_header(text)
    ports: set[str] = set()
    ignored = {"input", "output", "inout", "wire", "reg", "logic", "signed"}

    for item in _split_top_level_commas(header):
        item = re.sub(r"\[[^\]]*\]", " ", item)
        tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_$]*", item)
        names = [token for token in tokens if token not in ignored and not token.startswith("$")]
        if names:
            ports.add(names[-1])

    for _, declaration in re.findall(r"\b(input|output|inout)\b\s+([^;]+);", text):
        declaration = re.sub(r"\[[^\]]*\]", " ", declaration)
        declaration = re.sub(r"\b(?:wire|reg|logic|signed)\b", " ", declaration)
        for item in _split_top_level_commas(declaration):
            tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_$]*", item)
            if tokens:
                ports.add(tokens[-1])

    return module_name, ports


def _embedded_pinout_table(path: Path) -> dict[int, str]:
    pins: dict[int, str] = {}
    inside = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "// Embedded pinout documentation.":
            inside = True
            continue
        if inside and line.startswith("`timescale"):
            break
        if not inside or not line.startswith("//"):
            continue
        match = re.match(r"\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|", line[2:].strip())
        if match:
            pins[int(match.group(1))] = match.group(2).strip()
    return pins


def _is_internal_placeholder(port: dict, pin_number: int) -> bool:
    if pin_number != 0:
        return False
    note = str(port.get("note", "")).lower()
    return "internal" in note or "placeholder" in note


def _assert_export_pin_compatible(part: str, port: dict, pin_number: int, db_pin: dict, py_pin) -> None:
    export_direction = port["direction"]
    compatible = EXPORT_COMPATIBLE_DIRECTIONS.get(export_direction)
    assert compatible is not None, f"{part}.{port['name']} has unknown export direction {export_direction!r}"

    assert db_pin["direction"] in compatible, (
        f"{part}.{port['name']} maps pin {pin_number} to DB direction "
        f"{db_pin['direction']!r}, expected one of {sorted(compatible)}"
    )
    py_direction = PY_TO_DB_DIRECTION.get(py_pin.direction, py_pin.direction)
    assert py_direction in compatible, (
        f"{part}.{port['name']} maps pin {pin_number} to Python direction "
        f"{py_pin.direction!r}, expected one of {sorted(compatible)}"
    )

def test_all_package_verilog_exports_match_python_pin_models():
    packages = _package_dirs()
    assert len(packages) == 70

    for part_dir in packages:
        part = part_dir.name
        definition = load_digital_definition(part)
        netlist = _load_json(part_dir / "simulation" / "netlist.json")
        chip = _load_python_chip(part_dir)
        verilog_module, verilog_ports = _verilog_module_ports(part_dir / "simulation" / "model.v")

        db_pins = {pin["number"]: pin for pin in definition["pins"]}
        assert set(chip.pins) == set(db_pins), f"{part} Python pins do not match DB pin numbers"
        for pin_number, db_pin in db_pins.items():
            py_pin = chip.pins[pin_number]
            assert py_pin.name == db_pin["name"], (
                f"{part} pin {pin_number} Python name {py_pin.name!r} "
                f"does not match DB name {db_pin['name']!r}"
            )
            assert PY_TO_DB_DIRECTION.get(py_pin.direction, py_pin.direction) == db_pin["direction"], (
                f"{part} pin {pin_number} Python direction {py_pin.direction!r} "
                f"does not match DB direction {db_pin['direction']!r}"
            )
            assert py_pin.spec.active_low is bool(db_pin.get("active_low", False)), (
                f"{part} pin {pin_number} Python active_low flag does not match DB"
            )

        verilog = netlist["verilog"]
        assert verilog["module"] == verilog_module, f"{part} netlist module does not match Verilog module"
        export = verilog["export"]
        export_ports = export["ports"]
        export_port_names = {port["name"] for port in export_ports}
        if verilog_ports:
            assert export_port_names <= verilog_ports, (
                f"{part} netlist exports missing Verilog ports {sorted(export_port_names - verilog_ports)}"
            )

        for port in export_ports:
            assert port["pins"], f"{part}.{port['name']} has no mapped pins"
            for pin_number in port["pins"]:
                if _is_internal_placeholder(port, pin_number):
                    continue
                assert pin_number in db_pins, f"{part}.{port['name']} maps unknown DB pin {pin_number}"
                assert pin_number in chip.pins, f"{part}.{port['name']} maps unknown Python pin {pin_number}"
                _assert_export_pin_compatible(part, port, pin_number, db_pins[pin_number], chip.pins[pin_number])

        output_pins = set(export.get("output_pins", []))
        mapped_pins = {
            pin_number
            for port in export_ports
            for pin_number in port["pins"]
        }
        assert output_pins <= mapped_pins, f"{part} output_pins includes pins not present in export ports"


def test_legacy_74xx_verilog_pinout_headers_match_db_definitions():
    verilog_files = sorted(LEGACY_VERILOG_74XX.glob("*.v"))
    assert len(verilog_files) == 65

    for verilog_path in verilog_files:
        part = verilog_path.stem.upper()
        definition_path = DB_ROOT / "74xx" / part / "definition" / "definition.json"
        assert definition_path.exists(), f"{part} has legacy Verilog but no DB definition"
        db_pins = {
            pin["number"]: pin["name"]
            for pin in load_digital_definition(part)["pins"]
        }
        header_pins = _embedded_pinout_table(verilog_path)
        assert header_pins == db_pins, f"{part} legacy Verilog embedded pinout does not match DB"


def run_all():
    test_all_package_verilog_exports_match_python_pin_models()
    test_legacy_74xx_verilog_pinout_headers_match_db_definitions()


if __name__ == "__main__":
    run_all()
    print("Components Verilog/Python pin alignment tests passed")
