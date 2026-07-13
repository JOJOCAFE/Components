"""Resolve typed human-authored non-digital components to the stable package shape.

This is deliberately separate from ``compact_definition``: a resistor or a
virtual probe must not acquire invented digital timing or HDL requirements.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, RefResolver


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "lib" / "standard"
SCHEMAS = {
    "db.component.passive.compact": "compact.passive.schema.json",
    "db.component.virtual.compact": "compact.virtual.schema.json",
    "db.component.discrete.compact": "compact.discrete.schema.json",
    "db.component.support.compact": "compact.support.schema.json",
}


def validate_compact_component(source: Mapping[str, Any]) -> list[str]:
    """Return human-facing schema errors for one typed compact source."""
    schema_name = SCHEMAS.get(str(source.get("schema", "")))
    if schema_name is None:
        return ["schema must name a Components typed compact definition"]
    path = SCHEMA_ROOT / schema_name
    schema = json.loads(path.read_text(encoding="utf-8"))
    # The envelope has a public canonical $id.  Register its local copy so
    # validation is deterministic and never tries to fetch a schema online.
    base_path = SCHEMA_ROOT / "compact.component.schema.json"
    base = json.loads(base_path.read_text(encoding="utf-8"))
    resolver = RefResolver(
        base_uri=path.as_uri(), referrer=schema,
        store={str(base["$id"]): base, base_path.as_uri(): base},
    )
    errors = [error.message for error in Draft202012Validator(schema, resolver=resolver).iter_errors(dict(source))]
    expected = str(source.get("schema", "")).split(".")
    expected_payload = expected[2] if len(expected) == 4 else ""
    payloads = [key for key in ("passive", "virtual", "discrete", "support") if key in source]
    if payloads != [expected_payload]:
        errors.append(f"{source.get('schema')!r} must contain only its {expected_payload!r} typed payload")
    return errors


def resolve_compact_component(source: Mapping[str, Any]) -> dict[str, Any]:
    """Expand a compact passive/virtual/discrete/support source losslessly.

    The result is the existing ``db.component.definition`` package shape.  It
    does not alter a live package until an equivalence gate approves activation.
    """
    errors = validate_compact_component(source)
    if errors:
        raise ValueError("invalid compact component: " + "; ".join(errors))
    about = source["about"]
    pins = _pins(source["pins"])
    package = source["package"]
    group = about["group"]
    status = _derived_status(group, bool(source.get("sources")))
    part = source["part"]
    result: dict[str, Any] = {
        "schema": "db.component.definition", "version": 1,
        "id": part, "part": part, "title": about["title"],
        "family": about["family"], "group": group, "kind": about["kind"], "role": about["role"],
        "package": {"kind": package["kind"], "pins": len(pins), **({"default": package["default"]} if "default" in package else {})},
        "status": status, "pins": pins,
        "simulation": deepcopy(source["simulation"]), "ui": deepcopy(source["ui"]),
        "definition_layers": {
            "component": {"schema": "db.component.definition", "version": 1, "part": part, "title": about["title"], "family": about["family"], "group": group, "kind": about["kind"], "role": about["role"]},
            "package": {"schema": "db.component.package", "version": 1, "part": part, "packages": [{"id": package.get("default", package["kind"]), "kind": package["kind"], "pins": len(pins)}], "default_package": package.get("default", package["kind"])},
            "pins": {"schema": "db.component.pins", "version": 1, "part": part, "pins": deepcopy(pins), "buses": {}},
            "simulation": {"schema": "db.component.simulation", "version": 1, "part": part, "simulation": deepcopy(source["simulation"])},
            "ui": {"schema": "db.component.ui", "version": 1, "part": part, "ui": deepcopy(source["ui"])},
        },
        "authoring": {"schema": source["schema"], "profile": source["profile"], "source": "definition/definition.json"},
    }
    payload_key = group
    result[payload_key] = deepcopy(source[payload_key])
    if source.get("sources"):
        result["sources"] = deepcopy(source["sources"])
    if source.get("known_limitations"):
        result["known_limitations"] = deepcopy(source["known_limitations"])
    return result


def _pins(raw: Mapping[str, Any]) -> list[dict[str, Any]]:
    directions = {"in": "input", "out": "output", "io": "bidirectional"}
    pins: list[dict[str, Any]] = []
    for number, value in sorted(raw.items(), key=lambda item: int(item[0])):
        name, direction = value[0], directions.get(value[1], value[1])
        pin: dict[str, Any] = {"number": int(number), "name": name, "direction": direction}
        if len(value) == 3:
            options = value[2]
            if options.get("rail"):
                pin["rail"] = options["rail"]
            if options.get("active") == "low":
                pin["active_low"] = True
            if options.get("function"):
                pin["function"] = options["function"]
        pins.append(pin)
    return pins


def _derived_status(group: str, sourced: bool) -> dict[str, str]:
    return {"datasheet": "verified" if sourced else "not_applicable", "pinout": "modeled", "python_behavior": "modeled", "verilog_model": "not_applicable", "verilog_export": "not_applicable", "tests": "modeled"}
