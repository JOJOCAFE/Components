"""Normalized netlist and Verilog exporters for schematic designs."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any

from .chips import create_chip
from .core import Logic, parse_bus_tag


JsonMap = dict[str, Any]


def design_to_netlist(design: Any) -> JsonMap:
    """Return a serializable netlist derived from a normalized Design."""

    board = design._board if getattr(design, "_board", None) is not None else design.to_board()
    snapshot = board.snapshot()
    pin_index = _pin_index(snapshot)
    nets: list[JsonMap] = []

    for net in sorted(snapshot["nets"], key=lambda item: item["name"]):
        name = str(net["name"])
        bus = _bus_line(name)
        nets.append({
            "name": name,
            "kind": "bus" if bus else "net",
            "bus": bus["bus"] if bus else None,
            "index": bus["index"] if bus else None,
            "value": net["value"],
            "pins": [
                _pin_endpoint(pin)
                for pin in sorted(net["pins"], key=lambda item: (item["chip"], item["number"]))
            ],
            "pulls": deepcopy(net["pulls"]),
            "sources": deepcopy(net["sources"]),
        })

    return {
        "format": "chiplib.netlist",
        "version": 1,
        "name": design.name,
        "description": design.description,
        "design": design.to_dict(),
        "chips": [
            _chip_entry(ref, spec, pin_index.get(ref, {}))
            for ref, spec in sorted(design.chips.items())
        ],
        "buses": [
            {"name": name, "width": _width(spec)}
            for name, spec in sorted(design.buses.items())
        ],
        "rails": [
            {"name": name, "value": value}
            for name, value in sorted(design.rails.items())
        ],
        "nets": nets,
        "connections": [
            {
                "rule": rule,
                "endpoints": [endpoint.snapshot() for endpoint in design._connection_endpoints(rule)],
            }
            for rule in design.connections
        ],
        "pullups": list(design.pullups),
        "pulldowns": list(design.pulldowns),
        "inputs": deepcopy(design.inputs),
        "input_sets": deepcopy(design.input_sets),
        "clocks": deepcopy(design.clocks),
        "probes": deepcopy(design.probes),
        "displays": deepcopy(design.displays),
        "expect": deepcopy(design.expect),
        "steps": list(design.steps),
        "validation": design.validate(),
        "board_errors": snapshot["errors"],
    }


def design_from_netlist(data: JsonMap, design_class: Any) -> Any:
    """Recreate a Design from a chiplib netlist.

    Netlists exported by this module keep the canonical design JSON so the
    beginner-facing script can round-trip without losing UI metadata.
    """

    if not isinstance(data, dict):
        raise ValueError("netlist root must be an object")
    if "design" in data:
        return design_class.from_dict(deepcopy(data["design"]))

    design = design_class(str(data.get("name", "netlist")))
    design.description = str(data.get("description", ""))
    design.chips = {
        str(item["ref"]): {"part": str(item["part"])}
        for item in data.get("chips", [])
        if isinstance(item, dict) and "ref" in item and "part" in item
    }
    design.buses = {
        str(item["name"]): {"width": int(item.get("width", 1))}
        for item in data.get("buses", [])
        if isinstance(item, dict) and "name" in item
    }
    design.rails = {
        str(item["name"]): _logic(item.get("value", 0))
        for item in data.get("rails", [])
        if isinstance(item, dict) and "name" in item
    }
    design.connections = [str(item.get("rule", "")) for item in data.get("connections", []) if item.get("rule")]
    design.pullups = [str(item) for item in data.get("pullups", [])]
    design.pulldowns = [str(item) for item in data.get("pulldowns", [])]
    design.inputs = deepcopy(data.get("inputs", {}))
    design.input_sets = deepcopy(data.get("input_sets", {}))
    design.clocks = deepcopy(data.get("clocks", {}))
    design.probes = deepcopy(data.get("probes", {}))
    design.displays = deepcopy(data.get("displays", {}))
    design.expect = deepcopy(data.get("expect", {}))
    design.steps = [str(item) for item in data.get("steps", [])]
    return design


def design_from_kicad_netlist(path: str | Path, design_class: Any, *, name: str | None = None) -> Any:
    """Create a Design from a KiCad generic S-expression netlist export."""

    source = Path(path)
    text = source.read_text(encoding="utf-8")
    chips = {
        ref: {"part": value}
        for ref, value in re.findall(
            r'\(comp \(ref "([^"]+)"\)\s+\(value "([^"]+)"\)',
            text,
            flags=re.S,
        )
    }
    connections: list[str] = []
    for net_name, block in re.findall(
        r'\(net \(code "[^"]+"\) \(name "([^"]+)"\)(.*?)(?=\n    \(net |\n  \)\n\))',
        text,
        flags=re.S,
    ):
        nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)\)', block)
        if nodes:
            connections.append(f"{net_name} -> " + ", ".join(f"{ref}:{pin}" for ref, pin in nodes))
    return design_class.from_dict({
        "name": name or source.stem,
        "description": f"Imported from KiCad netlist {source.name}",
        "chips": chips,
        "connect": connections,
    })


def design_to_verilog(design: Any, *, include_testbench: bool = True) -> JsonMap:
    """Export a conservative structural Verilog wrapper from a Design."""

    netlist = design.to_netlist()
    module_name = _verilog_ident(design.name or "design")
    unsupported: list[JsonMap] = []
    lines: list[str] = [
        "`timescale 1ns/1ps",
        "",
        f"module {module_name}();",
    ]

    net_names = [net["name"] for net in netlist["nets"]]
    for name in sorted(net_names):
        lines.append(f"  wire {_net_id(name)};")
    open_wires = _open_output_wires(netlist)
    for name in open_wires:
        lines.append(f"  wire {name};")
    if net_names:
        lines.append("")

    for net in netlist["nets"]:
        for source in net.get("sources", []):
            if source.get("enabled", True):
                lines.append(f"  assign {_net_id(net['name'])} = {_logic_literal(source.get('value', 'Z'))};")
        for pull in net.get("pulls", []):
            lines.append(f"  tri{1 if pull.get('value') == 1 else 0} {_net_id(net['name'])}_pull = {_net_id(net['name'])};")
    if any(net.get("sources") or net.get("pulls") for net in netlist["nets"]):
        lines.append("")

    net_for_pin = _net_for_pin(netlist)
    for chip in netlist["chips"]:
        mapping = _verilog_mapping(str(chip["part"]))
        if mapping is None:
            unsupported.append({"ref": chip["ref"], "part": chip["part"], "reason": "no Verilog port mapping"})
            continue
        ports = mapping["ports"](chip["ref"], net_for_pin)
        port_lines = [f".{port}({expr})" for port, expr in ports]
        joined = ", ".join(port_lines)
        parameters = ""
        if str(mapping["module"]).startswith("ttl_"):
            delay = mapping.get("delay_ns", 1)
            if isinstance(delay, dict):
                delay = delay.get(chip["ref"], delay.get("*", 1))
            delay = int(delay)
            parameter_items = [f".DELAY_RISE({delay})", f".DELAY_FALL({delay})"]
            sample_delay = mapping.get("sample_delay_ns")
            if isinstance(sample_delay, dict):
                sample_delay = sample_delay.get(chip["ref"], sample_delay.get("*"))
            if sample_delay is not None:
                parameter_items.append(f".SAMPLE_DELAY({int(sample_delay)})")
            parameters = " #(" + ", ".join(parameter_items) + ")"
        lines.append(f"  {mapping['module']}{parameters} {chip['ref']} ({joined});")
    lines.append("endmodule")

    result: JsonMap = {
        "ok": not unsupported,
        "format": "verilog",
        "module": module_name,
        "verilog": "\n".join(lines) + "\n",
        "unsupported": unsupported,
        "netlist": netlist,
    }
    if include_testbench:
        tb_name = f"tb_{module_name}"
        result["testbench"] = (
            "`timescale 1ns/1ps\n\n"
            f"module {tb_name}();\n"
            f"  {module_name} dut();\n"
            "  initial begin\n"
            "    #1;\n"
            "    $finish;\n"
            "  end\n"
            "endmodule\n"
        )
    return result


def _chip_entry(ref: str, spec: Any, pins: dict[int, JsonMap]) -> JsonMap:
    part = str(spec.get("part", "")) if isinstance(spec, dict) else str(spec)
    entry: JsonMap = {"ref": ref, "part": part}
    if isinstance(spec, dict):
        for key in ("label", "module", "description"):
            if key in spec:
                entry[key] = deepcopy(spec[key])
    if pins:
        entry["pins"] = [pins[number] for number in sorted(pins)]
    else:
        chip = create_chip(part, ref)
        entry["pins"] = [
            {
                "number": pin.number,
                "name": pin.name,
                "direction": pin.direction,
                "active_low": pin.spec.active_low,
            }
            for pin in chip.pins.values()
        ]
    return entry


def _pin_index(snapshot: JsonMap) -> dict[str, dict[int, JsonMap]]:
    result: dict[str, dict[int, JsonMap]] = {}
    for chip in snapshot["chips"]:
        pins: dict[int, JsonMap] = {}
        for pin in chip["pins"]:
            pins[int(pin["number"])] = {
                "number": pin["number"],
                "name": pin["name"],
                "direction": pin["direction"],
                "active_low": pin["active_low"],
                "net": pin["net"],
                "value": pin["value"],
            }
        result[str(chip["ref"])] = pins
    return result


def _pin_endpoint(pin: JsonMap) -> JsonMap:
    return {
        "chip": pin["chip"],
        "pin": pin["number"],
        "name": pin["name"],
        "direction": pin["direction"],
        "ref": f"{pin['chip']}:{pin['number']}",
    }


def _bus_line(name: str) -> JsonMap | None:
    parsed = parse_bus_tag(name)
    if parsed is None:
        return None
    bus, index = parsed
    return {"bus": bus, "index": index}


def _width(spec: Any) -> int:
    return int(spec.get("width", 1)) if isinstance(spec, dict) else int(spec)


def _logic(value: Any) -> Logic:
    if value in (0, 1, "Z", "X"):
        return value
    return int(value)


def _logic_literal(value: Any) -> str:
    if value == 1:
        return "1'b1"
    if value == 0:
        return "1'b0"
    if value == "X":
        return "1'bx"
    return "1'bz"


def _verilog_ident(text: str) -> str:
    chars = [char if char.isalnum() or char == "_" else "_" for char in str(text)]
    name = "".join(chars).strip("_") or "design"
    if name[0].isdigit():
        name = f"m_{name}"
    return name


def _net_id(name: str) -> str:
    text = (
        str(name)
        .replace("bus:", "bus_")
        .replace("/", "bar_")
        .replace("[", "_")
        .replace("]", "")
        .replace("=", "_eq_")
    )
    return "n_" + _verilog_ident(text)


def _net_for_pin(netlist: JsonMap) -> dict[tuple[str, int], str]:
    result: dict[tuple[str, int], str] = {}
    for net in netlist["nets"]:
        for pin in net["pins"]:
            result[(str(pin["chip"]), int(pin["pin"]))] = _net_id(net["name"])
    return result


def _pin(ref: str, number: int, net_for_pin: dict[tuple[str, int], str], *, fallback: str = "1'bz") -> str:
    return net_for_pin.get((ref, number), fallback)


def _vec(ref: str, pins: list[int], net_for_pin: dict[tuple[str, int], str], *, output: bool = False) -> str:
    return "{" + ", ".join(
        _pin(ref, pin, net_for_pin, fallback=_open_wire(ref, pin) if output else "1'bz")
        for pin in reversed(pins)
    ) + "}"


def _open_wire(ref: str, pin: int) -> str:
    return f"open_{_verilog_ident(ref)}_{pin}"


def _open_output_wires(netlist: JsonMap) -> list[str]:
    result: list[str] = []
    net_for_pin = _net_for_pin(netlist)
    for chip in netlist["chips"]:
        mapping = _verilog_mapping(str(chip["part"]))
        if mapping is None:
            continue
        for pin in mapping.get("output_pins", []):
            if (chip["ref"], pin) not in net_for_pin:
                result.append(_open_wire(chip["ref"], pin))
    return sorted(result)


def _verilog_mapping(part: str) -> JsonMap | None:
    part_id = str(part).upper()
    db_mapping = _db_verilog_mapping(part_id)
    if db_mapping is not None:
        return db_mapping
    return VERILOG_MAPPINGS.get(part_id)


def _db_verilog_mapping(part: str) -> JsonMap | None:
    if part != "74HC00":
        return None

    manifest_path = Path(__file__).resolve().parents[2] / "db" / part / "chip.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    verilog = manifest.get("verilog", {})
    export = verilog.get("export", {}) if isinstance(verilog, dict) else {}
    ports = export.get("ports", {}) if isinstance(export, dict) else {}
    module = verilog.get("module") if isinstance(verilog, dict) else None
    if not isinstance(module, str) or not isinstance(ports, list):
        return None

    port_specs = deepcopy(ports)

    def db_ports(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
        return _ports_from_db_export(ref, net_for_pin, port_specs)

    return {
        "module": module,
        "ports": db_ports,
        "output_pins": [int(pin) for pin in export.get("output_pins", [])],
        "delay_ns": deepcopy(export.get("delay_ns", 1)),
    }


def _ports_from_db_export(
    ref: str,
    net_for_pin: dict[tuple[str, int], str],
    port_specs: list[JsonMap],
) -> list[tuple[str, str]]:
    ports: list[tuple[str, str]] = []
    for spec in port_specs:
        name = str(spec["name"])
        pins = [int(pin) for pin in spec.get("pins", [])]
        is_output = spec.get("direction") == "output"
        if len(pins) == 1:
            fallback = _open_wire(ref, pins[0]) if is_output else "1'bz"
            ports.append((name, _pin(ref, pins[0], net_for_pin, fallback=fallback)))
        else:
            ports.append((name, _vec(ref, pins, net_for_pin, output=is_output)))
    return ports


def _quad_2_input(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A", _vec(ref, [1, 4, 9, 12], net_for_pin)),
        ("B", _vec(ref, [2, 5, 10, 13], net_for_pin)),
        ("Y", _vec(ref, [3, 6, 8, 11], net_for_pin, output=True)),
    ]


def _quad_2_input_02(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A", _vec(ref, [2, 5, 8, 11], net_for_pin)),
        ("B", _vec(ref, [3, 6, 9, 12], net_for_pin)),
        ("Y", _vec(ref, [1, 4, 10, 13], net_for_pin, output=True)),
    ]


def _hex_inverter(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A", _vec(ref, [1, 3, 5, 9, 11, 13], net_for_pin)),
        ("Y", _vec(ref, [2, 4, 6, 8, 10, 12], net_for_pin, output=True)),
    ]


def _hex_buffer_07(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A", _vec(ref, [1, 3, 5, 9, 11, 13], net_for_pin)),
        ("Y", _vec(ref, [2, 4, 6, 8, 10, 12], net_for_pin, output=True)),
    ]


def _hc10(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A_2D", _vec(ref, [1, 2, 13, 3, 4, 5, 9, 10, 11], net_for_pin)),
        ("Y", _vec(ref, [12, 6, 8], net_for_pin, output=True)),
    ]


def _hc11(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A_2D", _vec(ref, [1, 2, 13, 3, 4, 5, 9, 10, 11], net_for_pin)),
        ("Y", _vec(ref, [12, 6, 8], net_for_pin, output=True)),
    ]


def _hc20(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A_2D", _vec(ref, [1, 2, 4, 5, 9, 10, 12, 13], net_for_pin)),
        ("Y", _vec(ref, [6, 8], net_for_pin, output=True)),
    ]


def _hc27(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A_2D", _vec(ref, [1, 2, 13, 3, 4, 5, 9, 10, 11], net_for_pin)),
        ("Y", _vec(ref, [12, 6, 8], net_for_pin, output=True)),
    ]


def _hc30(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A", _vec(ref, [1, 2, 3, 4, 5, 6, 11, 12], net_for_pin)),
        ("Y", _pin(ref, 8, net_for_pin, fallback=_open_wire(ref, 8))),
    ]


def _hc138(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A", _pin(ref, 1, net_for_pin)),
        ("B", _pin(ref, 2, net_for_pin)),
        ("C", _pin(ref, 3, net_for_pin)),
        ("G1", _pin(ref, 6, net_for_pin)),
        ("G2A_bar", _pin(ref, 4, net_for_pin)),
        ("G2B_bar", _pin(ref, 5, net_for_pin)),
        ("Y_bar", _vec(ref, [15, 14, 13, 12, 11, 10, 9, 7], net_for_pin, output=True)),
    ]


def _hc139(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Enable_bar", _vec(ref, [1, 15], net_for_pin)),
        ("A", _vec(ref, [2, 14], net_for_pin)),
        ("B", _vec(ref, [3, 13], net_for_pin)),
        ("Y1_bar", _vec(ref, [4, 5, 6, 7], net_for_pin, output=True)),
        ("Y2_bar", _vec(ref, [12, 11, 10, 9], net_for_pin, output=True)),
    ]


def _hc154(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Enable1_bar", _pin(ref, 18, net_for_pin)),
        ("Enable2_bar", _pin(ref, 19, net_for_pin)),
        ("A", _vec(ref, [23, 22, 21, 20], net_for_pin)),
        ("Y", _vec(ref, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17], net_for_pin, output=True)),
    ]


def _hc155(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Enable1C", _pin(ref, 1, net_for_pin)),
        ("Enable1G_bar", _pin(ref, 2, net_for_pin)),
        ("Enable2C_bar", _pin(ref, 15, net_for_pin)),
        ("Enable2G_bar", _pin(ref, 14, net_for_pin)),
        ("A", _vec(ref, [13, 3], net_for_pin)),
        ("Y_2D", _vec(ref, [7, 6, 5, 4, 9, 10, 11, 12], net_for_pin, output=True)),
    ]


def _hc148(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("EI_bar", _pin(ref, 5, net_for_pin)),
        ("A_bar", _vec(ref, [11, 12, 13, 1, 2, 3, 4, 10], net_for_pin)),
        ("EO_bar", _pin(ref, 15, net_for_pin, fallback=_open_wire(ref, 15))),
        ("GS_bar", _pin(ref, 14, net_for_pin, fallback=_open_wire(ref, 14))),
        ("Y_bar", _vec(ref, [9, 7, 6], net_for_pin, output=True)),
    ]


def _hc157(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Enable_bar", _pin(ref, 15, net_for_pin)),
        ("Select", _pin(ref, 1, net_for_pin)),
        ("A", _vec(ref, [2, 5, 11, 14], net_for_pin)),
        ("B", _vec(ref, [3, 6, 10, 13], net_for_pin)),
        ("Y", _vec(ref, [4, 7, 9, 12], net_for_pin, output=True)),
    ]


def _hc158(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Enable_bar", _pin(ref, 15, net_for_pin)),
        ("Select", _pin(ref, 1, net_for_pin)),
        ("A_2D", _vec(ref, [2, 3, 5, 6, 11, 10, 14, 13], net_for_pin)),
        ("Y_bar", _vec(ref, [4, 7, 9, 12], net_for_pin, output=True)),
    ]


def _hc151(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Enable_bar", _pin(ref, 7, net_for_pin)),
        ("Select", _vec(ref, [11, 10, 9], net_for_pin)),
        ("D", _vec(ref, [4, 3, 2, 1, 15, 14, 13, 12], net_for_pin)),
        ("Y", _pin(ref, 5, net_for_pin, fallback=_open_wire(ref, 5))),
        ("Y_bar", _pin(ref, 6, net_for_pin, fallback=_open_wire(ref, 6))),
    ]


def _hc153(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Enable_bar", _vec(ref, [1, 15], net_for_pin)),
        ("Select", _vec(ref, [14, 2], net_for_pin)),
        ("C1", _vec(ref, [6, 5, 4, 3], net_for_pin)),
        ("C2", _vec(ref, [10, 11, 12, 13], net_for_pin)),
        ("Y1", _pin(ref, 7, net_for_pin, fallback=_open_wire(ref, 7))),
        ("Y2", _pin(ref, 9, net_for_pin, fallback=_open_wire(ref, 9))),
    ]


def _hc160_family(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Clear_bar", _pin(ref, 1, net_for_pin)),
        ("Load_bar", _pin(ref, 9, net_for_pin)),
        ("ENT", _pin(ref, 10, net_for_pin)),
        ("ENP", _pin(ref, 7, net_for_pin)),
        ("D", _vec(ref, [3, 4, 5, 6], net_for_pin)),
        ("Clk", _pin(ref, 2, net_for_pin)),
        ("RCO", _pin(ref, 15, net_for_pin, fallback=_open_wire(ref, 15))),
        ("Q", _vec(ref, [14, 13, 12, 11], net_for_pin, output=True)),
    ]


def _hc181(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Select", _vec(ref, [6, 5, 4, 3], net_for_pin)),
        ("Mode", _pin(ref, 8, net_for_pin)),
        ("C_in", _pin(ref, 7, net_for_pin)),
        ("A_bar", _vec(ref, [2, 23, 21, 19], net_for_pin)),
        ("B_bar", _vec(ref, [1, 22, 20, 18], net_for_pin)),
        ("CP_bar", _pin(ref, 15, net_for_pin, fallback=_open_wire(ref, 15))),
        ("CG_bar", _pin(ref, 17, net_for_pin, fallback=_open_wire(ref, 17))),
        ("Equal", _pin(ref, 14, net_for_pin, fallback=_open_wire(ref, 14))),
        ("C_out", _pin(ref, 16, net_for_pin, fallback=_open_wire(ref, 16))),
        ("F_bar", _vec(ref, [9, 10, 11, 13], net_for_pin, output=True)),
    ]


def _hc161(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Clear_bar", _pin(ref, 1, net_for_pin)),
        ("Load_bar", _pin(ref, 9, net_for_pin)),
        ("ENT", _pin(ref, 10, net_for_pin)),
        ("ENP", _pin(ref, 7, net_for_pin)),
        ("D", _vec(ref, [3, 4, 5, 6], net_for_pin)),
        ("Clk", _pin(ref, 2, net_for_pin)),
        ("RCO", _pin(ref, 15, net_for_pin, fallback=_open_wire(ref, 15))),
        ("Q", _vec(ref, [14, 13, 12, 11], net_for_pin, output=True)),
    ]


def _hc164(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Clear_bar", _pin(ref, 9, net_for_pin)),
        ("Clk", _pin(ref, 8, net_for_pin)),
        ("A", _pin(ref, 1, net_for_pin)),
        ("B", _pin(ref, 2, net_for_pin)),
        ("Q", _vec(ref, [3, 4, 5, 6, 10, 11, 12, 13], net_for_pin, output=True)),
    ]


def _hc165(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("ShiftLoad_bar", _pin(ref, 1, net_for_pin)),
        ("Clk", _pin(ref, 2, net_for_pin)),
        ("ClkInhibit", _pin(ref, 15, net_for_pin)),
        ("Serial", _pin(ref, 10, net_for_pin)),
        ("D", _vec(ref, [11, 12, 13, 14, 3, 4, 5, 6], net_for_pin)),
        ("QH", _pin(ref, 9, net_for_pin, fallback=_open_wire(ref, 9))),
        ("QH_bar", _pin(ref, 7, net_for_pin, fallback=_open_wire(ref, 7))),
    ]


def _hc166(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Clear_bar", _pin(ref, 9, net_for_pin)),
        ("ShiftLoad_bar", _pin(ref, 14, net_for_pin)),
        ("Clk", _pin(ref, 7, net_for_pin)),
        ("ClkInhibit", _pin(ref, 6, net_for_pin)),
        ("Serial", _pin(ref, 1, net_for_pin)),
        ("D", _vec(ref, [2, 3, 4, 5, 13, 12, 11, 10], net_for_pin)),
        ("QH", _pin(ref, 15, net_for_pin, fallback=_open_wire(ref, 15))),
    ]


def _hc21(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A", _vec(ref, [1, 9], net_for_pin)),
        ("B", _vec(ref, [2, 10], net_for_pin)),
        ("C", _vec(ref, [4, 12], net_for_pin)),
        ("D", _vec(ref, [5, 13], net_for_pin)),
        ("Y", _vec(ref, [6, 8], net_for_pin, output=True)),
    ]


def _hc266(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A_2D", _vec(ref, [1, 2, 5, 6, 8, 9, 12, 13], net_for_pin)),
        ("Y", _vec(ref, [3, 4, 10, 11], net_for_pin, output=True)),
    ]


def _hc112(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Preset_bar", _vec(ref, [4, 10], net_for_pin)),
        ("Clear_bar", _vec(ref, [15, 14], net_for_pin)),
        ("J", _vec(ref, [3, 11], net_for_pin)),
        ("K", _vec(ref, [2, 12], net_for_pin)),
        ("Clk", _vec(ref, [1, 13], net_for_pin)),
        ("Q", _vec(ref, [5, 9], net_for_pin, output=True)),
        ("Q_bar", _vec(ref, [6, 7], net_for_pin, output=True)),
    ]


def _hc245(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("OE_bar", _pin(ref, 19, net_for_pin)),
        ("DIR", _pin(ref, 1, net_for_pin)),
        ("A", _vec(ref, [2, 3, 4, 5, 6, 7, 8, 9], net_for_pin, output=True)),
        ("B", _vec(ref, [18, 17, 16, 15, 14, 13, 12, 11], net_for_pin, output=True)),
    ]


def _hc244(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("OE1_bar", _pin(ref, 1, net_for_pin)),
        ("OE2_bar", _pin(ref, 19, net_for_pin)),
        ("A", _vec(ref, [2, 4, 6, 8, 11, 13, 15, 17], net_for_pin)),
        ("Y", _vec(ref, [18, 16, 14, 12, 9, 7, 5, 3], net_for_pin, output=True)),
    ]


def _hc240(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("OE1_bar", _pin(ref, 1, net_for_pin)),
        ("OE2_bar", _pin(ref, 19, net_for_pin)),
        ("A", _vec(ref, [2, 4, 6, 8, 11, 13, 15, 17], net_for_pin)),
        ("Y", _vec(ref, [18, 16, 14, 12, 9, 7, 5, 3], net_for_pin, output=True)),
    ]


def _hc251(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("OE_bar", _pin(ref, 7, net_for_pin)),
        ("Select", _vec(ref, [11, 10, 9], net_for_pin)),
        ("D", _vec(ref, [4, 3, 2, 1, 15, 14, 13, 12], net_for_pin)),
        ("Y", _pin(ref, 5, net_for_pin, fallback=_open_wire(ref, 5))),
        ("Y_bar", _pin(ref, 6, net_for_pin, fallback=_open_wire(ref, 6))),
    ]


def _hc257(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("OE_bar", _pin(ref, 15, net_for_pin)),
        ("Select", _pin(ref, 1, net_for_pin)),
        ("A", _vec(ref, [2, 5, 11, 14], net_for_pin)),
        ("B", _vec(ref, [3, 6, 10, 13], net_for_pin)),
        ("Y", _vec(ref, [4, 7, 9, 12], net_for_pin, output=True)),
    ]


def _hc238(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Enable1_bar", _pin(ref, 4, net_for_pin)),
        ("Enable2_bar", _pin(ref, 5, net_for_pin)),
        ("Enable3", _pin(ref, 6, net_for_pin)),
        ("A", _vec(ref, [1, 2, 3], net_for_pin)),
        ("Y", _vec(ref, [15, 14, 13, 12, 11, 10, 9, 7], net_for_pin, output=True)),
    ]


def _hc283(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A", _vec(ref, [5, 3, 14, 12], net_for_pin)),
        ("B", _vec(ref, [6, 2, 15, 11], net_for_pin)),
        ("C_in", _pin(ref, 7, net_for_pin)),
        ("Sum", _vec(ref, [4, 1, 13, 10], net_for_pin, output=True)),
        ("C_out", _pin(ref, 9, net_for_pin, fallback=_open_wire(ref, 9))),
    ]


def _hc352(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Enable_bar", _vec(ref, [1, 15], net_for_pin)),
        ("Select", _vec(ref, [14, 2], net_for_pin)),
        ("A_2D", _vec(ref, [6, 5, 4, 3, 10, 11, 12, 13], net_for_pin)),
        ("Y_bar", _vec(ref, [7, 9], net_for_pin, output=True)),
    ]


def _hc42(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A", _vec(ref, [15, 14, 13, 12], net_for_pin)),
        ("Y", _vec(ref, [1, 2, 3, 4, 5, 6, 7, 9, 10, 11], net_for_pin, output=True)),
    ]


def _hc541(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("OE1_bar", _pin(ref, 1, net_for_pin)),
        ("OE2_bar", _pin(ref, 19, net_for_pin)),
        ("A", _vec(ref, [2, 3, 4, 5, 6, 7, 8, 9], net_for_pin)),
        ("Y", _vec(ref, [18, 17, 16, 15, 14, 13, 12, 11], net_for_pin, output=True)),
    ]


def _hc273(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Clear_bar", _pin(ref, 1, net_for_pin)),
        ("Clk", _pin(ref, 11, net_for_pin)),
        ("D", _vec(ref, [3, 4, 7, 8, 13, 14, 17, 18], net_for_pin)),
        ("Q", _vec(ref, [2, 5, 6, 9, 12, 15, 16, 19], net_for_pin, output=True)),
    ]


def _hc374(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("OE_bar", _pin(ref, 1, net_for_pin)),
        ("Clk", _pin(ref, 11, net_for_pin)),
        ("D", _vec(ref, [3, 4, 7, 8, 13, 14, 17, 18], net_for_pin)),
        ("Q", _vec(ref, [2, 5, 6, 9, 12, 15, 16, 19], net_for_pin, output=True)),
    ]


def _hc377(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Enable_bar", _pin(ref, 1, net_for_pin)),
        ("D", _vec(ref, [3, 4, 7, 8, 13, 14, 17, 18], net_for_pin)),
        ("Clk", _pin(ref, 11, net_for_pin)),
        ("Q", _vec(ref, [2, 5, 6, 9, 12, 15, 16, 19], net_for_pin, output=True)),
    ]


def _hc193(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Clear", _pin(ref, 14, net_for_pin)),
        ("Load_bar", _pin(ref, 11, net_for_pin)),
        ("Up", _pin(ref, 5, net_for_pin)),
        ("Down", _pin(ref, 4, net_for_pin)),
        ("D", _vec(ref, [15, 1, 10, 9], net_for_pin)),
        ("Q", _vec(ref, [3, 2, 6, 7], net_for_pin, output=True)),
        ("Carry_bar", _pin(ref, 12, net_for_pin, fallback=_open_wire(ref, 12))),
        ("Borrow_bar", _pin(ref, 13, net_for_pin, fallback=_open_wire(ref, 13))),
    ]


def _hc574(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("OE_bar", _pin(ref, 1, net_for_pin)),
        ("Clk", _pin(ref, 11, net_for_pin)),
        ("D", _vec(ref, [2, 3, 4, 5, 6, 7, 8, 9], net_for_pin)),
        ("Q", _vec(ref, [19, 18, 17, 16, 15, 14, 13, 12], net_for_pin, output=True)),
    ]


def _hc688(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Enable_bar", _pin(ref, 1, net_for_pin)),
        ("A", _vec(ref, [2, 4, 6, 8, 12, 14, 16, 18], net_for_pin)),
        ("B", _vec(ref, [3, 5, 7, 9, 11, 13, 15, 17], net_for_pin)),
        ("Equal_bar", _pin(ref, 19, net_for_pin, fallback=_open_wire(ref, 19))),
    ]


def _hc595(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("SER", _pin(ref, 14, net_for_pin)),
        ("SRCLK", _pin(ref, 11, net_for_pin)),
        ("RCLK", _pin(ref, 12, net_for_pin)),
        ("SRCLR_bar", _pin(ref, 10, net_for_pin)),
        ("OE_bar", _pin(ref, 13, net_for_pin)),
        ("Q", _vec(ref, [15, 1, 2, 3, 4, 5, 6, 7], net_for_pin, output=True)),
        ("QH_prime", _pin(ref, 9, net_for_pin, fallback=_open_wire(ref, 9))),
    ]


def _hc593(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A_Q", _vec(ref, [1, 2, 3, 4, 5, 6, 7, 8], net_for_pin, output=True)),
        ("CLOAD", _pin(ref, 9, net_for_pin)),
        ("RCO", _pin(ref, 11, net_for_pin, fallback=_open_wire(ref, 11))),
        ("CCLR", _pin(ref, 12, net_for_pin)),
        ("CCK", _pin(ref, 13, net_for_pin)),
        ("CCKEN", _pin(ref, 14, net_for_pin)),
        ("CCKEN_bar", _pin(ref, 15, net_for_pin)),
        ("RCK", _pin(ref, 16, net_for_pin)),
        ("RCKEN", _pin(ref, 17, net_for_pin)),
        ("G", _pin(ref, 18, net_for_pin)),
        ("G_bar", _pin(ref, 19, net_for_pin)),
    ]


def _hc4078(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A", _vec(ref, [2, 3, 4, 5, 9, 10, 11, 12], net_for_pin)),
        ("X", _pin(ref, 13, net_for_pin, fallback=_open_wire(ref, 13))),
        ("Y", _pin(ref, 1, net_for_pin, fallback=_open_wire(ref, 1))),
    ]


def _hc73(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Clear_bar", _vec(ref, [2, 6], net_for_pin)),
        ("J", _vec(ref, [14, 7], net_for_pin)),
        ("K", _vec(ref, [3, 10], net_for_pin)),
        ("Clk", _vec(ref, [1, 5], net_for_pin)),
        ("Q", _vec(ref, [13, 9], net_for_pin, output=True)),
        ("Q_bar", _vec(ref, [12, 8], net_for_pin, output=True)),
    ]


def _hc74(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("Preset_bar", _vec(ref, [4, 10], net_for_pin)),
        ("Clear_bar", _vec(ref, [1, 13], net_for_pin)),
        ("D", _vec(ref, [2, 12], net_for_pin)),
        ("Clk", _vec(ref, [3, 11], net_for_pin)),
        ("Q", _vec(ref, [5, 9], net_for_pin, output=True)),
        ("Q_bar", _vec(ref, [6, 8], net_for_pin, output=True)),
    ]


def _hc85(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A", _vec(ref, [10, 12, 13, 15], net_for_pin)),
        ("B", _vec(ref, [9, 11, 14, 1], net_for_pin)),
        ("ALess_in", _pin(ref, 2, net_for_pin)),
        ("Equal_in", _pin(ref, 3, net_for_pin)),
        ("AGreater_in", _pin(ref, 4, net_for_pin)),
        ("ALess_out", _pin(ref, 7, net_for_pin, fallback=_open_wire(ref, 7))),
        ("Equal_out", _pin(ref, 6, net_for_pin, fallback=_open_wire(ref, 6))),
        ("AGreater_out", _pin(ref, 5, net_for_pin, fallback=_open_wire(ref, 5))),
    ]


def _hc922(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("RowY", _vec(ref, [1, 2, 3, 4], net_for_pin)),
        ("ColumnX", _vec(ref, [11, 10, 8, 7], net_for_pin, output=True)),
        ("Oscillator", _pin(ref, 5, net_for_pin)),
        ("KeybounceMask", _pin(ref, 6, net_for_pin)),
        ("OutputEnable", _pin(ref, 13, net_for_pin)),
        ("DataOut", _vec(ref, [17, 16, 15, 14], net_for_pin, output=True)),
        ("DataAvailable", _pin(ref, 12, net_for_pin, fallback=_open_wire(ref, 12))),
    ]


def _memory_28(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A", _vec(ref, [10, 9, 8, 7, 6, 5, 4, 3, 25, 24, 21, 23, 2, 26, 1], net_for_pin)),
        ("DQ", _vec(ref, [11, 12, 13, 15, 16, 17, 18, 19], net_for_pin, output=True)),
        ("CE_bar", _pin(ref, 20, net_for_pin)),
        ("OE_bar", _pin(ref, 22, net_for_pin)),
        ("WE_bar", _pin(ref, 27, net_for_pin, fallback="1'b1")),
    ]


def _memory_sst39sf010a(ref: str, net_for_pin: dict[tuple[str, int], str]) -> list[tuple[str, str]]:
    return [
        ("A", _vec(ref, [12, 11, 10, 9, 8, 7, 6, 5, 27, 26, 23, 25, 4, 28, 29, 3, 2], net_for_pin)),
        ("DQ", _vec(ref, [13, 14, 15, 17, 18, 19, 20, 21], net_for_pin, output=True)),
        ("CE_bar", _pin(ref, 22, net_for_pin)),
        ("OE_bar", _pin(ref, 24, net_for_pin)),
        ("WE_bar", _pin(ref, 31, net_for_pin, fallback="1'b1")),
    ]


VERILOG_MAPPINGS = {
    "74HC00": {"module": "ttl_74hc00", "ports": _quad_2_input, "output_pins": [3, 6, 8, 11], "delay_ns": {"U26": 8, "*": 1}},
    "74HC02": {"module": "ttl_74hc02", "ports": _quad_2_input_02, "output_pins": [1, 4, 10, 13]},
    "74HC07": {"module": "ttl_74hc07", "ports": _hex_buffer_07, "output_pins": [2, 4, 6, 8, 10, 12]},
    "74HC32": {"module": "ttl_74hc32", "ports": _quad_2_input, "output_pins": [3, 6, 8, 11]},
    "74HC86": {"module": "ttl_74hc86", "ports": _quad_2_input, "output_pins": [3, 6, 8, 11]},
    "74HC08": {"module": "ttl_74hc08", "ports": _quad_2_input, "output_pins": [3, 6, 8, 11]},
    "74HC04": {"module": "ttl_74hc04", "ports": _hex_inverter, "output_pins": [2, 4, 6, 8, 10, 12]},
    "74HC14": {"module": "ttl_74hc14", "ports": _hex_inverter, "output_pins": [2, 4, 6, 8, 10, 12]},
    "74HC10": {"module": "ttl_74hc10", "ports": _hc10, "output_pins": [6, 8, 12]},
    "74HC11": {"module": "ttl_74hc11", "ports": _hc11, "output_pins": [6, 8, 12]},
    "74HC20": {"module": "ttl_74hc20", "ports": _hc20, "output_pins": [6, 8]},
    "74HC27": {"module": "ttl_74hc27", "ports": _hc27, "output_pins": [6, 8, 12]},
    "74HC30": {"module": "ttl_74hc30", "ports": _hc30, "output_pins": [8]},
    "74HC138": {"module": "ttl_74hc138", "ports": _hc138, "output_pins": [7, 9, 10, 11, 12, 13, 14, 15]},
    "74HC139": {"module": "ttl_74hc139", "ports": _hc139, "output_pins": [4, 5, 6, 7, 9, 10, 11, 12]},
    "74HC148": {"module": "ttl_74hc148", "ports": _hc148, "output_pins": [6, 7, 9, 14, 15]},
    "74HC154": {"module": "ttl_74hc154", "ports": _hc154, "output_pins": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17]},
    "74HC155": {"module": "ttl_74hc155", "ports": _hc155, "output_pins": [4, 5, 6, 7, 9, 10, 11, 12]},
    "74HC151": {"module": "ttl_74hc151", "ports": _hc151, "output_pins": [5, 6]},
    "74HC153": {"module": "ttl_74hc153", "ports": _hc153, "output_pins": [7, 9]},
    "74HC157": {"module": "ttl_74hc157", "ports": _hc157, "output_pins": [4, 7, 9, 12]},
    "74HC158": {"module": "ttl_74hc158", "ports": _hc158, "output_pins": [4, 7, 9, 12]},
    "74HC160": {"module": "ttl_74hc160", "ports": _hc160_family, "output_pins": [11, 12, 13, 14, 15]},
    "74HC181": {"module": "ttl_74hc181", "ports": _hc181, "output_pins": [9, 10, 11, 13, 14, 15, 16, 17]},
    "74HC161": {"module": "ttl_74hc161", "ports": _hc161, "output_pins": [11, 12, 13, 14, 15]},
    "74HC162": {"module": "ttl_74hc162", "ports": _hc160_family, "output_pins": [11, 12, 13, 14, 15]},
    "74HC163": {"module": "ttl_74hc163", "ports": _hc160_family, "output_pins": [11, 12, 13, 14, 15]},
    "74HC164": {"module": "ttl_74hc164", "ports": _hc164, "output_pins": [3, 4, 5, 6, 10, 11, 12, 13], "delay_ns": 4},
    "74HC165": {"module": "ttl_74hc165", "ports": _hc165, "output_pins": [7, 9]},
    "74HC166": {"module": "ttl_74hc166", "ports": _hc166, "output_pins": [15]},
    "74HC21": {"module": "ttl_74hc21", "ports": _hc21, "output_pins": [6, 8]},
    "74HC112": {"module": "ttl_74hc112", "ports": _hc112, "output_pins": [5, 6, 7, 9]},
    "74HC193": {"module": "ttl_74hc193", "ports": _hc193, "output_pins": [2, 3, 6, 7, 12, 13]},
    "74HC238": {"module": "ttl_74hc238", "ports": _hc238, "output_pins": [7, 9, 10, 11, 12, 13, 14, 15]},
    "74HC240": {"module": "ttl_74hc240", "ports": _hc240, "output_pins": [3, 5, 7, 9, 12, 14, 16, 18]},
    "74HC244": {"module": "ttl_74hc244", "ports": _hc244, "output_pins": [3, 5, 7, 9, 12, 14, 16, 18]},
    "74HC245": {"module": "ttl_74hc245", "ports": _hc245, "output_pins": [2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18]},
    "74HC251": {"module": "ttl_74hc251", "ports": _hc251, "output_pins": [5, 6]},
    "74HC257": {"module": "ttl_74hc257", "ports": _hc257, "output_pins": [4, 7, 9, 12]},
    "74HC266": {"module": "ttl_74hc266", "ports": _hc266, "output_pins": [3, 4, 10, 11]},
    "74HC273": {"module": "ttl_74hc273", "ports": _hc273, "output_pins": [2, 5, 6, 9, 12, 15, 16, 19]},
    "74HC283": {"module": "ttl_74hc283", "ports": _hc283, "output_pins": [1, 4, 9, 10, 13]},
    "74HC352": {"module": "ttl_74hc352", "ports": _hc352, "output_pins": [7, 9]},
    "74HC374": {"module": "ttl_74hc374", "ports": _hc374, "output_pins": [2, 5, 6, 9, 12, 15, 16, 19]},
    "74HC377": {"module": "ttl_74hc377", "ports": _hc377, "output_pins": [2, 5, 6, 9, 12, 15, 16, 19]},
    "74HC42": {"module": "ttl_74hc42", "ports": _hc42, "output_pins": [1, 2, 3, 4, 5, 6, 7, 9, 10, 11]},
    "74HC541": {"module": "ttl_74hc541", "ports": _hc541, "output_pins": [11, 12, 13, 14, 15, 16, 17, 18]},
    "74HC574": {
        "module": "ttl_74hc574",
        "ports": _hc574,
        "output_pins": [12, 13, 14, 15, 16, 17, 18, 19],
        "sample_delay_ns": {"U5": 40, "U6": 40},
    },
    "74HC593": {"module": "ttl_74hc593", "ports": _hc593, "output_pins": [1, 2, 3, 4, 5, 6, 7, 8, 11]},
    "74HC595": {"module": "ttl_74hc595", "ports": _hc595, "output_pins": [1, 2, 3, 4, 5, 6, 7, 9, 15]},
    "74HC688": {"module": "ttl_74hc688", "ports": _hc688, "output_pins": [19]},
    "74HC4078": {"module": "ttl_74hc4078", "ports": _hc4078, "output_pins": [1, 13]},
    "74HC73": {"module": "ttl_74hc73", "ports": _hc73, "output_pins": [8, 9, 12, 13]},
    "74HC74": {
        "module": "ttl_74hc74",
        "ports": _hc74,
        "output_pins": [5, 6, 8, 9],
        "sample_delay_ns": {"U21": 20},
    },
    "74HC85": {"module": "ttl_74hc85", "ports": _hc85, "output_pins": [5, 6, 7]},
    "74HC922": {"module": "ttl_74hc922", "ports": _hc922, "output_pins": [7, 8, 10, 11, 12, 14, 15, 16, 17]},
    "62256": {"module": "mem_62256", "ports": _memory_28, "output_pins": [11, 12, 13, 15, 16, 17, 18, 19]},
    "AS6C62256": {"module": "mem_as6c62256", "ports": _memory_28, "output_pins": [11, 12, 13, 15, 16, 17, 18, 19]},
    "AT28C256": {"module": "mem_at28c256", "ports": _memory_28, "output_pins": [11, 12, 13, 15, 16, 17, 18, 19]},
    "CY7C199": {"module": "mem_cy7c199", "ports": _memory_28, "output_pins": [11, 12, 13, 15, 16, 17, 18, 19]},
    "SST39SF010A": {"module": "mem_sst39sf010a", "ports": _memory_sst39sf010a, "output_pins": [13, 14, 15, 17, 18, 19, 20, 21]},
}
