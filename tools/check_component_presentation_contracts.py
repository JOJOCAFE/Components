#!/usr/bin/env python3
"""Check the closed C3 Resource and deferred C4 Board ownership contracts.

This lightweight gate deliberately has no parser, runtime, or visual-editor
dependency.  It verifies that the checked fixture shapes accept presentation
records and reject a second source of electrical truth.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "Language" / "fixtures" / "component-presentation-contract"
SCHEMAS = ROOT / "Language" / "schemas"

RESOURCE_KEYS = {"id", "target", "resource", "presentation"}
BOARD_KEYS = {
    "schema", "version", "topology_ref", "resource_bindings", "placements",
    "routes", "widgets", "physical_captures", "view",
}
RESOURCE_FORBIDDEN = {
    "behavior", "model", "timing", "pins", "ports", "direction", "polarity",
    "topology", "nets", "buses", "edges", "connections", "drivers", "state",
    "events", "operations", "callbacks", "clock", "values",
}
BOARD_FORBIDDEN = {
    "behavior", "model", "timing", "pins", "ports", "instances", "devices",
    "nets", "buses", "edges", "connections", "drivers", "state", "events",
    "operations", "callbacks", "clock", "values", "parameters",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ownership_error(candidate: dict[str, Any], allowed: set[str], forbidden: set[str], code: str) -> str | None:
    keys = set(candidate)
    if keys & forbidden or keys - allowed:
        return code
    return None


def check_topology_ref(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"component_id", "schema", "digest"}
        and isinstance(value["component_id"], str)
        and value["schema"] == "components.resolved-component@1"
        and isinstance(value["digest"], str)
        and value["digest"].startswith("sha256:")
        and len(value["digest"]) == 71
    )


def validate_resource_document(document: dict[str, Any]) -> str | None:
    if set(document) != {"schema", "version", "topology_ref", "bindings"}:
        return "E_RESOURCE_OWNERSHIP"
    if document.get("schema") != "components.resource-binding@1" or document.get("version") != 1:
        return "E_RESOURCE_SCHEMA"
    if not check_topology_ref(document.get("topology_ref")) or not isinstance(document.get("bindings"), list):
        return "E_RESOURCE_SCHEMA"
    for binding in document["bindings"]:
        if not isinstance(binding, dict):
            return "E_RESOURCE_SCHEMA"
        error = ownership_error(binding, RESOURCE_KEYS, RESOURCE_FORBIDDEN, "E_RESOURCE_OWNERSHIP")
        if error:
            return error
        target = binding.get("target")
        resource = binding.get("resource")
        if not isinstance(binding.get("id"), str) or not isinstance(target, dict) or not isinstance(resource, dict):
            return "E_RESOURCE_SCHEMA"
        if set(target) != {"kind", "id"} or target.get("kind") not in {"device-instance", "probe", "display"} or not isinstance(target.get("id"), str):
            return "E_RESOURCE_SCHEMA"
        if set(resource) != {"id", "digest", "view"} or not all(isinstance(resource.get(key), str) for key in resource):
            return "E_RESOURCE_SCHEMA"
        presentation = binding.get("presentation", {})
        if not isinstance(presentation, dict) or set(presentation) - {"label", "symbol", "display_kind", "package"}:
            return "E_RESOURCE_OWNERSHIP"
    return None


def validate_board_document(document: dict[str, Any]) -> str | None:
    error = ownership_error(document, BOARD_KEYS, BOARD_FORBIDDEN, "E_BOARD_OWNERSHIP")
    if error:
        return error
    required = BOARD_KEYS - {"view"}
    if not required <= set(document) or document.get("schema") != "components.board-profile@1" or document.get("version") != 1:
        return "E_BOARD_SCHEMA"
    if not check_topology_ref(document.get("topology_ref")):
        return "E_BOARD_SCHEMA"
    for field in ("resource_bindings", "placements", "routes", "widgets", "physical_captures"):
        if not isinstance(document.get(field), list):
            return "E_BOARD_SCHEMA"
    allowed_targets = {"device-instance", "boundary-port", "probe", "display"}
    for placement in document["placements"]:
        if not isinstance(placement, dict) or set(placement) - {"target", "position", "rotation"}:
            return "E_BOARD_SCHEMA"
        target = placement.get("target", {})
        position = placement.get("position", {})
        if not isinstance(target, dict) or set(target) != {"kind", "id"} or target.get("kind") not in allowed_targets or not isinstance(target.get("id"), str):
            return "E_BOARD_SCHEMA"
        if not isinstance(position, dict) or set(position) != {"x", "y"}:
            return "E_BOARD_SCHEMA"
    for route in document["routes"]:
        if not isinstance(route, dict) or set(route) != {"edge_id", "points"} or not isinstance(route.get("edge_id"), str):
            return "E_BOARD_SCHEMA"
        if not isinstance(route.get("points"), list) or len(route["points"]) < 2:
            return "E_BOARD_SCHEMA"
    for widget in document["widgets"]:
        target = widget.get("target", {}) if isinstance(widget, dict) else {}
        if (
            not isinstance(widget, dict)
            or set(widget) != {"target", "kind", "read_only"}
            or widget.get("read_only") is not True
            or not isinstance(target, dict)
            or set(target) != {"kind", "id"}
            or target.get("kind") not in {"probe", "display"}
            or not isinstance(target.get("id"), str)
        ):
            return "E_BOARD_SCHEMA"
    return None


def main() -> int:
    errors: list[str] = []
    resource_schema = load(SCHEMAS / "resource-binding.schema.json")
    board_schema = load(SCHEMAS / "board-profile.schema.json")
    if resource_schema.get("additionalProperties") is not False or board_schema.get("additionalProperties") is not False:
        errors.append("schemas must be closed at their top-level ownership boundary")
    resource_document = load(FIXTURES / "resource-binding.valid.json")
    board_document = load(FIXTURES / "board-profile.valid.json")
    if validate_resource_document(resource_document):
        errors.append("resource-binding.valid.json was rejected")
    if validate_board_document(board_document):
        errors.append("board-profile.valid.json was rejected")
    if resource_document.get("topology_ref") != board_document.get("topology_ref"):
        errors.append("Board profile must preserve the Resource binding topology identity")
    negative = load(FIXTURES / "negative-ownership.json")
    if negative.get("schema") != "components.presentation-negative-ownership@1":
        errors.append("negative fixture has wrong schema")
    for case in negative.get("resource_cases", []):
        actual = ownership_error(case.get("candidate", {}), RESOURCE_KEYS, RESOURCE_FORBIDDEN, "E_RESOURCE_OWNERSHIP")
        if actual != case.get("expected_diagnostic"):
            errors.append(f"{case.get('id')}: expected {case.get('expected_diagnostic')}, got {actual}")
    for case in negative.get("board_cases", []):
        actual = validate_board_document(case.get("candidate", {}))
        if actual != case.get("expected_diagnostic"):
            errors.append(f"{case.get('id')}: expected {case.get('expected_diagnostic')}, got {actual}")
    if errors:
        print("COMPONENT PRESENTATION CONTRACT CHECK FAIL")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("COMPONENT PRESENTATION CONTRACT CHECK PASS (2 valid, 6 ownership-negative fixtures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
