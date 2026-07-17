"""Versioned JSON envelopes between readable Component source and clients."""
from __future__ import annotations
from pathlib import Path
from typing import Any

from .db import load_component_package


ROOT = Path(__file__).resolve().parents[2]
FRAME_ROOT = ROOT / "board" / "assets" / "74hc-functional-pinouts"
GATE_ROOT = ROOT / "board" / "assets" / "logic-gates" / "mil-no-pins"


def _presentation_pins(part: str) -> list[dict[str, Any]]:
    """Return definition-owned pin labels for a read-only Board client."""
    package = load_component_package(part)
    pins = package.get("layers", {}).get("definition", {}).get("pins", {}).get("pins", [])
    return [
        {"number": pin["number"], "name": pin["name"], "direction": pin["direction"]}
        for pin in pins
        if isinstance(pin, dict) and {"number", "name", "direction"} <= set(pin)
    ]


def _pin_anchors(instance_id: str, pins: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Give a Board client stable, definition-derived DIP anchor facts.

    The SVG is only a frame.  A client must use these resolved-definition facts
    for its visible anchors and source-edit proposal; it must not infer ports
    from SVG paths or from a separate canvas model.
    """
    count = len(pins)
    half = count // 2
    anchors: list[dict[str, Any]] = []
    for pin in pins:
        number = int(pin["number"])
        left = number <= half
        anchors.append({
            "id": f"{instance_id}.pin-{number}",
            "endpoint": f"{instance_id}.{pin['name']}",
            "physical_pin": number,
            "port": pin["name"],
            "direction": pin["direction"],
            "dip_side": "left" if left else "right",
            "dip_order": number if left else count + 1 - number,
        })
    return anchors


def _chip_frame(part: str) -> dict[str, str] | None:
    """Return a presentation-only local asset when a reviewed frame exists."""
    # The Board supplies its own definition-owned connection nodes.  Use a
    # no-pin logic symbol for the initial inverter rather than a DIP drawing
    # whose printed pin numbers could be mistaken for wiring truth.
    if part.lower() in {"74hc04", "digital.74hc04"}:
        candidate = GATE_ROOT / "not-mil.svg"
        return {
            "kind": "logic-gate-symbol.svg",
            "asset": "resources/logic-gates/mil-no-pins/not-mil.svg",
            "source": candidate.relative_to(ROOT).as_posix(),
        }
    filename = f"{part.lower()}.svg"
    candidate = FRAME_ROOT / filename
    if not candidate.is_file():
        return None
    return {
        "kind": "chip-frame.svg",
        "asset": f"resources/74hc-functional-pinouts/{filename}",
        "source": candidate.relative_to(ROOT).as_posix(),
    }


def board_view(resolved: dict[str, Any]) -> dict[str, Any]:
    """Create a presentation-only Board view; it cannot alter topology."""
    blocks = []
    for item in resolved.get("instances", []):
        pins = _presentation_pins(item["part"])
        blocks.append({
            "id": item["id"],
            "type": "device",
            "part": item["part"],
            "label": item["id"],
            "pins": pins,
            "pin_anchors": _pin_anchors(item["id"], pins),
            "resource": _chip_frame(item["part"]),
        })
    wires = [
        {
            "id": f"edge:{item['from']}->{item['to']}",
            "from": item["from"],
            "to": item["to"],
            # Component resolution currently rejects implicit bus connections.
            # Keep the Board's accepted route scope explicit so a later bus
            # contract cannot accidentally inherit scalar-route behavior.
            "kind": "scalar",
        }
        for item in resolved.get("edges", [])
    ]
    return {"format": "components.component-board-view@1", "source_of_truth": "components.resolved-component@1", "component_id": resolved.get("component_id"), "read_only": True, "blocks": blocks, "nets": [{"id": item["id"], "kind": item["kind"]} for item in resolved.get("nets", [])], "wires": wires, "message": "This is a drawable view of resolved Component topology. Edit text Component source, then resolve again."}
