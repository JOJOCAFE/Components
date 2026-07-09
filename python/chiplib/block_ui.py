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
    return {
        "format": "components.block_ui",
        "version": 1,
        "design": {
            "name": data.get("name", ""),
            "description": data.get("description", ""),
        },
        "blocks": _blocks_from_design(data, block_layout),
        "wires": [
            {
                "id": f"W{index + 1}",
                "rule": rule,
                "endpoints": [endpoint["ref"] for endpoint in design.connection_endpoints(rule)],
                "layout": deepcopy(wire_layout.get(f"W{index + 1}", {})),
            }
            for index, rule in enumerate(data.get("connect", []))
        ],
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
        "connect": [str(wire.get("rule", "")) for wire in data.get("wires", []) if isinstance(wire, dict) and wire.get("rule")],
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


def _blocks_from_design(data: JsonMap, layout: JsonMap) -> list[JsonMap]:
    blocks: list[JsonMap] = []
    for ref, spec in data.get("chips", {}).items():
        item = spec if isinstance(spec, dict) else {}
        properties = {k: deepcopy(v) for k, v in item.items() if k != "part"}
        blocks.append({
            "id": ref,
            "type": "chip",
            "part": item.get("part", ""),
            "label": item.get("label", ref),
            "properties": properties,
            "layout": deepcopy(layout.get(ref, {})),
        })
    for name, spec in data.get("buses", {}).items():
        item = spec if isinstance(spec, dict) else {}
        properties = {k: deepcopy(v) for k, v in item.items() if k != "width"}
        blocks.append({
            "id": name,
            "type": "bus",
            "width": int(item.get("width", 1)),
            "label": item.get("label", name),
            "properties": properties,
            "layout": deepcopy(layout.get(name, {})),
        })
    for name, value in data.get("rails", {}).items():
        blocks.append({
            "id": name,
            "type": "rail",
            "value": value,
            "label": name,
            "properties": {},
            "layout": deepcopy(layout.get(name, {})),
        })
    return blocks


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


def _copy_map(value: Any) -> JsonMap:
    return deepcopy(value) if isinstance(value, dict) else {}
