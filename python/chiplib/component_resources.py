"""Presentation-only Resource bridge for text Components.

The bridge deliberately returns JSON small enough for a terminal, API, AI, or
future visual client.  It reads the existing Resource package; it never copies
Resource data into a resolved topology or changes a Device's electrical truth.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .db import _component_base_path, load_component
from .resource_definition import load_device_resource


ROOT = Path(__file__).resolve().parents[2]
BINDING_SCHEMA_PATH = ROOT / "Language" / "schemas" / "resource-binding.schema.json"


def inspect_resource(part: str) -> dict[str, Any]:
    """Return a stable, presentation-only description of one library Resource."""

    try:
        manifest = load_component(part)
        canonical_part = str(manifest["part"])
        package_root = _component_base_path(canonical_part)
        resource = load_device_resource(package_root, canonical_part)
    except (KeyError, ValueError) as exc:
        return _blocked(part, "resource.invalid", str(exc))
    if resource is None:
        return _blocked(
            canonical_part,
            "resource.missing",
            f"{canonical_part} has no optional presentation Resource yet. Its Device behavior is still unchanged.",
        )

    definition_path = package_root / "resource" / "definition.json"
    identity = _resource_identity(package_root)
    views = [
        {
            "id": name,
            "kind": view["kind"],
            "artifact": _relative_artifact(definition_path.parent, view["artifact"]),
        }
        for name, view in sorted(resource["views"].items())
    ]
    return {
        "format": "components.resource-inspect@1",
        "ok": True,
        "resource": {
            "id": identity,
            "digest": _file_digest(definition_path),
            "part": canonical_part,
            "views": views,
        },
        "student": {
            "title": f"Ways to show {canonical_part}",
            "message": "Choose a view to see the part. This changes only its picture and label, never its logic or wires.",
            "available_views": [item["id"] for item in views],
        },
        "boundary": "Presentation only: no pins, behavior, timing, nets, operations, coordinates, or Board state are returned.",
        "diagnostics": [],
    }


def bind_resource(
    resolved: dict[str, Any], *, target_id: str, part: str, view: str,
    label: str | None = None,
) -> dict[str, Any]:
    """Create one checked Resource binding for an existing Device instance.

    A binding is an additive transport record.  The resolved Component passed
    in is neither mutated nor embedded, preserving topology ownership.
    """

    if not resolved.get("ok"):
        return _blocked(str(resolved.get("component_id", "Component")), "resource.component_invalid", "Resolve and fix the Component before attaching a presentation Resource.")
    instance = next((item for item in resolved.get("instances", []) if item.get("id") == target_id), None)
    if instance is None:
        return _blocked(str(resolved.get("component_id", "Component")), "resource.target_missing", f"No Device instance named {target_id!r} exists in this resolved Component.")
    if instance.get("part") != part:
        return _blocked(str(resolved.get("component_id", "Component")), "resource.part_mismatch", f"{target_id} is {instance.get('part')}, so it cannot use a Resource for {part}.")

    inspected = inspect_resource(part)
    if not inspected["ok"]:
        return inspected
    resource = inspected["resource"]
    selected = next((item for item in resource["views"] if item["id"] == view), None)
    if selected is None:
        return _blocked(part, "resource.view_missing", f"{part} has no view named {view!r}. Try: {', '.join(inspected['student']['available_views'])}.")

    binding = {
        "id": f"{target_id}-{view}",
        "target": {"kind": "device-instance", "id": target_id},
        "resource": {"id": resource["id"], "digest": resource["digest"], "view": view},
    }
    if label:
        binding["presentation"] = {"label": label}
    data = {
        "schema": "components.resource-binding@1",
        "version": 1,
        "topology_ref": resolved_topology_ref(resolved),
        "bindings": [binding],
    }
    errors = _binding_errors(data)
    if errors:
        return _blocked(part, "resource.binding_invalid", "; ".join(errors))
    return {
        "format": "components.resource-bind@1",
        "ok": True,
        "binding": data,
        "student": {
            "message": f"{target_id} will be shown as {part} in the {view} view.",
            "next_step": "Send this JSON with the resolved Component to a reader or future visual editor.",
        },
        "boundary": "The binding is presentation-only. It did not alter Device pins, behavior, timing, topology, runtime state, or Board data.",
        "diagnostics": [],
    }


def resolved_topology_ref(resolved: dict[str, Any]) -> dict[str, str]:
    """Return the deterministic topology identity referenced by binding JSON."""

    canonical = json.dumps(resolved, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return {
        "component_id": str(resolved["component_id"]),
        "schema": "components.resolved-component@1",
        "digest": "sha256:" + hashlib.sha256(canonical).hexdigest(),
    }


def _binding_errors(data: dict[str, Any]) -> list[str]:
    schema = json.loads(BINDING_SCHEMA_PATH.read_text(encoding="utf-8"))
    return [error.message for error in Draft202012Validator(schema).iter_errors(data)]


def _resource_identity(package_root: Path) -> str:
    relative = package_root.relative_to(ROOT / "lib" / "standard")
    return "standard." + ".".join(relative.parts) + ".resource@1"


def _relative_artifact(base: Path, artifact: str) -> str:
    return (base / artifact).resolve().relative_to(ROOT).as_posix()


def _file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _blocked(part: str, code: str, message: str) -> dict[str, Any]:
    return {
        "format": "components.resource-inspect@1",
        "ok": False,
        "resource": {"part": part},
        "diagnostics": [{"code": code, "message": message}],
        "boundary": "Resources are presentation-only and cannot repair or replace Device truth.",
    }
