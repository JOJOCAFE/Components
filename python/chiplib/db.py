"""DB manifest loader."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any


JsonMap = dict[str, Any]
ROOT = Path(__file__).resolve().parents[2]
DB_ROOT = ROOT / "db"

REQUIRED_STATUS_KEYS = (
    "datasheet",
    "pinout",
    "python_behavior",
    "verilog_model",
    "verilog_export",
    "tests",
)


def db_root() -> Path:
    return DB_ROOT


def component_ids() -> list[str]:
    if not DB_ROOT.exists():
        return []
    return sorted(
        path.name
        for path in DB_ROOT.iterdir()
        if path.is_dir() and (path / "chip.json").exists()
    )


def load_component(part: str) -> JsonMap:
    path = _manifest_path(part)
    if not path.exists():
        raise KeyError(f"component DB entry not found: {part}")
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"component DB manifest must be an object: {path}")
    manifest = deepcopy(data)
    manifest.setdefault("part", path.parent.name)
    manifest["db_path"] = str(path.relative_to(ROOT))
    manifest["missing_properties"] = missing_properties(manifest)
    manifest["missing_files"] = missing_files(manifest)
    return manifest


def load_all_components() -> list[JsonMap]:
    return [load_component(part) for part in component_ids()]


def component_summary() -> JsonMap:
    components = load_all_components()
    return {
        "format": "db.summary",
        "version": 1,
        "root": str(DB_ROOT.relative_to(ROOT)),
        "count": len(components),
        "components": [
            {
                "part": item.get("part"),
                "title": item.get("title", ""),
                "family": item.get("family", ""),
                "status": deepcopy(item.get("status", {})),
                "missing_properties": list(item.get("missing_properties", [])),
                "missing_files": list(item.get("missing_files", [])),
            }
            for item in components
        ],
    }


def missing_properties(manifest: JsonMap) -> list[str]:
    missing: list[str] = []
    status = manifest.get("status", {})
    if not isinstance(status, dict):
        return list(REQUIRED_STATUS_KEYS)
    for key in REQUIRED_STATUS_KEYS:
        value = status.get(key)
        if value in (None, "", "missing", "unknown"):
            missing.append(key)
    return missing


def missing_files(manifest: JsonMap) -> list[str]:
    missing: list[str] = []
    for rel_path in _referenced_paths(manifest):
        if not (ROOT / rel_path).exists():
            missing.append(rel_path)
    return missing


def _manifest_path(part: str) -> Path:
    clean = str(part).strip()
    return DB_ROOT / clean / "chip.json"


def _referenced_paths(manifest: JsonMap) -> list[str]:
    paths: list[str] = []
    legacy = manifest.get("legacy_paths", {})
    if isinstance(legacy, dict):
        for value in legacy.values():
            if isinstance(value, str):
                paths.append(value)
            elif isinstance(value, list):
                paths.extend(str(item) for item in value)
    verilog = manifest.get("verilog", {})
    if isinstance(verilog, dict) and isinstance(verilog.get("file"), str):
        paths.append(str(verilog["file"]))
    return sorted(set(paths))
