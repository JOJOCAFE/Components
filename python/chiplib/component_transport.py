"""Versioned JSON envelopes between readable Component source and clients."""
from __future__ import annotations
from typing import Any

def board_view(resolved: dict[str, Any]) -> dict[str, Any]:
    """Create a presentation-only Board view; it cannot alter topology."""
    return {"format": "components.component-board-view@1", "source_of_truth": "components.resolved-component@1", "component_id": resolved.get("component_id"), "read_only": True, "blocks": [{"id": item["id"], "type": "device", "part": item["part"], "label": item["id"]} for item in resolved.get("instances", [])], "nets": [{"id": item["id"], "kind": item["kind"]} for item in resolved.get("nets", [])], "wires": [{"from": item["from"], "to": item["to"]} for item in resolved.get("edges", [])], "message": "This is a drawable view of resolved Component topology. Edit text Component source, then resolve again."}
