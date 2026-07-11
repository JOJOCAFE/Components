"""Block-UI import/export over the normalized Design model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


JsonMap = dict[str, Any]


def design_to_block_ui(design: Any) -> JsonMap:
    """Return a drawable block representation without changing design logic."""

    data = design.to_dict()
    layout = _copy_map(data.get("layout", {}))
    block_layout = _copy_map(layout.get("blocks", {}))
    wire_layout = _copy_map(layout.get("wires", {}))
    netlist = _netlist_view(design)
    return {
        "format": "components.block_ui",
        "version": 1,
        "design": {
            "name": data.get("name", ""),
            "description": data.get("description", ""),
        },
        "blocks": _blocks_from_design(data, block_layout, netlist),
        "wires": _wires_from_design(design, data, wire_layout, netlist),
        "nets": _nets_from_netlist(netlist),
        "run_config": _run_config(data),
        "editor": _editor_config(data),
        "aliases": deepcopy(data.get("aliases", {})),
        "groups": deepcopy(data.get("groups", {})),
        "modules": deepcopy(data.get("modules", {})),
        "rails": deepcopy(data.get("rails", {})),
        "pullups": list(data.get("pullups", [])),
        "pulldowns": list(data.get("pulldowns", [])),
        "inputs": deepcopy(data.get("inputs", {})),
        "input_sets": deepcopy(data.get("input_sets", {})),
        "clocks": deepcopy(data.get("clocks", {})),
        "controls": deepcopy(data.get("controls", {})),
        "memory_images": deepcopy(data.get("memory_images", {})),
        "probes": deepcopy(data.get("probes", {})),
        "displays": deepcopy(data.get("displays", {})),
        "expect": deepcopy(data.get("expect", {})),
        "steps": list(data.get("steps", [])),
        "validate": deepcopy(data.get("validate", {})),
        "layout": deepcopy(layout),
    }


def design_from_block_ui(data: JsonMap) -> Any:
    """Create a Design from block UI JSON."""

    if not isinstance(data, dict):
        raise ValueError("block UI data must be an object")
    if data.get("format") != "components.block_ui":
        raise ValueError("block UI format must be components.block_ui")
    from .design import Design

    design_info = _copy_map(data.get("design", {}))
    schematic: JsonMap = {
        "name": str(design_info.get("name", "block-ui-design")),
        "description": str(design_info.get("description", "")),
        "chips": {},
        "buses": {},
        "aliases": _copy_map(data.get("aliases", {})),
        "groups": _copy_map(data.get("groups", {})),
        "modules": _copy_map(data.get("modules", {})),
        "rails": _copy_map(data.get("rails", {"VCC": 1, "GND": 0})),
        "connect": _connect_rules_from_wires(data.get("wires", [])),
        "pullups": [str(item) for item in data.get("pullups", [])],
        "pulldowns": [str(item) for item in data.get("pulldowns", [])],
        "inputs": deepcopy(data.get("inputs", {})),
        "input_sets": deepcopy(data.get("input_sets", {})),
        "clocks": deepcopy(data.get("clocks", {})),
        "controls": deepcopy(data.get("controls", {})),
        "memory_images": deepcopy(data.get("memory_images", {})),
        "probes": deepcopy(data.get("probes", {})),
        "displays": deepcopy(data.get("displays", {})),
        "expect": deepcopy(data.get("expect", {})),
        "steps": [str(item) for item in data.get("steps", [])],
        "validate": _copy_map(data.get("validate", {})),
        "run_config": _run_config(data),
        "layout": _layout_from_blocks(data),
    }
    for block in data.get("blocks", []):
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type", ""))
        block_id = str(block.get("id", ""))
        if not block_id:
            continue
        properties = _copy_map(block.get("properties", {}))
        if block_type == "chip":
            part = str(block.get("part", properties.pop("part", "")))
            schematic["chips"][block_id] = {"part": part, **properties}
        elif block_type == "bus":
            width = int(block.get("width", properties.pop("width", 1)))
            schematic["buses"][block_id] = {"width": width, **properties}
        elif block_type == "rail":
            schematic["rails"][block_id] = block.get("value", properties.get("value", 0))
    return Design.from_dict(schematic)


def _blocks_from_design(data: JsonMap, layout: JsonMap, netlist: JsonMap) -> list[JsonMap]:
    blocks: list[JsonMap] = []
    pin_index = _pin_index(netlist)
    for ref, spec in data.get("chips", {}).items():
        item = spec if isinstance(spec, dict) else {}
        properties = {k: deepcopy(v) for k, v in item.items() if k != "part"}
        pins = _chip_pins(ref, pin_index.get(ref, []))
        blocks.append({
            "id": ref,
            "type": "chip",
            "part": item.get("part", ""),
            "shape": "dip",
            "package": {"kind": "DIP", "pins": len(pins)},
            "label": item.get("label", ref),
            "pins": pins,
            "properties": properties,
            "layout": deepcopy(layout.get(ref, {})),
        })
    for name, spec in data.get("buses", {}).items():
        item = spec if isinstance(spec, dict) else {}
        width = int(item.get("width", 1))
        properties = {k: deepcopy(v) for k, v in item.items() if k != "width"}
        blocks.append({
            "id": name,
            "type": "bus",
            "width": width,
            "label": item.get("label", name),
            "pins": [
                {
                    "id": f"{name}:{index}",
                    "ref": f"{name}:{index}",
                    "kind": "bus",
                    "bus": name,
                    "index": index,
                    "net": f"bus:{name}[{index}]",
                }
                for index in range(width)
            ],
            "properties": properties,
            "layout": deepcopy(layout.get(name, {})),
        })
    for name, value in data.get("rails", {}).items():
        blocks.append({
            "id": name,
            "type": "rail",
            "value": value,
            "label": name,
            "pins": [{"id": name, "ref": name, "kind": "rail", "rail": name, "net": name}],
            "properties": {},
            "layout": deepcopy(layout.get(name, {})),
        })
    return blocks


def _wires_from_design(design: Any, data: JsonMap, layout: JsonMap, netlist: JsonMap) -> list[JsonMap]:
    net_for_pin = _net_for_pin(netlist)
    wires: list[JsonMap] = []
    for index, rule in enumerate(data.get("connect", [])):
        wire_id = f"W{index + 1}"
        endpoints = design.connection_endpoints(rule)
        wires.append({
            "id": wire_id,
            "rule": rule,
            "endpoints": [endpoint["ref"] for endpoint in endpoints],
            "endpoint_details": [_endpoint_detail(endpoint, net_for_pin) for endpoint in endpoints],
            "layout": deepcopy(layout.get(wire_id, {})),
        })
    return wires


def _nets_from_netlist(netlist: JsonMap) -> list[JsonMap]:
    result: list[JsonMap] = []
    for net in netlist.get("nets", []):
        if not isinstance(net, dict):
            continue
        result.append({
            "id": net.get("name", ""),
            "name": net.get("name", ""),
            "kind": net.get("kind", "net"),
            "bus": net.get("bus"),
            "index": net.get("index"),
            "value": net.get("value"),
            "endpoints": [
                {
                    "ref": pin.get("ref", ""),
                    "kind": "pin",
                    "chip": pin.get("chip", ""),
                    "pin": pin.get("pin"),
                    "name": pin.get("name", ""),
                    "direction": pin.get("direction", ""),
                }
                for pin in net.get("pins", [])
                if isinstance(pin, dict)
            ],
            "pulls": deepcopy(net.get("pulls", [])),
            "sources": deepcopy(net.get("sources", [])),
        })
    return result


def _run_config(data: JsonMap) -> JsonMap:
    configured = _copy_map(data.get("run_config", {}))
    default_backend = str(configured.get("default_backend", "python"))
    if default_backend not in ("python", "verilog"):
        default_backend = "python"
    selected_backend = str(configured.get("selected_backend", default_backend))
    if selected_backend not in ("python", "verilog"):
        selected_backend = default_backend
    config = {
        "default_backend": "python",
        "selected_backend": selected_backend,
        "backends": {
            "python": {
                "command": "run",
                "input": "design",
                "input_format": "schematic",
                "supports": ["validate", "snapshot", "run", "probe"],
            },
            "verilog": {
                "command": "export-verilog",
                "input": "netlist",
                "netlist_format": "chiplib.netlist",
                "supports": ["export-verilog", "testbench"],
            },
        },
        "steps": list(data.get("steps", [])),
        "inputs": sorted(str(name) for name in data.get("inputs", {})),
        "input_sets": sorted(str(name) for name in data.get("input_sets", {})),
        "clocks": sorted(str(name) for name in data.get("clocks", {})),
        "probes": sorted(str(name) for name in data.get("probes", {})),
    }
    config["default_backend"] = default_backend
    return config


def _editor_config(data: JsonMap) -> JsonMap:
    """Return backend-owned editor affordances for visual and AI clients."""

    return {
        "schema": "components.block_ui.editor",
        "version": 1,
        "source_of_truth": "normalized_design",
        "palette": {
            "commands": [
                {"name": "db --student", "purpose": "beginner-readable component list"},
                {"name": "db --catalog", "purpose": "frontend component metadata"},
                {"name": "db PART --detail", "purpose": "one component's pins, status, and UI hints"},
            ],
            "default_groups": ["74xx", "memory", "virtual", "passive", "discrete"],
            "missing_data_policy": "show_status_warning",
        },
        "actions": [
            {"name": "place_chip", "requires": ["part", "ref"], "updates": ["blocks", "layout.blocks"]},
            {"name": "place_bus", "requires": ["id", "width"], "updates": ["blocks", "layout.blocks"]},
            {"name": "place_rail", "requires": ["id", "value"], "updates": ["blocks", "rails", "layout.blocks"]},
            {"name": "connect", "requires": ["endpoint_a", "endpoint_b"], "updates": ["wires", "connect"]},
            {"name": "disconnect", "requires": ["wire_id"], "updates": ["wires", "connect"]},
            {"name": "set_input", "requires": ["input_set", "rule"], "updates": ["inputs"]},
            {"name": "add_probe", "requires": ["name", "target"], "updates": ["probes"]},
            {"name": "run", "requires": ["backend"], "updates": ["snapshot", "probe_history"]},
        ],
        "validation_gates": [
            "validate",
            "snapshot",
            "run",
            "probe",
            "export-netlist",
            "export-verilog",
        ],
        "mcp_ready_tools": [
            {"tool": "component_catalog", "cli_equivalent": "db --catalog"},
            {"tool": "component_detail", "cli_equivalent": "db PART --detail"},
            {"tool": "validate_design", "cli_equivalent": "validate JSON_FILE"},
            {"tool": "run_design", "cli_equivalent": "run JSON_FILE"},
            {"tool": "export_block_ui", "cli_equivalent": "export-block-ui JSON_FILE"},
            {"tool": "import_block_ui", "cli_equivalent": "import-block-ui JSON_FILE"},
        ],
        "student_rules": [
            "Use real package pins from the DB catalog.",
            "Show missing datasheet or export status instead of guessing behavior.",
            "Run validation before simulation or Verilog export.",
        ],
        "current_design": {
            "chips": sorted(str(name) for name in data.get("chips", {})),
            "buses": sorted(str(name) for name in data.get("buses", {})),
            "rails": sorted(str(name) for name in data.get("rails", {})),
        },
    }


def _layout_from_blocks(data: JsonMap) -> JsonMap:
    layout = _copy_map(data.get("layout", {}))
    blocks = layout.setdefault("blocks", {})
    wires = layout.setdefault("wires", {})
    for block in data.get("blocks", []):
        if isinstance(block, dict) and block.get("id") and isinstance(block.get("layout"), dict):
            blocks[str(block["id"])] = deepcopy(block["layout"])
    for wire in data.get("wires", []):
        if isinstance(wire, dict) and wire.get("id") and isinstance(wire.get("layout"), dict):
            wires[str(wire["id"])] = deepcopy(wire["layout"])
    return layout


def _connect_rules_from_wires(wires: Any) -> list[str]:
    rules: list[str] = []
    for wire in wires if isinstance(wires, list) else []:
        if not isinstance(wire, dict):
            continue
        rule = str(wire.get("rule", "")).strip()
        if rule:
            rules.append(rule)
            continue
        refs = [_endpoint_ref(endpoint) for endpoint in wire.get("endpoint_details", wire.get("endpoints", []))]
        refs = [ref for ref in refs if ref]
        if len(refs) >= 2:
            rules.append(f"{refs[0]} -> {', '.join(refs[1:])}")
    return rules


def _endpoint_ref(endpoint: Any) -> str:
    if isinstance(endpoint, str):
        return endpoint.strip()
    if not isinstance(endpoint, dict):
        return ""
    if endpoint.get("ref"):
        return str(endpoint["ref"]).strip()
    kind = str(endpoint.get("kind", "")).strip()
    chip = endpoint.get("chip", endpoint.get("block"))
    pin = endpoint.get("pin", endpoint.get("number", endpoint.get("pin_number")))
    if kind == "pin" and chip and pin is not None:
        return f"{chip}:{pin}"
    bus = endpoint.get("bus", endpoint.get("block"))
    index = endpoint.get("index", endpoint.get("terminal"))
    if kind == "bus" and bus and index is not None:
        return f"{bus}:{index}"
    if kind == "rail" and endpoint.get("rail"):
        return str(endpoint["rail"]).strip()
    if kind == "net" and endpoint.get("name"):
        return str(endpoint["name"]).strip()
    if endpoint.get("target"):
        return str(endpoint["target"]).strip()
    return ""


def _netlist_view(design: Any) -> JsonMap:
    try:
        return design.to_netlist()
    except Exception as exc:  # pragma: no cover - export should still expose editable blocks.
        return {"nets": [], "chips": [], "errors": [{"type": "netlist_unavailable", "detail": str(exc)}]}


def _pin_index(netlist: JsonMap) -> dict[str, list[JsonMap]]:
    return {
        str(chip.get("ref", "")): deepcopy(chip.get("pins", []))
        for chip in netlist.get("chips", [])
        if isinstance(chip, dict)
    }


def _net_for_pin(netlist: JsonMap) -> dict[tuple[str, int], str]:
    result: dict[tuple[str, int], str] = {}
    for net in netlist.get("nets", []):
        if not isinstance(net, dict):
            continue
        for pin in net.get("pins", []):
            if isinstance(pin, dict) and pin.get("chip") and pin.get("pin") is not None:
                result[(str(pin["chip"]), int(pin["pin"]))] = str(net.get("name", ""))
    return result


def _chip_pins(ref: str, pins: list[JsonMap]) -> list[JsonMap]:
    total = len(pins)
    midpoint = (total + 1) // 2
    result: list[JsonMap] = []
    for pin in sorted(pins, key=lambda item: int(item.get("number", 0))):
        number = int(pin.get("number", 0))
        side = "left" if number <= midpoint else "right"
        side_index = number - 1 if side == "left" else total - number
        side_total = midpoint if side == "left" else total - midpoint
        result.append({
            "id": f"{ref}:{number}",
            "ref": f"{ref}:{number}",
            "kind": "pin",
            "chip": ref,
            "number": number,
            "name": pin.get("name", ""),
            "direction": pin.get("direction", ""),
            "active_low": bool(pin.get("active_low", False)),
            "net": pin.get("net"),
            "value": pin.get("value"),
            "side": side,
            "side_index": side_index,
            "side_total": side_total,
            "dip_position": {
                "side": side,
                "index": side_index,
                "count": side_total,
            },
        })
    return result


def _endpoint_detail(endpoint: JsonMap, net_for_pin: dict[tuple[str, int], str]) -> JsonMap:
    detail = deepcopy(endpoint)
    kind = str(detail.get("kind", ""))
    if kind == "pin" and detail.get("chip") and detail.get("pin") is not None:
        detail["resolved_ref"] = f"{detail['chip']}:{detail['pin']}"
        detail["net"] = net_for_pin.get((str(detail["chip"]), int(detail["pin"])))
    elif kind == "bus":
        detail["resolved_ref"] = f"{detail['bus']}:{detail['index']}"
        detail["net"] = detail.get("target")
    elif kind in ("net", "rail"):
        detail["resolved_ref"] = detail.get("target")
        detail["net"] = detail.get("target")
    return detail


def _copy_map(value: Any) -> JsonMap:
    return deepcopy(value) if isinstance(value, dict) else {}
