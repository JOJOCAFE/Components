"""Validate optional device-to-presentation resource mappings.

Resources deliberately stay outside the device definition: a DIP symbol tells
the board/editor how to show a 74HC00, but it does not say what NAND means or
how quickly it switches.  The compact resolver checks this link when present
without adding resource data to its canonical runtime device record.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
RESOURCE_SCHEMA_PATH = ROOT / "lib" / "standard" / "resource.schema.json"


def load_device_resource(package_root: Path, expected_part: str) -> dict[str, Any] | None:
    """Load one optional resource map and prove that its local links are safe.

    ``None`` means that a legacy package has not yet been split.  That remains
    valid during migration.  A present resource map must be correct rather than
    silently falling back to a guessed symbol or footprint.
    """

    path = package_root / "resource" / "definition.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid resource JSON: {path}: {error}") from error
    schema = json.loads(RESOURCE_SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(data)]
    if errors:
        raise ValueError(f"invalid resource definition {path}: " + "; ".join(errors))
    maps = data["maps"]
    if maps["part"] != expected_part:
        raise ValueError(f"resource definition part {maps['part']!r} does not match {expected_part!r}")
    for label, relative in [("device_definition", maps["device_definition"]), *[(f"view:{name}", view["artifact"]) for name, view in data["views"].items()]]:
        target = _local_file(path.parent, relative, package_root)
        if not target.is_file():
            raise ValueError(f"resource {label} does not exist: {target}")
    return data


def _local_file(base: Path, relative: str, package_root: Path) -> Path:
    target = (base / relative).resolve()
    root = package_root.resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"resource path escapes package: {relative!r}")
    return target
