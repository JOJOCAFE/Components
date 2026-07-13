#!/usr/bin/env python3
"""Check compact Device migration records without changing package sources.

The check inventories only compact Device sources that are active or explicitly
marked as pilots, proves their generated runtime record is fresh, and validates
any optional Resource map.  It is not a broad migration command.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from chiplib.compact_definition import COMPACT_SCHEMA, resolve_compact_definition  # noqa: E402
from chiplib.compact_component_definition import SCHEMAS as COMPONENT_SCHEMAS, resolve_compact_component  # noqa: E402
from chiplib.memory_definition import MEMORY_SCHEMA, resolve_compact_memory_definition  # noqa: E402
from chiplib.resource_definition import load_device_resource  # noqa: E402


@dataclass(frozen=True)
class MigrationRecord:
    part: str
    device_class: str
    state: str
    source: Path
    resolved: Path
    resource: Path | None


def _render(data: object) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def collect_records(root: Path = ROOT) -> list[MigrationRecord]:
    """Return explicit active/pilot compact sources in stable display order."""
    records: list[MigrationRecord] = []
    for source in sorted((root / "lib" / "standard").glob("**/definition/*.json")):
        data = json.loads(source.read_text(encoding="utf-8"))
        schema = data.get("schema")
        if schema not in {COMPACT_SCHEMA, MEMORY_SCHEMA, *COMPONENT_SCHEMAS}:
            continue
        state = "active" if source.name == "definition.json" else "pilot"
        if source.name not in {"definition.json", "compact.pilot.json"}:
            raise ValueError(f"unsupported compact migration source name: {source}")
        package = source.parents[1]
        resolved = package / "generated" / ("resolved.json" if state == "active" else "compact.pilot.resolved.json")
        resource = package / "resource" / "definition.json"
        device_class = (
            "digital" if schema == COMPACT_SCHEMA else "memory"
            if schema == MEMORY_SCHEMA else str(schema).split(".")[2]
        )
        records.append(MigrationRecord(
            part=str(data["part"]), device_class=device_class,
            state=state, source=source, resolved=resolved,
            resource=resource if resource.exists() else None,
        ))
    return records


def validate_record(record: MigrationRecord) -> list[str]:
    """Return all freshness and ownership failures for one explicit record."""
    source_data = json.loads(record.source.read_text(encoding="utf-8"))
    package = record.source.parents[1]
    try:
        schema = source_data["schema"]
        resolved = (
            resolve_compact_definition(source_data, package)
            if schema == COMPACT_SCHEMA else
            resolve_compact_memory_definition(source_data, package)
            if schema == MEMORY_SCHEMA else resolve_compact_component(source_data)
        )
    except (ValueError, KeyError) as error:
        return [f"{record.part}: source does not resolve: {error}"]
    failures: list[str] = []
    if not record.resolved.is_file():
        failures.append(f"{record.part}: missing generated runtime record {record.resolved.relative_to(ROOT)}")
    elif record.resolved.read_text(encoding="utf-8") != _render(resolved):
        failures.append(f"{record.part}: stale generated runtime record {record.resolved.relative_to(ROOT)}")
    try:
        resource = load_device_resource(package, record.part)
    except ValueError as error:
        failures.append(f"{record.part}: invalid Resource map: {error}")
    else:
        if resource is not None and ("resource" in resolved or "views" in resolved):
            failures.append(f"{record.part}: Resource leaked into resolved Device facts")
    return failures


def main() -> int:
    records = collect_records()
    failures = [failure for record in records for failure in validate_record(record)]
    print("part       class    state   source                                      resolved                         resource")
    for record in records:
        print(
            f"{record.part:<10} {record.device_class:<8} {record.state:<7} "
            f"{record.source.relative_to(ROOT)!s:<43} {record.resolved.relative_to(ROOT)!s:<32} "
            f"{'yes' if record.resource else 'no'}"
        )
    if failures:
        print("\nMIGRATION GATE FAILED", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"\nMIGRATION GATE PASS: {len(records)} explicit compact Device records are current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
