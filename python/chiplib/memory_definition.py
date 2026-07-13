"""Resolve compact asynchronous-memory Devices without classing them as 74xx.

The live DB still consumes the legacy ``db.component.digital`` runtime shape.
That compatibility output is not an authoring classification: memory sources
validate against their own schema and only adapt at the resolver boundary.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from .compact_definition import COMPACT_SCHEMA, json_load, resolve_compact_definition


MEMORY_SCHEMA = "db.component.memory.compact"
MEMORY_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "lib" / "standard" / "compact.memory.schema.json"


def validate_compact_memory_definition(source: Mapping[str, Any]) -> list[str]:
    """Return structural errors for a human-authored memory Device source."""
    schema = json_load(MEMORY_SCHEMA_PATH)
    return [error.message for error in Draft202012Validator(schema).iter_errors(dict(source))]


def resolve_compact_memory_definition(source: Mapping[str, Any], package_root: Path) -> dict[str, Any]:
    """Resolve a memory Device through the legacy-compatible runtime adapter."""
    if source.get("schema") != MEMORY_SCHEMA:
        raise ValueError(f"expected {MEMORY_SCHEMA}, got {source.get('schema')!r}")
    errors = validate_compact_memory_definition(source)
    if errors:
        raise ValueError("invalid compact memory definition: " + "; ".join(errors))
    compatibility_source = deepcopy(dict(source))
    compatibility_source["schema"] = COMPACT_SCHEMA
    resolved = resolve_compact_definition(compatibility_source, package_root)
    # A compatibility candidate keeps the former canonical logic object as the
    # source of truth while using the compact memory vocabulary for authoring.
    # Restore it only at the runtime boundary, just as legacy timing is
    # restored by the shared compact resolver.
    legacy_logic = source.get("logic", {}).get("legacy_canonical") if isinstance(source.get("logic"), Mapping) else None
    if isinstance(legacy_logic, Mapping):
        resolved["logic"] = deepcopy(dict(legacy_logic))
    resolved["authoring"] = {"schema": MEMORY_SCHEMA, "profile": source["profile"], "source": "definition/definition.json"}
    return resolved
