"""DB manifest loader."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any


JsonMap = dict[str, Any]
ROOT = Path(__file__).resolve().parents[2]
DB_ROOT = ROOT / "DB"
CHIP_STATUS_PATH = ROOT / "CHIP_STATUS.md"
DIGITAL_SCHEMA_PATH = DB_ROOT / "digital.schema.json"

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
    manifest = _manifest_from_definition(data, path) if path.name == "definition.json" else deepcopy(data)
    manifest.setdefault("part", path.parents[1].name if path.name == "definition.json" else path.parent.name)
    manifest.setdefault("id", manifest["part"])
    manifest["db_path"] = str(path.relative_to(ROOT))
    _apply_path_defaults(manifest, path)
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


def component_catalog(*, group: str | None = None) -> JsonMap:
    """Return frontend-oriented component catalog metadata."""

    components = load_all_components()
    group_filter = str(group).strip() if group else None
    if group_filter:
        components = [item for item in components if str(item.get("group", "")) == group_filter]
    groups = _group_summaries(load_all_components())
    return {
        "format": "components.db.catalog",
        "version": 1,
        "root": str(DB_ROOT.relative_to(ROOT)),
        "group": group_filter,
        "count": len(components),
        "groups": groups,
        "components": [_component_card(item) for item in components],
    }


def student_component_catalog(*, group: str | None = None) -> JsonMap:
    """Return a smaller catalog view suitable for learner-facing UIs."""

    catalog = component_catalog(group=group)
    components = [load_component(str(item["part"])) for item in catalog["components"]]
    return {
        "format": "components.db.student_catalog",
        "version": 1,
        "audience": "students ages 10-15, still useful for older learners",
        "root": catalog["root"],
        "group": catalog["group"],
        "count": catalog["count"],
        "groups": deepcopy(catalog["groups"]),
        "components": [_student_component_card(item) for item in components],
        "legend": {
            "ready": "Good for building and simulation examples.",
            "usable": "Usable, but some advanced output or evidence may be missing.",
            "needs_info": "Visible in the catalog, but students should see the missing data first.",
        },
    }


def component_detail(part: str) -> JsonMap:
    """Return frontend-oriented metadata for one component."""

    manifest = load_component(part)
    detail = _component_card(manifest)
    detail.update({
        "format": "components.db.component",
        "version": 1,
        "pins": deepcopy(manifest.get("pins", [])),
        "sources": deepcopy(manifest.get("sources", [])),
        "legacy_paths": deepcopy(manifest.get("legacy_paths", {})),
        "verilog": deepcopy(manifest.get("verilog", {})),
        "simulation": deepcopy(manifest.get("simulation", {})),
        "ui": deepcopy(manifest.get("ui", {})),
    })
    digital = load_digital_definition(part, required=False)
    if digital is not None:
        detail["digital_definition"] = {
            "path": _digital_definition_path(part).relative_to(ROOT).as_posix(),
            "schema": digital.get("schema"),
            "version": digital.get("version"),
            "generation_targets": list(digital.get("generation", {}).get("targets", [])) if isinstance(digital.get("generation"), dict) else [],
        }
    return detail


def component_metadata(part: str) -> JsonMap:
    """Alias for callers that name selected-component detail as metadata."""

    return component_detail(part)


def load_digital_definition(part: str, *, required: bool = True) -> JsonMap | None:
    """Load the generator-ready one-file digital definition for a component."""

    path = _digital_definition_path(part)
    if not path.exists():
        if required:
            raise KeyError(f"digital definition not found: {part}")
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"digital definition must be an object: {path}")
    definition = deepcopy(data)
    definition.setdefault("part", path.parents[1].name)
    definition["definition_path"] = path.relative_to(ROOT).as_posix()
    definition["validation"] = validate_digital_definition(definition)
    return definition


def load_digital_package(part: str) -> JsonMap:
    """Load a digital definition plus package layer files."""

    definition = load_digital_definition(part)
    if definition is None:
        raise KeyError(f"digital definition not found: {part}")
    manifest = load_component(part)
    base = _component_base_path(part)
    derived = _derived_package_layers(definition, manifest)
    layers = {
        "definition": {
            "component": _definition_layer(definition, base, derived, "component"),
            "package": _definition_layer(definition, base, derived, "package"),
            "pins": _definition_layer(definition, base, derived, "pins"),
            "power": _definition_layer(definition, base, derived, "power"),
            "logic": _definition_layer(definition, base, derived, "logic"),
            "timing": _definition_layer(definition, base, derived, "timing"),
            "electrical": _definition_layer(definition, base, derived, "electrical"),
        },
        "simulation": {
            "model": _load_optional_json(base / "simulation" / "model.json"),
            "netlist": _load_optional_json(base / "simulation" / "netlist.json"),
        },
        "tests": {
            "truth_table": _load_optional_json(base / "tests" / "truth_table.json"),
            "timing": _load_optional_json(base / "tests" / "timing.json"),
            "tri_state": _load_optional_json(base / "tests" / "tri_state.json"),
            "bus_fight": _load_optional_json(base / "tests" / "bus_fight.json"),
            "propagation": _load_optional_json(base / "tests" / "propagation.json"),
        },
        "symbol": {"dip": _load_optional_json(base / "symbol" / "dip.json")},
        "datasheet": {"sources": _datasheet_layer(definition, base)},
    }
    file_candidates = {
            "manifest": _manifest_path(part),
            "definition": base / "definition" / "definition.json",
            "simulation_model_py": base / "simulation" / "model.py",
            "simulation_model_v": base / "simulation" / "model.v",
            "simulation_netlist": base / "simulation" / "netlist.json",
            "simulation": base / "simulation" / "model.json",
            "symbol": base / "symbol" / "dip.json",
    }
    for key in ("component", "package", "pins", "power", "logic", "timing", "electrical"):
        legacy_path = base / "definition" / f"{key}.json"
        if legacy_path.exists():
            file_candidates[f"legacy_{key}"] = legacy_path
    files = {name: str(path.relative_to(ROOT)) for name, path in file_candidates.items() if path.exists()}
    portable_files = _portable_simulation_files(files)
    return {
        "format": "db.component.package",
        "version": 1,
        "part": definition["part"],
        "manifest": manifest,
        "definition": definition,
        "digital": definition,
        "layers": layers,
        "derived": derived,
        "files": files,
        "portable_files": portable_files,
    }


def generate_component_artifacts(part: str) -> JsonMap:
    """Generate structured artifact payloads from definition/definition.json."""

    package = load_digital_package(part)
    definition = package["digital"]
    manifest = package["manifest"]
    pins = list(definition.get("pins", []))
    buses = _digital_buses(pins)
    power = _digital_power_rails(pins)
    symbol = _dip_symbol_from_definition(definition)
    tests = _generated_test_plan(definition, package)
    docs = _documentation_data(definition, buses)
    demo = _interactive_demo_data(definition, buses)
    verilog = {
        "part": definition["part"],
        "module": definition.get("generation", {}).get("verilog", {}).get("module", ""),
        "file": definition.get("generation", {}).get("verilog", {}).get("file", ""),
        "netlist": definition.get("generation", {}).get("verilog", {}).get("netlist", ""),
        "export": deepcopy(manifest.get("verilog", {}).get("export", {})),
    }
    return {
        "format": "db.component.generated",
        "version": 1,
        "source": definition.get("definition_path", ""),
        "part": definition["part"],
        "portable_files": deepcopy(package.get("portable_files", [])),
        "artifacts": {
            "json": {
                "format": "components.generated.detail",
                "part": definition["part"],
                "title": definition.get("metadata", {}).get("title", definition["part"]),
                "family": definition.get("metadata", {}).get("family", ""),
                "group": definition.get("metadata", {}).get("group", ""),
                "role": definition.get("metadata", {}).get("role", ""),
                "package": deepcopy(definition.get("package", {})),
                "pins": deepcopy(pins),
                "buses": buses,
                "power": power,
                "logic": deepcopy(definition.get("logic", {})),
                "timing": deepcopy(definition.get("timing", {})),
            },
            "python_simulator": {
                "part": definition["part"],
                "portable": True,
                "copy_with_chip": [item["source"] for item in package.get("portable_files", []) if item.get("runtime") == "python"],
                **deepcopy(definition.get("generation", {}).get("python", {})),
            },
            "verilog_wrapper": verilog,
            "kicad_symbol": symbol,
            "svg_pinout": symbol,
            "documentation": docs,
            "unit_test": tests,
            "interactive_demo": demo,
        },
    }


def validate_digital_definition(definition: JsonMap) -> JsonMap:
    """Return structured validation for a generator-ready digital definition."""

    errors: list[JsonMap] = []
    part = str(definition.get("part", ""))
    path = str(definition.get("definition_path", f"DB/*/{part}/definition/definition.json"))
    if definition.get("schema") != "db.component.digital":
        errors.append(_issue("digital_schema_invalid", part, path, "schema must be db.component.digital"))
    if not isinstance(definition.get("version"), int) or int(definition.get("version", 0)) < 1:
        errors.append(_issue("digital_version_invalid", part, path, "version must be an integer >= 1"))
    for key in ("metadata", "package", "pins", "logic", "timing", "generation", "verification", "datasheet"):
        if key not in definition:
            errors.append(_issue("digital_missing_section", part, path, f"missing section: {key}"))
    metadata = definition.get("metadata", {})
    if not isinstance(metadata, dict):
        errors.append(_issue("digital_metadata_invalid", part, path, "metadata must be an object"))
    else:
        for key in ("title", "family", "group", "role"):
            if not isinstance(metadata.get(key), str) or not metadata.get(key):
                errors.append(_issue("digital_metadata_missing", part, path, f"metadata.{key} must be a non-empty string"))
    package = definition.get("package", {})
    pins = definition.get("pins", [])
    if not isinstance(package, dict):
        errors.append(_issue("digital_package_invalid", part, path, "package must be an object"))
    elif not isinstance(package.get("kind"), str) or not package.get("kind"):
        errors.append(_issue("digital_package_kind_invalid", part, path, "package.kind must be a non-empty string"))
    if not isinstance(pins, list) or not pins:
        errors.append(_issue("digital_pins_invalid", part, path, "pins must be a non-empty list"))
    elif isinstance(package, dict) and package.get("pins") != len(pins):
        errors.append(_issue("digital_pin_count_mismatch", part, path, f"package pins={package.get('pins')} but digital definition has {len(pins)} pins"))
    pin_numbers: set[int] = set()
    power_rails: set[str] = set()
    for pin in pins if isinstance(pins, list) else []:
        if not isinstance(pin, dict):
            errors.append(_issue("digital_pin_invalid", part, path, "pin entry is not an object"))
            continue
        number = pin.get("number")
        name = pin.get("name")
        direction = pin.get("direction")
        if not isinstance(number, int) or number < 1:
            errors.append(_issue("digital_pin_number_invalid", part, path, f"invalid pin number: {number!r}"))
        elif number in pin_numbers:
            errors.append(_issue("digital_duplicate_pin", part, path, f"duplicate pin number: {number}"))
        else:
            pin_numbers.add(number)
        if not isinstance(name, str) or not name:
            errors.append(_issue("digital_pin_name_invalid", part, path, f"pin {number} has no name"))
        if direction not in {"input", "output", "bidirectional", "passive", "power", "nc", "unknown"}:
            errors.append(_issue("digital_pin_direction_invalid", part, path, f"pin {number} has invalid direction: {direction!r}"))
        if direction == "power" and isinstance(pin.get("rail"), str):
            power_rails.add(str(pin["rail"]))
        if name.startswith("/") and pin.get("active_low") is not True:
            errors.append(_issue("digital_active_low_flag_missing", part, path, f"pin {number} {name} should set active_low=true"))
        if pin.get("active_low") is True and not name.startswith("/"):
            errors.append(_issue("digital_active_low_name_mismatch", part, path, f"pin {number} {name} sets active_low but name is not /-prefixed"))
    if "VCC" not in power_rails and "VDD" not in power_rails:
        errors.append(_issue("digital_missing_positive_rail", part, path, "digital definition has no VCC/VDD rail"))
    if "GND" not in power_rails and "VSS" not in power_rails:
        errors.append(_issue("digital_missing_ground_rail", part, path, "digital definition has no GND/VSS rail"))
    logic = definition.get("logic", {})
    if not isinstance(logic, dict) or not isinstance(logic.get("type"), str) or not logic.get("type"):
        errors.append(_issue("digital_logic_type_missing", part, path, "logic.type must be a non-empty string"))
    timing = definition.get("timing", {})
    if not isinstance(timing, dict):
        errors.append(_issue("digital_timing_invalid", part, path, "timing must be an object"))
    elif "delay_ns" in timing and (not isinstance(timing.get("delay_ns"), int) or timing.get("delay_ns") < 0):
        errors.append(_issue("digital_delay_invalid", part, path, "timing.delay_ns must be an integer >= 0"))
    layers = definition.get("definition_layers")
    if layers is not None:
        if not isinstance(layers, dict):
            errors.append(_issue("digital_definition_layers_invalid", part, path, "definition_layers must be an object"))
        else:
            for key in ("component", "package", "pins", "power", "logic", "timing", "electrical"):
                layer = layers.get(key)
                if not isinstance(layer, dict):
                    errors.append(_issue("digital_definition_layer_missing", part, path, f"definition_layers.{key} must be an object"))
                    continue
                if not isinstance(layer.get("schema"), str) or not layer.get("schema"):
                    errors.append(_issue("digital_definition_layer_schema_missing", part, path, f"definition_layers.{key}.schema must be a non-empty string"))
                if layer.get("part") != part:
                    errors.append(_issue("digital_definition_layer_part_mismatch", part, path, f"definition_layers.{key}.part must match {part}"))
    generation = definition.get("generation", {})
    targets = generation.get("targets", []) if isinstance(generation, dict) else []
    required_targets = {"json", "python_simulator", "verilog_wrapper", "kicad_symbol", "svg_pinout", "documentation", "unit_test", "interactive_demo"}
    if not isinstance(targets, list) or not required_targets.issubset(set(str(item) for item in targets)):
        errors.append(_issue("digital_generation_targets_missing", part, path, f"generation.targets must include {sorted(required_targets)}"))
    if not isinstance(generation, dict):
        errors.append(_issue("digital_generation_invalid", part, path, "generation must be an object"))
    else:
        python = generation.get("python", {})
        verilog = generation.get("verilog", {})
        if not isinstance(python, dict) or not python.get("factory") or not python.get("part"):
            errors.append(_issue("digital_generation_python_invalid", part, path, "generation.python needs factory and part"))
        if not isinstance(verilog, dict) or not verilog.get("module") or not verilog.get("file"):
            errors.append(_issue("digital_generation_verilog_invalid", part, path, "generation.verilog needs module and file"))
    tests = definition.get("verification", {}).get("tests", []) if isinstance(definition.get("verification"), dict) else []
    if not isinstance(tests, list) or not tests:
        errors.append(_issue("digital_tests_missing", part, path, "verification.tests must list required test types"))
    datasheet = definition.get("datasheet", {})
    sources = datasheet.get("sources", []) if isinstance(datasheet, dict) else []
    if not isinstance(sources, list) or not sources:
        errors.append(_issue("digital_sources_missing", part, path, "datasheet.sources must list source evidence"))
    for source in sources if isinstance(sources, list) else []:
        if not isinstance(source, dict):
            errors.append(_issue("digital_source_invalid", part, path, "datasheet source is not an object"))
            continue
        for key in ("label", "package_evidence"):
            if not isinstance(source.get(key), str) or not source.get(key):
                errors.append(_issue("digital_source_missing_field", part, path, f"datasheet source missing {key}"))
        if not isinstance(source.get("url"), str) and not isinstance(source.get("file"), str):
            errors.append(_issue("digital_source_missing_location", part, path, "datasheet source needs url or file"))
    status = definition.get("status")
    if status is not None:
        if not isinstance(status, dict):
            errors.append(_issue("digital_status_invalid", part, path, "status must be an object"))
        else:
            allowed_status = {"verified", "modeled", "tested", "missing", "blocked", "unknown", "not_applicable"}
            for key in REQUIRED_STATUS_KEYS:
                value = status.get(key)
                if value not in allowed_status:
                    errors.append(_issue("digital_status_invalid_value", part, path, f"status.{key} must be one of {sorted(allowed_status)}"))
    if part:
        errors.extend(_digital_manifest_mismatches(definition, part, path))
    return {"ok": not errors, "errors": errors}


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
        location = str(manifest.get("db_path", f"DB/{part}/chip.json"))
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

        pinout_mismatches = _pinout_mismatches(manifest)
        for mismatch in pinout_mismatches:
            errors.append(_issue(
                mismatch["code"],
                part,
                location,
                mismatch["message"],
            ))

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
        has_export_mapping = _has_db_export(manifest)
        if _has_legacy_catalog_contract(manifest) and export_status == "tested" and not has_export_mapping:
            errors.append(_issue("export_status_without_mapping", part, location, "status says verilog_export=tested but no DB export metadata exists"))
        if _has_legacy_catalog_contract(manifest) and has_export_mapping and export_status in (None, "", "missing", "unknown"):
            warnings.append(_issue("export_mapping_without_status", part, location, "DB export metadata exists but export status is not set"))

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
    legacy = legacy_catalog_parts()
    active_parts = {str(item.get("part", "")).upper() for item in chip_status_components}
    excluded_parts = set(chip_status["missing_datasheet"])
    for part in sorted(excluded_parts & (set(chip_status["verified"]) | set(chip_status["modeled"]) | set(chip_status["tested"]))):
        errors.append(_issue(
            "chip_status_exclusion_conflict",
            part,
            str(CHIP_STATUS_PATH.relative_to(ROOT)),
            f"{part} is marked missing-datasheet but also appears in an active status section",
        ))
    for part in sorted(excluded_parts & (active_parts | set(legacy["verilog_models"]) | set(legacy["pinouts"]))):
        errors.append(_issue(
            "chip_status_excluded_part_active",
            part,
            str(CHIP_STATUS_PATH.relative_to(ROOT)),
            f"{part} is marked missing-datasheet but still appears in active DB or legacy files",
        ))

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
        if status_key == "missing_datasheet":
            continue
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
        "tested": _section_parts(text, "Tested", "Export Notes"),
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
    grouped_definition = _definition_manifest_path(clean)
    if grouped_definition.exists():
        return grouped_definition
    return flat


def _digital_definition_path(part: str) -> Path:
    manifest_path = _manifest_path(part)
    if manifest_path.name == "definition.json":
        return manifest_path
    if manifest_path.exists():
        return manifest_path.parent / "definition" / "definition.json"
    return manifest_path.parent / "definition" / "definition.json"


def _component_base_path(part: str) -> Path:
    manifest_path = _manifest_path(part)
    if manifest_path.name == "definition.json":
        return manifest_path.parents[1]
    return manifest_path.parent


def _manifest_paths() -> dict[str, Path]:
    if not DB_ROOT.exists():
        return {}
    result: dict[str, Path] = {}
    for name in GROUPED_MANIFEST_NAMES:
        for path in DB_ROOT.glob(f"*/{name}"):
            result[path.parent.name] = path
        for path in DB_ROOT.glob(f"*/*/{name}"):
            result[path.parent.name] = path
    for path in DB_ROOT.glob("*/*/definition/definition.json"):
        result.setdefault(path.parents[1].name, path)
    return result


def _definition_manifest_path(part: str) -> Path:
    for path in DB_ROOT.glob("*/*/definition/definition.json"):
        if path.parents[1].name == part:
            return path
    return DB_ROOT / part / "definition" / "definition.json"


def _manifest_from_definition(definition: JsonMap, path: Path) -> JsonMap:
    base = path.parents[1]
    metadata = definition.get("metadata", {}) if isinstance(definition.get("metadata"), dict) else {}
    generation = definition.get("generation", {}) if isinstance(definition.get("generation"), dict) else {}
    verilog_generation = generation.get("verilog", {}) if isinstance(generation.get("verilog"), dict) else {}
    python_generation = generation.get("python", {}) if isinstance(generation.get("python"), dict) else {}
    netlist = _load_optional_json(base / "simulation" / "netlist.json") or {}
    netlist_verilog = netlist.get("verilog", {}) if isinstance(netlist.get("verilog"), dict) else {}
    verilog = {
        "module": verilog_generation.get("module", netlist_verilog.get("module", "")),
        "file": verilog_generation.get("file", ""),
        "export": deepcopy(netlist_verilog.get("export", {})),
    }
    if verilog_generation.get("netlist"):
        verilog["netlist"] = verilog_generation["netlist"]
    return {
        "schema": "db.chip",
        "version": 1,
        "part": definition.get("part", base.name),
        "title": metadata.get("title", definition.get("part", base.name)),
        "family": metadata.get("family", ""),
        "group": metadata.get("group", ""),
        "role": metadata.get("role", ""),
        "kind": "ic",
        "package": deepcopy(definition.get("package", {})),
        "status": deepcopy(definition.get("status", {})),
        "pins": deepcopy(definition.get("pins", [])),
        "legacy_paths": {
            "pinout": verilog.get("file", ""),
            "verilog": verilog.get("file", ""),
            "python_behavior": python_generation.get("file", ""),
            "verilog_export": (base / "simulation" / "netlist.json").relative_to(ROOT).as_posix(),
        },
        "verilog": verilog,
        "python": deepcopy(python_generation),
        "sources": deepcopy(definition.get("datasheet", {}).get("sources", [])),
    }


def _apply_path_defaults(manifest: JsonMap, path: Path) -> None:
    group = _manifest_group_from_path(path)
    if group and not manifest.get("group"):
        manifest["group"] = group
    if path.name == "chip.json" and group in {"74xx", "memory"}:
        manifest.setdefault("kind", "ic")
        manifest.setdefault("role", "logic" if group == "74xx" else "memory")


def _manifest_group_from_path(path: Path) -> str:
    try:
        rel = path.relative_to(DB_ROOT)
    except ValueError:
        return ""
    parts = rel.parts
    if len(parts) >= 3:
        return parts[0].lower()
    return ""


def _group_summaries(components: list[JsonMap]) -> list[JsonMap]:
    counts: dict[str, int] = {}
    for item in components:
        group = str(item.get("group", ""))
        if group:
            counts[group] = counts.get(group, 0) + 1
    indexes = _db_group_indexes()
    result: list[JsonMap] = []
    for group_id in sorted(counts):
        index = indexes.get(group_id, {})
        result.append({
            "id": group_id,
            "title": index.get("title", group_id),
            "path": index.get("path", f"DB/{group_id}"),
            "count": counts[group_id],
            "migration_status": index.get("migration_status", ""),
        })
    return result


def _db_group_indexes() -> dict[str, JsonMap]:
    indexes: dict[str, JsonMap] = {}
    if not DB_ROOT.exists():
        return indexes
    for path in sorted(DB_ROOT.glob("*/index.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            group_id = str(data.get("id", path.parent.name))
            data.setdefault("path", str(path.parent.relative_to(ROOT)))
            indexes[group_id] = data
    return indexes


def _component_card(manifest: JsonMap) -> JsonMap:
    package = manifest.get("package", {})
    status = manifest.get("status", {})
    pins = manifest.get("pins", [])
    return {
        "id": manifest.get("id", manifest.get("part", "")),
        "part": manifest.get("part", manifest.get("id", "")),
        "title": manifest.get("title", manifest.get("part", "")),
        "group": manifest.get("group", ""),
        "kind": manifest.get("kind", ""),
        "role": manifest.get("role", ""),
        "family": manifest.get("family", ""),
        "db_path": manifest.get("db_path", ""),
        "package": deepcopy(package) if isinstance(package, dict) else {},
        "pin_count": len(pins) if isinstance(pins, list) else 0,
        "status": deepcopy(status) if isinstance(status, dict) else {},
        "capabilities": _component_capabilities(manifest),
        "warnings": _component_warnings(manifest),
    }


def _student_component_card(manifest: JsonMap) -> JsonMap:
    part = str(manifest.get("part", manifest.get("id", "")))
    capabilities = _component_capabilities(manifest)
    warnings = _component_warnings(manifest)
    pins = manifest.get("pins", [])
    pin_list = pins if isinstance(pins, list) else []
    status = manifest.get("status", {})
    status_map = status if isinstance(status, dict) else {}
    ready = bool(capabilities["physical_pinout"] and capabilities["python_behavior"] and not warnings)
    export_ready = bool(capabilities["verilog_export"])
    if ready and export_ready:
        readiness = "ready"
    elif capabilities["python_behavior"] or capabilities["simulation_service"]:
        readiness = "usable"
    else:
        readiness = "needs_info"
    return {
        "part": part,
        "title": manifest.get("title", part),
        "group": manifest.get("group", ""),
        "kind": manifest.get("kind", ""),
        "role": manifest.get("role", ""),
        "readiness": readiness,
        "status": {
            "datasheet": status_map.get("datasheet", "unknown"),
            "pinout": status_map.get("pinout", "unknown"),
            "python_behavior": status_map.get("python_behavior", "unknown"),
            "verilog_model": status_map.get("verilog_model", "unknown"),
            "verilog_export": status_map.get("verilog_export", "unknown"),
            "tests": status_map.get("tests", "unknown"),
        },
        "capabilities": {
            "can_simulate": bool(capabilities["python_behavior"] or capabilities["simulation_service"]),
            "can_export_verilog": export_ready,
            "has_verified_pinout": bool(capabilities["physical_pinout"]),
            "has_datasheet": bool(capabilities["datasheet_verified"]),
        },
        "pins": {
            "count": len(pin_list),
            "preview": [
                {
                    "number": pin.get("number"),
                    "name": pin.get("name"),
                    "direction": pin.get("direction"),
                }
                for pin in pin_list[:8]
                if isinstance(pin, dict)
            ],
        },
        "files": {
            "db": manifest.get("db_path", ""),
            "verilog": capabilities["verilog_file"],
        },
        "warnings": warnings,
        "student_note": _student_note(manifest, readiness),
    }


def _student_note(manifest: JsonMap, readiness: str) -> str:
    role = str(manifest.get("role", "component")).replace("_", " ")
    if readiness == "ready":
        return f"Ready to use as a {role} in examples and simulations."
    if readiness == "usable":
        return f"Usable as a {role}; check the status fields before using advanced outputs."
    return "Keep this visible, but show what information is missing before students build with it."


def _component_capabilities(manifest: JsonMap) -> JsonMap:
    status = manifest.get("status", {})
    simulation = manifest.get("simulation", {})
    verilog = manifest.get("verilog", {})
    legacy_paths = manifest.get("legacy_paths", {})
    status_map = status if isinstance(status, dict) else {}
    return {
        "physical_pinout": status_map.get("pinout") == "verified",
        "datasheet_verified": status_map.get("datasheet") == "verified",
        "python_behavior": status_map.get("python_behavior") in ("modeled", "tested"),
        "verilog_model": status_map.get("verilog_model") == "modeled",
        "verilog_export": status_map.get("verilog_export") == "tested",
        "simulation_service": simulation.get("service", "") if isinstance(simulation, dict) else "",
        "verilog_file": verilog.get("file", "") if isinstance(verilog, dict) else "",
        "legacy_files": bool(legacy_paths) if isinstance(legacy_paths, dict) else False,
    }


def _component_warnings(manifest: JsonMap) -> list[JsonMap]:
    warnings: list[JsonMap] = []
    part = str(manifest.get("part", manifest.get("id", "")))
    for key in manifest.get("missing_properties", []):
        warnings.append({"code": "missing_property", "part": part, "property": key})
    for path in manifest.get("missing_files", []):
        warnings.append({"code": "missing_file", "part": part, "path": path})
    status = manifest.get("status", {})
    if isinstance(status, dict) and status.get("datasheet") in ("missing", "unknown"):
        warnings.append({"code": "missing_datasheet", "part": part})
    return warnings


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


def _has_db_export(manifest: JsonMap) -> bool:
    verilog = manifest.get("verilog", {})
    export = verilog.get("export", {}) if isinstance(verilog, dict) else {}
    ports = export.get("ports", []) if isinstance(export, dict) else []
    output_pins = export.get("output_pins", []) if isinstance(export, dict) else []
    return isinstance(ports, list) and bool(ports) and isinstance(output_pins, list)


def _load_optional_json(path: Path) -> JsonMap | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"split package file must be an object: {path}")
    return data


def _definition_layer(definition: JsonMap, base: Path, derived: JsonMap, key: str) -> JsonMap | None:
    merged_layers = definition.get("definition_layers", {})
    if isinstance(merged_layers, dict) and isinstance(merged_layers.get(key), dict):
        return deepcopy(merged_layers[key])

    legacy_layer = _load_optional_json(base / "definition" / f"{key}.json")
    if legacy_layer is not None:
        return legacy_layer

    layer = derived.get(key)
    return deepcopy(layer) if isinstance(layer, dict) else None


def _datasheet_layer(definition: JsonMap, base: Path) -> JsonMap | None:
    datasheet = definition.get("datasheet")
    if isinstance(datasheet, dict) and isinstance(datasheet.get("sources"), list):
        return {
            "schema": "db.component.datasheet.sources",
            "version": 1,
            "part": definition.get("part", ""),
            "sources": deepcopy(datasheet["sources"]),
        }
    return _load_optional_json(base / "datasheet" / "sources.json")


def _portable_simulation_files(files: JsonMap) -> list[JsonMap]:
    result: list[JsonMap] = []
    for key, kind, runtime, copy_as in (
        ("simulation_model_py", "python_model", "python", "model.py"),
        ("simulation_model_v", "verilog_model", "verilog", "model.v"),
        ("simulation_netlist", "netlist", "metadata", "netlist.json"),
    ):
        source = files.get(key)
        if isinstance(source, str) and source:
            result.append({
                "kind": kind,
                "runtime": runtime,
                "source": source,
                "copy_as": copy_as,
            })
            if key == "simulation_model_py":
                result.append({
                    "kind": "python_runtime",
                    "runtime": "python",
                    "source": "python/chiplib/core.py",
                    "copy_as": "chiplib/core.py",
                    "shared": True,
                    "copy_once": True,
                })
    return result


def _derived_package_layers(definition: JsonMap, manifest: JsonMap) -> JsonMap:
    pins = list(definition.get("pins", [])) if isinstance(definition.get("pins"), list) else []
    return {
        "component": {
            "schema": "db.component.definition",
            "version": 1,
            "part": definition.get("part", ""),
            "title": definition.get("metadata", {}).get("title", ""),
            "family": definition.get("metadata", {}).get("family", ""),
            "group": definition.get("metadata", {}).get("group", ""),
            "kind": manifest.get("kind", ""),
            "role": definition.get("metadata", {}).get("role", manifest.get("role", "")),
        },
        "package": {
            "schema": "db.component.package",
            "version": 1,
            "part": definition.get("part", ""),
            "packages": [{
                "id": definition.get("package", {}).get("default", definition.get("package", {}).get("kind", "")),
                "kind": definition.get("package", {}).get("kind", ""),
                "pins": definition.get("package", {}).get("pins", len(pins)),
            }],
            "default_package": definition.get("package", {}).get("default", ""),
        },
        "pins": {
            "schema": "db.component.pins",
            "version": 1,
            "part": definition.get("part", ""),
            "pins": deepcopy(pins),
            "buses": _digital_buses(pins),
        },
        "power": {
            "schema": "db.component.power",
            "version": 1,
            "part": definition.get("part", ""),
            "rails": _digital_power_rails(pins),
        },
        "logic": {
            "schema": "db.component.logic",
            "version": 1,
            "part": definition.get("part", ""),
            "logic": deepcopy(definition.get("logic", {})),
        },
        "timing": {
            "schema": "db.component.timing",
            "version": 1,
            "part": definition.get("part", ""),
            "timing": deepcopy(definition.get("timing", {})),
        },
        "electrical": {
            "schema": "db.component.electrical",
            "version": 1,
            "part": definition.get("part", ""),
            "electrical": deepcopy(definition.get("electrical", {})),
        },
        "datasheet": {
            "schema": "db.component.datasheet.sources",
            "version": 1,
            "part": definition.get("part", ""),
            "sources": deepcopy(definition.get("datasheet", {}).get("sources", [])),
        },
    }


def _digital_buses(pins: list[Any]) -> JsonMap:
    buses: dict[str, list[JsonMap]] = {}
    for pin in pins:
        if not isinstance(pin, dict) or not isinstance(pin.get("bus"), str):
            continue
        buses.setdefault(str(pin["bus"]), []).append(pin)
    result: JsonMap = {}
    for name, bus_pins in sorted(buses.items()):
        ordered = sorted(bus_pins, key=lambda item: int(item.get("bit", item.get("number", 0))))
        result[name] = {
            "width": len(ordered),
            "pins_lsb_first": [int(item["number"]) for item in ordered if isinstance(item.get("number"), int)],
        }
    return result


def _digital_power_rails(pins: list[Any]) -> list[JsonMap]:
    rails: list[JsonMap] = []
    for pin in pins:
        if not isinstance(pin, dict) or pin.get("direction") != "power":
            continue
        rail = str(pin.get("rail", pin.get("name", "")))
        rails.append({
            "name": rail,
            "pin": pin.get("number"),
            "nominal_logic": 0 if rail in {"GND", "VSS"} else 1,
        })
    return rails


def _dip_symbol_from_definition(definition: JsonMap) -> JsonMap:
    pin_count = int(definition.get("package", {}).get("pins", 0))
    midpoint = pin_count // 2
    pins = list(definition.get("pins", [])) if isinstance(definition.get("pins"), list) else []
    labels = {
        str(pin["number"]): str(pin["name"])
        for pin in pins
        if isinstance(pin, dict) and isinstance(pin.get("number"), int) and pin.get("direction") in {"power", "input"}
    }
    return {
        "schema": "db.component.symbol.dip",
        "version": 1,
        "part": definition.get("part", ""),
        "shape": "dip",
        "pins": pin_count,
        "left": list(range(1, midpoint + 1)),
        "right": list(range(pin_count, midpoint, -1)),
        "labels": labels,
        "bus_groups": {name: value["pins_lsb_first"] for name, value in _digital_buses(pins).items()},
    }


def _generated_test_plan(definition: JsonMap, package: JsonMap) -> JsonMap:
    tests = definition.get("verification", {}).get("tests", [])
    required_vectors = definition.get("verification", {}).get("required_vectors", [])
    split_tests = package.get("layers", {}).get("tests", {})
    return {
        "schema": "db.component.generated.tests",
        "version": 1,
        "part": definition.get("part", ""),
        "tests": [
            {
                "type": test_type,
                "source": f"tests/{test_type}.json",
                "present": split_tests.get(test_type) is not None if isinstance(split_tests, dict) else False,
            }
            for test_type in tests
            if isinstance(test_type, str)
        ],
        "required_vectors": list(required_vectors) if isinstance(required_vectors, list) else [],
    }


def _documentation_data(definition: JsonMap, buses: JsonMap) -> JsonMap:
    controls = [
        {"pin": pin.get("name"), "function": pin.get("function", "control"), "active_low": pin.get("active_low", False)}
        for pin in definition.get("pins", [])
        if isinstance(pin, dict) and pin.get("function")
    ]
    return {
        "schema": "db.component.generated.documentation",
        "version": 1,
        "part": definition.get("part", ""),
        "title": definition.get("metadata", {}).get("title", definition.get("part", "")),
        "summary": f"{definition.get('metadata', {}).get('title', definition.get('part', 'Component'))}.",
        "sections": ["overview", "pins", "controls", "truth_table", "timing", "try_it"],
        "pin_count": definition.get("package", {}).get("pins"),
        "buses": buses,
        "controls": controls,
    }


def _interactive_demo_data(definition: JsonMap, buses: JsonMap) -> JsonMap:
    pins = list(definition.get("pins", [])) if isinstance(definition.get("pins"), list) else []
    controls = [
        str(pin.get("name"))
        for pin in pins
        if isinstance(pin, dict) and pin.get("direction") == "input" and pin.get("name")
    ]
    probes = sorted(buses) or [
        str(pin.get("name"))
        for pin in pins
        if isinstance(pin, dict) and pin.get("direction") in {"output", "bidirectional"} and pin.get("name")
    ][:8]
    return {
        "schema": "db.component.generated.interactive_demo",
        "version": 1,
        "part": definition.get("part", ""),
        "controls": controls,
        "probes": probes,
        "default_steps": ["apply controls", "settle", "probe"],
    }


def _digital_manifest_mismatches(definition: JsonMap, part: str, path: str) -> list[JsonMap]:
    try:
        manifest = load_component(part)
    except KeyError:
        return [_issue("digital_manifest_missing", part, path, f"chip manifest not found for {part}")]

    errors: list[JsonMap] = []
    metadata = definition.get("metadata", {})
    package = definition.get("package", {})
    generation = definition.get("generation", {})
    digital_pins = definition.get("pins", [])
    manifest_pins = manifest.get("pins", [])

    if isinstance(metadata, dict):
        for key in ("title", "family", "group"):
            expected = manifest.get(key)
            actual = metadata.get(key)
            if expected is not None and actual != expected:
                errors.append(_issue(
                    "digital_manifest_metadata_mismatch",
                    part,
                    path,
                    f"metadata.{key}={actual!r} does not match manifest {expected!r}",
                ))

    if isinstance(package, dict):
        manifest_package = manifest.get("package", {})
        if isinstance(manifest_package, dict):
            for key in ("kind", "pins"):
                expected = manifest_package.get(key)
                actual = package.get(key)
                if expected is not None and actual != expected:
                    errors.append(_issue(
                        "digital_manifest_package_mismatch",
                        part,
                        path,
                        f"package.{key}={actual!r} does not match manifest {expected!r}",
                    ))

    if isinstance(digital_pins, list) and isinstance(manifest_pins, list):
        digital_by_number = {
            pin["number"]: pin
            for pin in digital_pins
            if isinstance(pin, dict) and isinstance(pin.get("number"), int)
        }
        manifest_by_number = {
            pin["number"]: pin
            for pin in manifest_pins
            if isinstance(pin, dict) and isinstance(pin.get("number"), int)
        }
        for number in sorted(set(digital_by_number) | set(manifest_by_number)):
            digital_pin = digital_by_number.get(number)
            manifest_pin = manifest_by_number.get(number)
            if digital_pin is None:
                errors.append(_issue("digital_manifest_pin_missing", part, path, f"pin {number} is missing from digital definition"))
                continue
            if manifest_pin is None:
                errors.append(_issue("digital_manifest_pin_extra", part, path, f"pin {number} is not present in chip manifest"))
                continue
            for key in ("name", "direction", "active_low"):
                if key not in manifest_pin:
                    continue
                if digital_pin.get(key) != manifest_pin.get(key):
                    errors.append(_issue(
                        "digital_manifest_pin_mismatch",
                        part,
                        path,
                        f"pin {number} {key}={digital_pin.get(key)!r} does not match manifest {manifest_pin.get(key)!r}",
                    ))

    if isinstance(generation, dict):
        python = generation.get("python", {})
        manifest_python = manifest.get("python", {})
        if isinstance(python, dict) and isinstance(manifest_python, dict):
            for key in ("factory", "part"):
                expected = manifest_python.get(key)
                actual = python.get(key)
                if expected is not None and actual != expected:
                    errors.append(_issue(
                        "digital_manifest_python_mismatch",
                        part,
                        path,
                        f"generation.python.{key}={actual!r} does not match manifest {expected!r}",
                    ))
        verilog = generation.get("verilog", {})
        manifest_verilog = manifest.get("verilog", {})
        if isinstance(verilog, dict) and isinstance(manifest_verilog, dict):
            for key in ("module", "file"):
                expected = manifest_verilog.get(key)
                actual = verilog.get(key)
                if expected is not None and actual != expected:
                    errors.append(_issue(
                        "digital_manifest_verilog_mismatch",
                        part,
                        path,
                        f"generation.verilog.{key}={actual!r} does not match manifest {expected!r}",
                    ))

    digital_pin_numbers = {
        pin["number"]
        for pin in digital_pins
        if isinstance(pin, dict) and isinstance(pin.get("number"), int)
    } if isinstance(digital_pins, list) else set()
    verilog = manifest.get("verilog", {})
    export = verilog.get("export", {}) if isinstance(verilog, dict) else {}
    export_pins: set[int] = set()
    internal_placeholder_pins: set[int] = set()
    if isinstance(export, dict):
        for port in export.get("ports", []):
            if not isinstance(port, dict):
                continue
            port_pins = [pin for pin in port.get("pins", []) if isinstance(pin, int)]
            export_pins.update(port_pins)
            note = str(port.get("note", "")).lower()
            if "internal" in note and "placeholder" in note:
                internal_placeholder_pins.update(pin for pin in port_pins if pin == 0)
        export_pins.update(pin for pin in export.get("output_pins", []) if isinstance(pin, int))
    for number in sorted((export_pins - internal_placeholder_pins) - digital_pin_numbers):
        errors.append(_issue(
            "digital_manifest_export_pin_missing",
            part,
            path,
            f"verilog export references pin {number}, which is missing from digital definition",
        ))

    return errors


def _pinout_mismatches(manifest: JsonMap) -> list[JsonMap]:
    verilog = manifest.get("verilog", {})
    if not isinstance(verilog, dict) or not isinstance(verilog.get("file"), str):
        return []
    model_path = ROOT / str(verilog["file"])
    if not model_path.exists():
        return []
    pinout = _embedded_pinout_pins(model_path)
    if not pinout:
        return []
    manifest_pins = {
        int(pin["number"]): str(pin["name"])
        for pin in manifest.get("pins", [])
        if isinstance(pin, dict) and isinstance(pin.get("number"), int) and isinstance(pin.get("name"), str)
    }
    mismatches: list[JsonMap] = []
    for number in sorted(set(pinout) | set(manifest_pins)):
        pinout_name = pinout.get(number)
        manifest_name = manifest_pins.get(number)
        if pinout_name is None:
            mismatches.append({
                "code": "pinout_extra_manifest_pin",
                "message": f"pin {number} exists in DB as {manifest_name!r} but not embedded pinout",
            })
        elif manifest_name is None:
            mismatches.append({
                "code": "pinout_missing_manifest_pin",
                "message": f"pin {number} exists in embedded pinout as {pinout_name!r} but not DB",
            })
        elif pinout_name != manifest_name:
            mismatches.append({
                "code": "pinout_name_mismatch",
                "message": f"pin {number} embedded pinout={pinout_name!r} DB={manifest_name!r}",
            })
    return mismatches


def _embedded_pinout_pins(path: Path) -> dict[int, str]:
    pins: dict[int, str] = {}
    inside = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "// Embedded pinout documentation.":
            inside = True
            continue
        if not inside:
            continue
        if not line.startswith("//"):
            break
        text = line[2:].strip()
        match = re.match(r"\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|", text)
        if match:
            pins[int(match.group(1))] = match.group(2).strip()
    return pins


def _legacy_74hc_models() -> list[str]:
    return [path.stem.upper() for path in (ROOT / "Verilog" / "74xx").glob("*.v")]


def _legacy_memory_models() -> list[str]:
    return [_memory_part_id(path.stem) for path in (ROOT / "Verilog" / "Memory").glob("*.v")]


def _legacy_74hc_pinouts() -> list[str]:
    return [
        path.stem.upper()
        for path in (ROOT / "Verilog" / "74xx").glob("*.v")
        if "Embedded pinout documentation" in path.read_text(encoding="utf-8")
    ]


def _legacy_memory_pinouts() -> list[str]:
    return [
        _memory_part_id(path.stem)
        for path in (ROOT / "Verilog" / "Memory").glob("*.v")
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
        "severity": "error" if code.startswith(("missing_", "pin_count", "duplicate", "invalid", "verilog_module", "export_status", "pinout_", "chip_status_exclusion", "chip_status_excluded")) else "warning",
        "part": part,
        "location": location,
        "message": message,
    }
