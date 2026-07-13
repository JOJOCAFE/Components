#!/usr/bin/env python3
"""Run DB truth vectors against package-local Verilog models with Icarus."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "VERILOG_BEHAVIOR_CROSSCHECK_REPORT.md"
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "tools"))

from python_behavior_crosscheck import bus_aliases, normalize_bus_expected  # noqa: E402
from chiplib.db import resolve_definition_source  # noqa: E402


ANNOTATION_EXPECT_KEYS = {
    "busy_updates",
    "no_write",
    "write",
    "write_pending",
}


GENERIC_PIN_ALIASES = {
    "A": ("1A", "A0", "A", "D0", "D1"),
    "B": ("1B", "B0", "B", "D1"),
    "C": ("1C", "C", "D2"),
    "D": ("1D", "D", "D3"),
    "Y": ("1Y", "Y", "Q0", "QA"),
    "/LD": ("/LOAD",),
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def import_model(path: Path):
    name = "verilog_behavior_" + "_".join(path.parts[-4:-2])
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"//.*", "", text)


def split_commas(text: str) -> list[str]:
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


def verilog_port_directions(path: Path) -> dict[str, str]:
    text = strip_comments(path.read_text(encoding="utf-8"))
    directions: dict[str, str] = {}
    for direction, declaration in re.findall(r"\b(input|output|inout)\b\s+([^;]+);", text):
        declaration = re.sub(r"\[[^\]]*\]", " ", declaration)
        declaration = re.sub(r"\b(?:wire|reg|logic|signed)\b", " ", declaration)
        for item in split_commas(declaration):
            tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_$]*", item)
            if tokens:
                directions[tokens[-1]] = direction
    match = re.search(r"\bmodule\s+\w+\s*(?:#\s*\([^;]*?\)\s*)?\((.*?)\);", text, flags=re.DOTALL)
    if match:
        for item in split_commas(match.group(1)):
            clean = re.sub(r"\[[^\]]*\]", " ", item)
            tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_$]*", clean)
            if len(tokens) >= 2 and tokens[0] in {"input", "output", "inout"}:
                directions[tokens[-1]] = tokens[0]
    return directions


def package_dirs() -> list[Path]:
    return sorted(
        path.parent.parent
        for path in (ROOT / "lib" / "standard").glob("*/*/simulation/model.v")
        if path.parent.parent.parent.name in {"74xx", "memory"}
        and (path.parent / "model.py").exists()
        and (path.parent / "netlist.json").exists()
        and (path.parent.parent / "tests" / "truth_table.json").exists()
    )


def parse_value(value: Any, width: int, *, broadcast_scalar: bool = False) -> tuple[str, bool]:
    if value == "Z":
        return f"{width}'h{'z' * ((width + 3) // 4)}", True
    if isinstance(value, str) and value.startswith("0x"):
        number = int(value, 16)
    else:
        number = int(value)
        if broadcast_scalar and width > 1:
            number = ((1 << width) - 1) if number else 0
    return f"{width}'h{number:x}", False


def scalar_value(value: Any) -> tuple[str, bool]:
    if value == "Z":
        return "1'bz", True
    return ("1'b1" if int(value) else "1'b0"), False


def build_maps(part_dir: Path, definition: dict[str, Any], netlist: dict[str, Any], chip: Any):
    ports = netlist["verilog"]["export"]["ports"]
    port_by_name = {port["name"]: port for port in ports}
    pin_to_port: dict[int, tuple[str, int]] = {}
    for port in ports:
        for bit, pin in enumerate(port["pins"]):
            if pin:
                pin_to_port[int(pin)] = (port["name"], bit)
    pin_name_to_number = {pin["name"]: int(pin["number"]) for pin in definition["pins"]}
    aliases = bus_aliases(definition, chip)
    alias_to_pins: dict[str, list[int]] = {}
    for alias, names in aliases.items():
        pins = [pin_name_to_number[name] for name in names if name in pin_name_to_number]
        if len(pins) > 1:
            alias_to_pins[alias] = pins
    grouped: dict[str, list[tuple[int, int]]] = {}
    for pin in definition["pins"]:
        name = str(pin["name"])
        number = int(pin["number"])
        match = re.fullmatch(r"(\d+)([A-Za-z]+)", name)
        if match:
            index, suffix = match.groups()
            grouped.setdefault(suffix, []).append((int(index), number))
        match = re.fullmatch(r"/Y(\d+)", name)
        if match:
            grouped.setdefault("/Y", []).append((int(match.group(1)), number))
        match = re.fullmatch(r"(?:DQ|I/O)(\d+)", name)
        if match:
            grouped.setdefault("DQ", []).append((int(match.group(1)), number))
    for alias, items in grouped.items():
        if alias not in alias_to_pins and len(items) > 1:
            alias_to_pins[alias] = [number for _, number in sorted(items)]
    return port_by_name, pin_to_port, pin_name_to_number, alias_to_pins


def resolve_signal(
    key: str,
    port_by_name: dict[str, dict[str, Any]],
    pin_to_port: dict[int, tuple[str, int]],
    pin_name_to_number: dict[str, int],
    alias_to_pins: dict[str, list[int]],
    *,
    prefer_exact_pin: bool = False,
) -> tuple[str, int, str] | None:
    pin_number = pin_name_to_number.get(key)
    if prefer_exact_pin and pin_number is not None and pin_number in pin_to_port:
        port_name, bit = pin_to_port[pin_number]
        if key not in port_by_name or len(port_by_name[key]["pins"]) > 1:
            expr = port_name if len(port_by_name[port_name]["pins"]) == 1 else f"{port_name}[{bit}]"
            return port_name, 1, expr

    if key in port_by_name:
        width = len(port_by_name[key]["pins"])
        return key, width, key

    if key in alias_to_pins:
        pins = alias_to_pins[key]
        mapped = [pin_to_port.get(pin) for pin in pins]
        if all(item is not None for item in mapped):
            names = {item[0] for item in mapped if item is not None}
            bits = [item[1] for item in mapped if item is not None]
            if len(names) == 1 and bits == list(range(len(bits))):
                name = next(iter(names))
                return name, len(bits), name
            if len(names) == 1:
                name = next(iter(names))
                exprs = [
                    name if len(port_by_name[name]["pins"]) == 1 else f"{name}[{bit}]"
                    for bit in reversed(bits)
                ]
                return name, len(bits), "{" + ", ".join(exprs) + "}"

    for alias in GENERIC_PIN_ALIASES.get(key, ()):
        pin_number = pin_name_to_number.get(alias)
        if pin_number is not None and pin_number in pin_to_port:
            port_name, bit = pin_to_port[pin_number]
            expr = port_name if len(port_by_name[port_name]["pins"]) == 1 else f"{port_name}[{bit}]"
            return port_name, 1, expr

    if pin_number is not None and pin_number in pin_to_port:
        port_name, bit = pin_to_port[pin_number]
        expr = port_name if len(port_by_name[port_name]["pins"]) == 1 else f"{port_name}[{bit}]"
        return port_name, 1, expr
    return None


def clock_port_for(part: str, port_by_name: dict[str, dict[str, Any]]) -> str | None:
    overrides = {
        "74HC193": "Down",
        "74HC4520": "CP",
        "74HC4538": "A",
        "74HC593": "CCK",
        "74HC595": "SRCLK",
        "74HC922": "Oscillator",
    }
    if overrides.get(part) in port_by_name:
        return overrides[part]
    for name in ("Clk", "CLK", "CP", "Clock", "SRCLK", "CCK", "Oscillator"):
        if name in port_by_name:
            return name
    return None


def should_broadcast_scalar(key: str, value: Any, width: int) -> bool:
    return (
        width > 1
        and key in GENERIC_PIN_ALIASES
        and not (isinstance(value, str) and value.startswith("0x"))
        and value != "Z"
    )


def input_assignment_priority(item: tuple[str, Any]) -> tuple[int, str]:
    key, _value = item
    normalized = key.replace("/", "").replace("_bar", "").replace(" ", "").upper()
    if any(token in normalized for token in ("CLR", "CLEAR", "RESET", "MR", "CCLR")):
        return (0, key)
    if any(token in normalized for token in ("LOAD", "CLOAD", "SHLD")):
        return (2, key)
    if normalized in {"CE", "OE", "WE"} or any(token in normalized for token in ("CLK", "CLOCK", "CK", "CP", "UP", "DOWN")):
        return (3, key)
    return (1, key)


def verilog_compare(expr: str, width: int, expected: Any, *, broadcast_scalar: bool = False) -> str:
    literal, is_z = (
        parse_value(expected, width, broadcast_scalar=broadcast_scalar)
        if width > 1
        else scalar_value(expected)
    )
    op = "===" if is_z else "!=="
    if is_z:
        return f"if ({expr} !== {literal}) begin $display(\"FAIL %0s expected {literal} got %h\", \"{expr}\", {expr}); failures = failures + 1; end"
    return f"if ({expr} !== {literal}) begin $display(\"FAIL %0s expected {literal} got %h\", \"{expr}\", {expr}); failures = failures + 1; end"


def apply_assignment(port: str, width: int, expr: str, value: Any, directions: dict[str, str], *, broadcast_scalar: bool = False) -> list[str]:
    literal, is_z = (
        parse_value(value, width, broadcast_scalar=broadcast_scalar)
        if width > 1
        else scalar_value(value)
    )
    if directions.get(port) == "inout":
        if is_z:
            return [f"drive_{port} = 1'b0;"]
        return [f"drive_{port} = 1'b1;", f"drv_{expr} = {literal};" if expr != port else f"drv_{port} = {literal};"]
    return [f"{expr} = {literal};"]


def emit_testbench(part: str, module: str, model_path: Path, definition: dict[str, Any], netlist: dict[str, Any], vectors: list[dict[str, Any]], chip: Any) -> tuple[str | None, int, int, list[str]]:
    directions = verilog_port_directions(model_path)
    port_by_name, pin_to_port, pin_name_to_number, alias_to_pins = build_maps(part_dir=model_path.parent.parent, definition=definition, netlist=netlist, chip=chip)
    clock_port = clock_port_for(part, port_by_name)
    unsupported: list[str] = []
    runnable = 0
    skipped_z = 0

    lines = ["`timescale 1ns/1ps", f"module tb_{part.lower()};", "  integer failures = 0;"]
    for port in port_by_name.values():
        name = port["name"]
        width = len(port["pins"])
        rng = "" if width == 1 else f"[{width - 1}:0] "
        direction = directions.get(name, "input" if port["direction"] == "input" else "output")
        if direction == "inout":
            lines.append(f"  reg {rng}drv_{name} = 0;")
            lines.append(f"  reg drive_{name} = 1'b0;")
            lines.append(f"  wire {rng}{name};")
            lines.append(f"  assign {name} = drive_{name} ? drv_{name} : {{{width}{{1'bz}}}};")
        elif direction == "output":
            lines.append(f"  wire {rng}{name};")
        else:
            lines.append(f"  reg {rng}{name} = {{{width}{{1'bx}}}};")
    conns = ", ".join(f".{name}({name})" for name in port_by_name)
    lines.append(f"  {module} dut({conns});")
    lines.append("  initial begin")

    for index, vector in enumerate(vectors):
        inputs = vector.get("inputs")
        expect = vector.get("expect")
        if not isinstance(inputs, dict) or not isinstance(expect, dict):
            continue
        values = list(inputs.values()) + [v for k, v in expect.items() if k not in ANNOTATION_EXPECT_KEYS]
        if any(isinstance(v, str) and not (v.startswith("0x") or v == "Z") for v in values):
            unsupported.append(f"{vector.get('name', index)}: non-literal vector")
            continue
        if vector.get("fresh") is True:
            for port in port_by_name.values():
                name = port["name"]
                direction = directions.get(name, "input" if port["direction"] == "input" else "output")
                if direction == "inout":
                    lines.append(f"    drive_{name} = 1'b0; drv_{name} = 0;")
        input_ports: set[str] = set()
        for key, value in inputs.items():
            resolved = resolve_signal(
                key,
                port_by_name,
                pin_to_port,
                pin_name_to_number,
                alias_to_pins,
                prefer_exact_pin=not (isinstance(value, str) and value.startswith("0x")),
            )
            if resolved is not None:
                input_ports.add(resolved[0])
        for port in port_by_name.values():
            name = port["name"]
            direction = directions.get(name, "input" if port["direction"] == "input" else "output")
            keep_write_drive = any(key in expect for key in ("write", "write_pending"))
            if direction == "inout" and name not in input_ports and not keep_write_drive:
                lines.append(f"    drive_{name} = 1'b0;")
        unresolved = []
        actively_driven_this_vector: set[str] = set()
        for key, value in sorted(inputs.items(), key=input_assignment_priority):
            resolved = resolve_signal(
                key,
                port_by_name,
                pin_to_port,
                pin_name_to_number,
                alias_to_pins,
                prefer_exact_pin=not (isinstance(value, str) and value.startswith("0x")),
            )
            if resolved is None:
                unresolved.append(key)
                continue
            port, width, expr = resolved
            if port == clock_port:
                continue
            broadcast_scalar = should_broadcast_scalar(key, value, width)
            _, is_z_input = (
                parse_value(value, width, broadcast_scalar=broadcast_scalar)
                if width > 1
                else scalar_value(value)
            )
            if directions.get(port) == "inout" and not is_z_input:
                actively_driven_this_vector.add(port)
            for line in apply_assignment(port, width, expr, value, directions, broadcast_scalar=broadcast_scalar):
                lines.append(f"    {line}")
        if unresolved:
            unsupported.append(f"{vector.get('name', index)}: unresolved inputs {unresolved}")
            continue
        if vector.get("clock") is True:
            if not clock_port:
                unsupported.append(f"{vector.get('name', index)}: clock requested but no clock port found")
                continue
            lines.append(f"    {clock_port} = 0; #1; {clock_port} = {{{len(port_by_name[clock_port]['pins'])}{{1'b1}}}}; #1; {clock_port} = 0;")
        lines.append("    #2;")
        for key, expected in expect.items():
            if key in ANNOTATION_EXPECT_KEYS:
                continue
            resolved = resolve_signal(
                key,
                port_by_name,
                pin_to_port,
                pin_name_to_number,
                alias_to_pins,
                prefer_exact_pin=not (isinstance(expected, str) and expected.startswith("0x")),
            )
            if resolved is None:
                unsupported.append(f"{vector.get('name', index)}: unresolved expected {key}")
                continue
            port, width, expr = resolved
            broadcast_scalar = should_broadcast_scalar(key, expected, width)
            _, is_z = (
                parse_value(expected, width, broadcast_scalar=broadcast_scalar)
                if width > 1
                else scalar_value(expected)
            )
            if is_z and directions.get(port) == "inout" and port in actively_driven_this_vector:
                lines.append(f"    drive_{port} = 1'b0; #1;")
            lines.append(f"    // {vector.get('name', index)}: {key}")
            lines.append(f"    {verilog_compare(expr, width, expected, broadcast_scalar=broadcast_scalar)}")
            if (
                is_z
                and directions.get(port) == "inout"
                and port in actively_driven_this_vector
                and "write_pending" in expect
            ):
                lines.append(f"    drive_{port} = 1'b1;")
        runnable += 1
    lines.append("    if (failures) begin $fatal(1, \"VERILOG BEHAVIOR FAILED %0d\", failures); end")
    lines.append(f"    $display(\"VERILOG BEHAVIOR PASS {part} vectors={runnable} skipped_z={skipped_z}\");")
    lines.append("    $finish;")
    lines.append("  end")
    lines.append("endmodule")
    if runnable == 0:
        return None, runnable, skipped_z, unsupported
    return "\n".join(lines) + "\n", runnable, skipped_z, unsupported


def run_part(part_dir: Path, tmp: Path, iverilog: str, vvp: str) -> dict[str, Any]:
    part = part_dir.name
    definition_path = part_dir / "definition" / "definition.json"
    definition = resolve_definition_source(load_json(definition_path), definition_path)
    netlist = load_json(part_dir / "simulation" / "netlist.json")
    truth = load_json(part_dir / "tests" / "truth_table.json")
    module_py = import_model(part_dir / "simulation" / "model.py")
    chip = module_py.create("U")
    vectors = truth.get("vectors") or []
    tb, runnable, skipped_z, unsupported = emit_testbench(
        part,
        netlist["verilog"]["module"],
        part_dir / "simulation" / "model.v",
        definition,
        netlist,
        vectors,
        chip,
    )
    row = {
        "part": part,
        "vectors": runnable,
        "skipped_z": skipped_z,
        "unsupported": unsupported,
        "result": "NO_RUNNABLE",
        "details": "-",
    }
    if tb is None:
        return row
    tb_path = tmp / f"tb_{part}.v"
    out_path = tmp / f"tb_{part}.vvp"
    tb_path.write_text(tb, encoding="utf-8")
    compiled = subprocess.run(
        [
            iverilog,
            "-g2012",
            "-Wall",
            "-o",
            str(out_path),
            *verilog_compile_inputs(part_dir),
            str(tb_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if compiled.returncode != 0:
        row["result"] = "COMPILE_FAIL"
        row["details"] = (compiled.stderr or compiled.stdout).strip()
        return row
    simulated = subprocess.run([vvp, str(out_path)], text=True, capture_output=True, check=False)
    if simulated.returncode != 0 or "VERILOG BEHAVIOR FAILED" in simulated.stdout:
        row["result"] = "FAIL"
        row["details"] = (simulated.stdout + simulated.stderr).strip()
        return row
    row["result"] = "PASS"
    row["details"] = simulated.stdout.strip().splitlines()[-1] if simulated.stdout.strip() else "-"
    return row


def verilog_compile_inputs(part_dir: Path) -> list[str]:
    model = part_dir / "simulation" / "model.v"
    text = model.read_text(encoding="utf-8")
    files: list[Path] = []
    if "mem_62256" in text and part_dir.name != "62256":
        files.append(ROOT / "lib" / "standard" / "memory" / "62256" / "simulation" / "model.v")
    files.append(model)
    return [str(path) for path in files]


def write_report(rows: list[dict[str, Any]]) -> None:
    failures = [row for row in rows if row["result"] != "PASS"]
    lines = [
        "# Verilog Behavior Cross-check Report",
        "",
        "Generated by `tools/verilog_behavior_crosscheck.py`. Each runnable DB truth vector is compiled into an Icarus Verilog testbench against the package-local `simulation/model.v` export.",
        "",
        "Note: bidirectional `Z` expectations on externally driven wires are checked by releasing the testbench driver under the same control levels before comparing the pin to high impedance.",
        "",
        "| Part | Result | Vectors | Skipped Z | Unsupported | Details |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in rows:
        detail = str(row["details"]).replace("\n", "<br>")
        lines.append(f"| {row['part']} | {row['result']} | {row['vectors']} | {row['skipped_z']} | {len(row['unsupported'])} | {detail} |")
    lines.extend(["", "## Failures", ""])
    if failures:
        for row in failures:
            lines.append(f"- {row['part']}: {row['result']} {row['details']}")
    else:
        lines.append("- none")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    iverilog = shutil.which("iverilog")
    vvp = shutil.which("vvp")
    if not iverilog or not vvp:
        print(json.dumps({"rows": 0, "failures": ["iverilog/vvp missing"], "report": str(REPORT)}, indent=2))
        return 1

    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        for part_dir in package_dirs():
            rows.append(run_part(part_dir, tmp, iverilog, vvp))
    write_report(rows)
    failures = [f"{row['part']}: {row['result']}" for row in rows if row["result"] != "PASS"]
    print(json.dumps({"rows": len(rows), "failures": failures, "report": str(REPORT)}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
