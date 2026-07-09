"""DB manifest loader."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any

from .netlist import VERILOG_MAPPINGS


JsonMap = dict[str, Any]
ROOT = Path(__file__).resolve().parents[2]
DB_ROOT = ROOT / "db"
CHIP_STATUS_PATH = ROOT / "CHIP_STATUS.md"

REQUIRED_STATUS_KEYS = (
    "datasheet",
    "pinout",
    "python_behavior",
    "verilog_model",
    "verilog_export",
    "tests",
)

GROUPED_MANIFEST_NAMES = ("chip.json", "component.json")
CHIP_STATUS_GROUPS = {"74xx", "memory"}


def db_root() -> Path:
    return DB_ROOT


def component_ids() -> list[str]:
    return sorted(_manifest_paths())


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
    manifest.setdefault("id", manifest["part"])
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
                "id": item.get("id", item.get("part")),
                "group": item.get("group", ""),
                "kind": item.get("kind", ""),
                "role": item.get("role", ""),
                "title": item.get("title", ""),
                "family": item.get("family", ""),
                "status": deepcopy(item.get("status", {})),
                "missing_properties": list(item.get("missing_properties", [])),
                "missing_files": list(item.get("missing_files", [])),
            }
            for item in components
        ],
    }


def audit_db() -> JsonMap:
    components = load_all_components()
    legacy_components = [item for item in components if _has_legacy_catalog_contract(item)]
    db_parts = {str(item.get("part", "")).upper() for item in legacy_components}
    all_db_parts = {str(item.get("part", "")).upper() for item in components}
    legacy = legacy_catalog_parts()
    legacy_parts = set(legacy["verilog_models"])
    errors: list[JsonMap] = []
    warnings: list[JsonMap] = []

    for manifest in components:
        part = str(manifest.get("part", ""))
        location = str(manifest.get("db_path", f"db/{part}/chip.json"))
        for key in manifest.get("missing_properties", []):
            errors.append(_issue("missing_property", part, location, f"missing status/property: {key}"))
        for path in manifest.get("missing_files", []):
            errors.append(_issue("missing_file", part, location, f"referenced file does not exist: {path}"))

        package = manifest.get("package", {})
        pins = manifest.get("pins", [])
        if isinstance(package, dict) and isinstance(pins, list):
            expected_pins = package.get("pins")
            if expected_pins != len(pins):
                errors.append(_issue(
                    "pin_count_mismatch",
                    part,
                    location,
                    f"package pins={expected_pins} but manifest has {len(pins)} pins",
                ))
        if _requires_power_pin(manifest) and not any(isinstance(pin, dict) and pin.get("direction") == "power" for pin in pins if isinstance(pins, list)):
            errors.append(_issue("missing_power_pin", part, location, "manifest has no power pins"))

        seen_numbers: set[int] = set()
        for pin in pins if isinstance(pins, list) else []:
            if not isinstance(pin, dict):
                errors.append(_issue("invalid_pin", part, location, "pin entry is not an object"))
                continue
            number = pin.get("number")
            name = str(pin.get("name", ""))
            if isinstance(number, int):
                if number in seen_numbers:
                    errors.append(_issue("duplicate_pin", part, location, f"duplicate pin number: {number}"))
                seen_numbers.add(number)
            if name.startswith("/") and pin.get("active_low") is not True:
                warnings.append(_issue("active_low_flag_missing", part, location, f"{name} should set active_low=true"))
            if pin.get("active_low") is True and not name.startswith("/"):
                warnings.append(_issue("active_low_name_mismatch", part, location, f"{name} sets active_low but name is not /-prefixed"))

        verilog = manifest.get("verilog", {})
        if isinstance(verilog, dict):
            module = verilog.get("module")
            file_name = verilog.get("file")
            if isinstance(module, str) and isinstance(file_name, str):
                model_path = ROOT / file_name
                if model_path.exists():
                    text = model_path.read_text(encoding="utf-8")
                    if re.search(rf"\bmodule\s+{re.escape(module)}\b", text) is None:
                        errors.append(_issue("verilog_module_missing", part, file_name, f"module {module} not found"))

        status = manifest.get("status", {})
        export_status = status.get("verilog_export") if isinstance(status, dict) else None
        has_export_mapping = part.upper() in VERILOG_MAPPINGS
        if _has_legacy_catalog_contract(manifest) and export_status == "tested" and not has_export_mapping:
            errors.append(_issue("export_status_without_mapping", part, location, "status says verilog_export=tested but no mapping exists"))
        if _has_legacy_catalog_contract(manifest) and has_export_mapping and export_status in (None, "", "missing", "unknown"):
            warnings.append(_issue("export_mapping_without_status", part, location, "Verilog mapping exists but export status is not set"))

        if _has_legacy_catalog_contract(manifest) and part.upper() not in legacy_parts:
            warnings.append(_issue("db_part_missing_legacy_model", part, location, "DB part has no legacy Verilog model file"))
        pinout_parts = set(legacy["pinouts"])
        if _has_legacy_catalog_contract(manifest) and part.upper() not in pinout_parts:
            warnings.append(_issue("db_part_missing_legacy_pinout", part, location, "DB part has no legacy pinout file"))

    missing_db = sorted(legacy_parts - db_parts)
    if missing_db:
        warnings.append({
            "code": "legacy_parts_missing_db",
            "severity": "warning",
            "message": f"{len(missing_db)} legacy model parts do not have DB manifests",
            "parts": missing_db,
        })
    missing_model = sorted(db_parts - legacy_parts)
    if missing_model:
        warnings.append({
            "code": "db_parts_missing_legacy_model",
            "severity": "warning",
            "message": f"{len(missing_model)} DB parts do not have legacy model files",
            "parts": missing_model,
        })
    status_report = db_status_report()
    errors.extend(status_report["errors"])
    warnings.extend(status_report["warnings"])

    return {
        "format": "db.audit",
        "version": 1,
        "ok": not errors,
        "root": str(DB_ROOT.relative_to(ROOT)),
        "db_count": len(all_db_parts),
        "legacy_contract_count": len(db_parts),
        "legacy_model_count": len(legacy_parts),
        "legacy_pinout_count": len(legacy["pinouts"]),
        "coverage": {
            "db_parts": sorted(db_parts),
            "legacy_model_parts": sorted(legacy_parts),
            "legacy_pinout_parts": sorted(legacy["pinouts"]),
            "legacy_parts_missing_db": missing_db,
            "db_parts_missing_legacy_model": missing_model,
        },
        "chip_status": status_report,
        "errors": errors,
        "warnings": warnings,
    }


def db_status_report() -> JsonMap:
    components = load_all_components()
    chip_status_components = [item for item in components if _reports_to_chip_status(item)]
    generated = {
        "verified": sorted(
            str(item.get("part", "")).upper()
            for item in chip_status_components
            if _status(item, "pinout") == "verified" and _status(item, "datasheet") == "verified"
        ),
        "modeled": sorted(
            str(item.get("part", "")).upper()
            for item in chip_status_components
            if _status(item, "python_behavior") == "modeled" or _status(item, "verilog_model") == "modeled"
        ),
        "tested": sorted(
            str(item.get("part", "")).upper()
            for item in chip_status_components
            if _status(item, "verilog_export") == "tested"
        ),
        "missing_datasheet": sorted(
            str(item.get("part", "")).upper()
            for item in chip_status_components
            if _status(item, "datasheet") in ("missing", "unknown")
        ),
    }
    chip_status = parse_chip_status()
    errors: list[JsonMap] = []
    warnings: list[JsonMap] = []

    checks = (
        ("verified", "verified"),
        ("modeled", "modeled"),
        ("tested", "tested"),
        ("missing_datasheet", "missing_datasheet"),
    )
    for generated_key, status_key in checks:
        generated_parts = set(generated[generated_key])
        status_parts = set(chip_status[status_key])
        for part in sorted(generated_parts - status_parts):
            errors.append(_issue(
                "chip_status_missing_db_part",
                part,
                str(CHIP_STATUS_PATH.relative_to(ROOT)),
                f"DB marks {part} as {generated_key}, but CHIP_STATUS.md does not list it in {status_key}",
            ))
        missing_db_parts = sorted(status_parts - generated_parts)
        if missing_db_parts:
            warnings.append({
                "code": "chip_status_parts_missing_db",
                "severity": "warning",
                "category": status_key,
                "message": f"{len(missing_db_parts)} CHIP_STATUS.md {status_key} parts do not have matching DB status yet",
                "parts": missing_db_parts,
            })

    return {
        "format": "db.status",
        "version": 1,
        "ok": not errors,
        "source": str(CHIP_STATUS_PATH.relative_to(ROOT)),
        "generated": generated,
        "chip_status": chip_status,
        "errors": errors,
        "warnings": warnings,
    }


def legacy_catalog_parts() -> JsonMap:
    return {
        "verilog_models": sorted(set(_legacy_74hc_models()) | set(_legacy_memory_models())),
        "pinouts": sorted(set(_legacy_74hc_pinouts()) | set(_legacy_memory_pinouts())),
    }


def parse_chip_status() -> JsonMap:
    if not CHIP_STATUS_PATH.exists():
        return {"verified": [], "modeled": [], "tested": [], "missing_datasheet": []}
    text = CHIP_STATUS_PATH.read_text(encoding="utf-8")
    return {
        "verified": _section_parts(text, "Verified", "Modeled"),
        "modeled": _section_parts(text, "Modeled", "Tested"),
        "tested": _section_parts(text, "Tested", "Remaining Export Gap"),
        "missing_datasheet": _section_parts(text, "Missing Datasheet", None),
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
    flat = DB_ROOT / clean / "chip.json"
    if flat.exists():
        return flat
    matches = [
        path
        for path in _manifest_paths().values()
        if path.parent.name == clean
    ]
    if matches:
        return sorted(matches)[0]
    return flat


def _manifest_paths() -> dict[str, Path]:
    if not DB_ROOT.exists():
        return {}
    result: dict[str, Path] = {}
    for name in GROUPED_MANIFEST_NAMES:
        for path in DB_ROOT.glob(f"*/{name}"):
            result[path.parent.name] = path
        for path in DB_ROOT.glob(f"*/*/{name}"):
            result[path.parent.name] = path
    return result


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


def _legacy_74hc_models() -> list[str]:
    return [path.stem.upper() for path in (ROOT / "verilog" / "74xx").glob("*.v")]


def _legacy_memory_models() -> list[str]:
    return [_memory_part_id(path.stem) for path in (ROOT / "verilog" / "Memory").glob("*.v")]


def _legacy_74hc_pinouts() -> list[str]:
    return [
        path.stem.upper()
        for path in (ROOT / "verilog" / "74xx").glob("*.v")
        if "Embedded pinout documentation" in path.read_text(encoding="utf-8")
    ]


def _legacy_memory_pinouts() -> list[str]:
    return [
        _memory_part_id(path.stem)
        for path in (ROOT / "verilog" / "Memory").glob("*.v")
        if "Embedded pinout documentation" in path.read_text(encoding="utf-8")
    ]


def _memory_part_id(value: str) -> str:
    return str(value).upper()


def _status(manifest: JsonMap, key: str) -> str:
    status = manifest.get("status", {})
    if isinstance(status, dict):
        return str(status.get(key, ""))
    return ""


def _has_legacy_catalog_contract(manifest: JsonMap) -> bool:
    group = str(manifest.get("group", "")).lower()
    return group in ("", "74xx", "memory")


def _reports_to_chip_status(manifest: JsonMap) -> bool:
    group = str(manifest.get("group", "")).lower()
    return group == "" or group in CHIP_STATUS_GROUPS


def _requires_power_pin(manifest: JsonMap) -> bool:
    group = str(manifest.get("group", "")).lower()
    role = str(manifest.get("role", "")).lower()
    kind = str(manifest.get("kind", "")).lower()
    if group in ("virtual", "passive", "discrete"):
        return False
    if kind == "virtual" or role in ("stimulus", "probe", "rail", "passive", "discrete"):
        return False
    return True


def _section_parts(text: str, heading: str, next_heading: str | None) -> list[str]:
    start = text.find(f"## {heading}")
    if start < 0:
        return []
    end = len(text)
    if next_heading is not None:
        next_start = text.find(f"## {next_heading}", start + 1)
        if next_start >= 0:
            end = next_start
    section = text[start:end]
    return sorted(set(
        part
        for part in (item.upper() for item in re.findall(r"`([^`]+)`", section))
        if _looks_like_part_id(part)
    ))


def _looks_like_part_id(value: str) -> bool:
    if any(char in value for char in " /*.-"):
        return False
    return re.match(r"^(74HC[0-9A-Z]+|[A-Z]*[0-9][A-Z0-9]*)$", value) is not None


def _issue(code: str, part: str, location: str, message: str) -> JsonMap:
    return {
        "code": code,
        "severity": "error" if code.startswith(("missing_", "pin_count", "duplicate", "invalid", "verilog_module", "export_status")) else "warning",
        "part": part,
        "location": location,
        "message": message,
    }
