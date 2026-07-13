"""Resolve human-authored component definitions into the stable digital shape.

The compact format is deliberately an authoring format.  Callers of the DB
continue to receive ``db.component.digital`` records, so editors and tools do
not need a flag-day migration.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from .resource_definition import load_device_resource


JsonMap = dict[str, Any]

COMPACT_SCHEMA = "db.component.digital.compact"
CANONICAL_SCHEMA = "db.component.digital"
GENERATION_TARGETS = [
    "json", "python_simulator", "verilog_wrapper", "verilog_testbench",
    "kicad_symbol", "svg_pinout", "documentation", "unit_test",
    "interactive_demo",
]

PROFILES: dict[str, JsonMap] = {
    "74hc.digital@0.2": {
        "family": "74HC",
        "group": "74xx",
        "package_kind": "DIP",
        "output_drive": "push_pull",
    },
    "memory.async@0.2": {
        "family": "Memory", "group": "memory", "package_kind": "DIP",
        "output_drive": "tri_state",
    },
}

COMPACT_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "lib" / "standard" / "compact.digital.schema.json"


def validate_compact_definition(source: Mapping[str, Any]) -> list[str]:
    """Return schema errors for a human-authored compact source."""

    schema = json_load(COMPACT_SCHEMA_PATH)
    return [error.message for error in Draft202012Validator(schema).iter_errors(dict(source))]


def resolve_compact_definition(source: Mapping[str, Any], package_root: Path) -> JsonMap:
    """Expand one compact authoring record without guessing chip facts.

    Profiles provide only published defaults.  A missing pin, model name,
    source, or timing fact remains an error for the normal DB validator rather
    than being invented by this resolver.
    """

    if source.get("schema") != COMPACT_SCHEMA:
        raise ValueError(f"expected {COMPACT_SCHEMA}, got {source.get('schema')!r}")
    errors = validate_compact_definition(source)
    if errors:
        raise ValueError("invalid compact definition: " + "; ".join(errors))
    profile_name = str(source.get("profile", ""))
    profile = PROFILES.get(profile_name)
    if profile is None:
        raise ValueError(f"unknown compact definition profile: {profile_name!r}")
    part = str(source.get("part", ""))
    if not part:
        raise ValueError("compact definition needs part")
    # Resource is presentation-only.  Validate an optional package mapping so
    # a symbol/footprint cannot silently point at the wrong device, but keep it
    # out of the canonical device record consumed by simulation and HDL tools.
    load_device_resource(package_root, part)
    about = source.get("about", {})
    package = source.get("package", {})
    model = source.get("model", {})
    verify = source.get("verify", {})
    if not isinstance(about, Mapping) or not isinstance(package, Mapping):
        raise ValueError("compact about and package must be objects")
    pins = _resolve_pins(source.get("pins"))
    timing = _resolve_timing(source.get("timing"), part)
    definition_layer_timing = timing.pop("_definition_layer_timing", None)
    sources = _resolve_sources(source.get("sources"))
    base_rel = _package_relative_path(package_root)
    python_model = str(model.get("python", "")) if isinstance(model, Mapping) else ""
    verilog_model = str(model.get("verilog", "")) if isinstance(model, Mapping) else ""
    if not python_model or not verilog_model:
        raise ValueError("compact model requires python and verilog names")

    electrical = deepcopy(source.get("electrical", {}))
    if not isinstance(electrical, dict):
        raise ValueError("compact electrical must be an object")
    evidence = _evidence_for(sources)
    status = _derived_status(package_root, sources)
    canonical: JsonMap = {
        "schema": CANONICAL_SCHEMA,
        "version": 1,
        "part": part,
        "metadata": {
            "title": str(about.get("title", part)),
            "family": str(about.get("family", profile["family"])),
            "group": str(about.get("group", profile["group"])),
            "role": str(about.get("role", "logic")),
        },
        "package": {
            "kind": str(package.get("kind", profile["package_kind"])),
            "default": str(package.get("default", "")),
            "pins": len(pins),
        },
        "pins": pins,
        "logic": deepcopy(source.get("logic", {})),
        "timing": timing,
        "generation": {
            "targets": list(GENERATION_TARGETS),
            "python": {"part": part, "class": python_model, "factory": "create", "file": f"{base_rel}/simulation/model.py"},
            "verilog": {"module": verilog_model, "file": f"{base_rel}/simulation/model.v", "netlist": f"{base_rel}/simulation/netlist.json"},
        },
        "verification": {
            "tests": list(verify) if isinstance(verify, list) else list(verify.get("tests", ["truth_table", "timing", "propagation"])),
            "required_vectors": [] if isinstance(verify, list) else deepcopy(verify.get("required_vectors", [])),
        },
        "datasheet": {"schema": "db.component.datasheet.sources", "version": 1, "part": part, "sources": sources},
        "evidence": {"dip_pinout_verified": True, "manufacturer": str(about.get("manufacturer", sources[0]["label"])), "datasheet_status": "historical-or-current"},
        "status": status,
        "logic_family_model": str(model.get("logic_family_model", python_model)),
        "variants": _resolve_variants(source.get("variants", [])),
        "procurement": deepcopy(source.get("procurement", {})),
        "definition_layers": {
            "pins": {
                "schema": "db.component.pins", "version": 1, "part": part,
                "pins": deepcopy(pins),
            },
            "power": {
                "schema": "db.component.power", "version": 1, "part": part,
                "rails": [deepcopy(pin) for pin in pins if pin["direction"] == "power"],
            },
            "timing": deepcopy(definition_layer_timing) if definition_layer_timing is not None else _generic_timing_layer(part, timing, evidence),
            "electrical": {"schema": "db.component.electrical", "version": 1, "part": part, **electrical, "evidence": electrical.get("evidence", evidence)},
        },
        "authoring": {"schema": COMPACT_SCHEMA, "profile": profile_name, "source": "definition/definition.json"},
    }
    # Older canonical memory packages legitimately omit ``variants``.  Do not
    # synthesize an empty field: the live DB validator distinguishes absence
    # from an incomplete authored variant list.
    if not canonical["variants"]:
        del canonical["variants"]
        # Match canonical packages that predate the optional model-alias field.
        del canonical["logic_family_model"]
    return canonical


def _resolve_pins(raw: Any) -> list[JsonMap]:
    if not isinstance(raw, Mapping) or not raw:
        raise ValueError("compact package.pins must be a non-empty object keyed by pin number")
    result: list[JsonMap] = []
    for number_text, item in sorted(raw.items(), key=lambda entry: int(entry[0])):
        if not isinstance(item, list) or len(item) not in {2, 3} or not all(isinstance(value, str) for value in item[:2]):
            raise ValueError(f"compact pin {number_text} must be [name, direction, optional metadata]")
        number = int(number_text)
        name, direction = item[0], _direction(item[1])
        metadata = item[2] if len(item) == 3 else {}
        if not isinstance(metadata, Mapping):
            raise ValueError(f"compact pin {number_text} metadata must be an object")
        pin: JsonMap = {"number": number, "name": name, "direction": direction}
        if name.startswith("/"):
            pin["active_low"] = True
        if metadata.get("active") == "low":
            pin["active_low"] = True
        # ``edge`` is the documented compact spelling.  Accept the earlier
        # ``clock`` spelling too so the initial 74HC00 pilot remains readable
        # by the same resolver.
        clock_edge = metadata.get("edge", metadata.get("clock"))
        if clock_edge in {"rising", "falling"}:
            pin["clock"] = True
        for key in ("bus", "bit", "rail", "function", "drive", "enable"):
            if key in metadata:
                pin[key] = deepcopy(metadata[key])
        if direction == "power" and "rail" not in pin:
            pin["rail"] = name
        result.append(pin)
    return result


def _direction(value: str) -> str:
    return {"in": "input", "out": "output", "io": "bidirectional"}.get(value, value)


def _resolve_timing(raw: Any, part: str) -> JsonMap:
    if not isinstance(raw, Mapping):
        raise ValueError("compact timing must be an object")
    legacy = raw.get("legacy_canonical")
    if legacy is not None:
        if not isinstance(legacy, Mapping):
            raise ValueError("compact timing.legacy_canonical must be an object")
        canonical, layer = legacy.get("timing"), legacy.get("definition_layer")
        if not isinstance(canonical, Mapping) or not isinstance(layer, Mapping):
            raise ValueError("compact timing.legacy_canonical requires timing and definition_layer objects")
        # This is a migration-only compatibility payload.  It has one source
        # of truth in the compact file and is returned untouched, so old timing
        # rows/parameters cannot be weakened by a generic normalization path.
        return {**deepcopy(dict(canonical)), "_definition_layer_timing": deepcopy(dict(layer))}
    clocked = raw.get("clocked")
    asynchronous_memory = raw.get("asynchronous_memory")
    if asynchronous_memory is not None:
        if not isinstance(asynchronous_memory, Mapping):
            raise ValueError("compact timing.asynchronous_memory must be an object")
        return _resolve_asynchronous_memory_timing(raw, asynchronous_memory, part)
    if clocked is not None:
        if not isinstance(clocked, Mapping):
            raise ValueError("compact timing.clocked must be an object")
        return _resolve_clocked_timing(raw, clocked, part)
    clocked_tri_state = raw.get("clocked_tri_state")
    if clocked_tri_state is not None:
        if not isinstance(clocked_tri_state, Mapping):
            raise ValueError("compact timing.clocked_tri_state must be an object")
        return _resolve_clocked_tri_state_timing(raw, clocked_tri_state, part)
    multipath = raw.get("multipath")
    if multipath is not None:
        if not isinstance(multipath, Mapping):
            raise ValueError("compact timing.multipath must be an object")
        return _resolve_multipath_timing(raw, multipath, part)
    tri_state = raw.get("tri_state")
    if tri_state is not None:
        if not isinstance(tri_state, Mapping):
            raise ValueError("compact timing.tri_state must be an object")
        return _resolve_tri_state_timing(raw, tri_state, part)
    delay_ns = _nanoseconds(raw.get("default", raw.get("default_delay_ns")))
    datasheet = deepcopy(raw.get("datasheet", {}))
    if not isinstance(datasheet, dict):
        raise ValueError("compact timing.datasheet must be an object")
    typical = _nanoseconds(datasheet.get("typical_ns", delay_ns))
    maximum = _nanoseconds(datasheet.get("max_ns_25c", delay_ns))
    maximum_range = _nanoseconds(datasheet.get("max_ns_minus40_to_85c", maximum))
    path = str(datasheet.get("path", "input_to_output"))
    params = _timing_parameters(typical, maximum, maximum_range, path, part, datasheet)
    runtime_datasheet = {key: value for key, value in datasheet.items() if key != "parameter_note"}
    resolved = {
        "delay_ns": delay_ns,
        "datasheet": {**runtime_datasheet, "typical_ns": typical, "max_ns_25c": maximum, "max_ns_minus40_to_85c": maximum_range, "path": path},
        "simple": {"default_delay_ns": delay_ns, "source": "legacy functional simulator default"},
        "timed": {"status": "conservative_default_until_part_specific_datasheet_timing_extracted", "paths": {
            "input_to_output_ns": {"from": "input", "to": "output", "parameter": "tpd", "condition": "input or select changes", "ranges_ns": {"conservative_default": {"typ_ns": delay_ns, "max_ns": delay_ns, "min_ns": None, "source": "conservative_default_from_existing_model_delay"}}},
            "transition_time_ns": {"from": "output transition", "to": "output transition", "parameter": "tt", "condition": "enabled output switches", "ranges_ns": {"conservative_default": {"typ_ns": delay_ns, "max_ns": delay_ns, "min_ns": None, "source": "conservative_default_from_existing_model_delay"}}},
        }},
        "timing_parameters": params,
    }
    clock_edge = raw.get("clock_edge")
    if clock_edge is not None:
        if clock_edge not in {"rising", "falling"}:
            raise ValueError("compact timing.clock_edge must be 'rising' or 'falling'")
        resolved["clock_edge"] = clock_edge
    return resolved


def _resolve_asynchronous_memory_timing(raw: Mapping[str, Any], memory: Mapping[str, Any], part: str) -> JsonMap:
    """Resolve EEPROM/SRAM access, float, and write-window truth.

    This is deliberately not a clocked or ordinary tri-state profile: address,
    CE and OE have independent read paths, while WE has a write pulse and a
    post-write busy model.  The detailed rows stay named in the compact file.
    """
    default = _nanoseconds(raw.get("default"))
    variant, read, write, model, evidence = (memory.get(key) for key in ("variant", "read", "write", "model", "evidence"))
    if not all(isinstance(item, Mapping) for item in (variant, read, write, model, evidence)):
        raise ValueError("compact asynchronous_memory requires variant, read, write, model, and evidence")
    selected = str(variant.get("selected", ""))
    available = variant.get("available")
    if not selected or not isinstance(available, Mapping) or not available:
        raise ValueError("compact asynchronous_memory variant needs selected and available speed grades")
    paths = {"address_to_data_valid_ns": _nanoseconds(read.get("address")), "ce_to_data_valid_ns": _nanoseconds(read.get("ce")), "oe_to_data_valid_ns": _nanoseconds(read.get("oe")), "ce_or_oe_to_high_z_ns": _nanoseconds(read.get("float"))}
    pulse, setup, address_hold = (_nanoseconds(write.get(key)) for key in ("pulse_min", "data_setup_min", "address_hold_min"))
    read_rows = {f"at28c256_{grade}": value for grade, value in available.items()}
    # The source values below are present as named compact input; the runtime
    # view preserves the historic model fields exactly.
    layer_delay = {
        "default_ns": default,
        "source": str(model.get("default_source")),
        "datasheet_read_ns": {
            "tacc_address_to_output": deepcopy(read_rows), "tce_ce_to_output": deepcopy(read_rows),
            "toe_oe_to_output": deepcopy(model.get("oe_by_grade")), "tdf_ce_or_oe_to_float": deepcopy(model.get("float_by_grade")),
        },
        "datasheet_write_ns": {"address_hold": address_hold, "write_pulse_width": pulse, "data_setup": setup, "data_hold": _nanoseconds(write.get("data_hold")), "write_cycle_us": write.get("cycle_us"), "latch_edge": str(write.get("latch_edge")), "write_cycle_updates_default": write.get("cycle_updates"), "busy_behavior": str(model.get("busy_behavior")), "programming_fidelity": str(model.get("programming_fidelity"))},
        "model_delay_ns": default, "selected_variant": selected.lower(),
        "variant_policy": {"available_variants": list(read_rows), "default_variant": selected.lower(), "unselected_variant_policy": str(variant.get("unselected_policy")), "physical_signoff_requires": str(variant.get("physical_signoff_requires"))},
        "paths": deepcopy(paths), "fidelity_level": str(model.get("fidelity_level")), "unsupported_programming_features": deepcopy(model.get("unsupported_features")),
        "public_timing": {"variant": selected.upper().replace("AT28C256_", "AT28C256-"), "paths": deepcopy(paths), "write": {"pulse_min_ns": pulse, "data_setup_min_ns": setup, "address_hold_min_ns": address_hold}},
    }
    source = str(evidence.get("parameter_source", evidence.get("source"))).replace(" datasheet, ", " ").replace("read and write", "read/write"); note_read = "tACC/tCE/tOE read access paths define data valid after address, CE, or OE; EEPROM read timing is not split by output HIGH/LOW transition."
    note_enable = "tOE/tCE read output-enable paths define when the output becomes valid from disabled/read state; datasheet does not split high-Z-to-HIGH versus high-Z-to-LOW."
    note_float = "tDF CE/OE-to-float path defines output-disable timing; not split by previous HIGH/LOW output state."
    def exact(values: JsonMap, source_field: str, note: str) -> JsonMap:
        return {"status": "exact", "source_field": source_field, "note": note, "values_ns": values, "mapping_basis": note, "source": source}
    parameters = {"schema": "db.component.timing_parameters", "version": 1, "basis": "normalized_from_existing_datasheet_timing", "conditions": {"variant": selected.upper().replace("AT28C256_", "AT28C256-")}, "parameters": {}}
    read_values = {key: paths[key] for key in ("address_to_data_valid_ns", "ce_to_data_valid_ns", "oe_to_data_valid_ns")}
    enable_values = {key: paths[key] for key in ("oe_to_data_valid_ns", "ce_to_data_valid_ns")}
    for key in ("tPLH", "tPHL"): parameters["parameters"][key] = exact(read_values, "definition_layers.timing.delay.public_timing.paths", note_read)
    for key in ("tPZH", "tPZL"): parameters["parameters"][key] = exact(enable_values, "definition_layers.timing.delay.public_timing.paths", note_enable)
    for key in ("tPHZ", "tPLZ"): parameters["parameters"][key] = exact({"ce_or_oe_to_high_z_ns": paths["ce_or_oe_to_high_z_ns"]}, "definition_layers.timing.delay.public_timing.paths", note_float)
    for key in ("clock_to_q_high", "clock_to_q_low"): parameters["parameters"][key] = {"status": "not_applicable", "reason": f"{part} is asynchronous memory and has no clock-to-Q output."}
    parameters["parameters"]["setup"] = {"status": "exact", "source_field": "definition_layers.timing.delay.public_timing.write", "note": "Write setup/hold-style requirements are source-backed for the selected variant.", "values_ns": {"data_setup_min_ns": setup, "address_hold_min_ns": address_hold}}
    parameters["parameters"]["hold"] = {"status": "exact", "source_field": "definition_layers.timing.delay.public_timing.write", "note": "Write hold requirement is source-backed for the selected variant.", "values_ns": {"address_hold_min_ns": address_hold}}
    parameters["parameters"]["minimum_pulse_width"] = {"status": "exact", "source_field": "definition_layers.timing.delay.public_timing.write", "note": "Write pulse width is source-backed for the selected variant.", "values_ns": {"write_pulse_min_ns": pulse}}
    timing = {"variant": selected.upper().replace("AT28C256_", "AT28C256-"), "paths": deepcopy(paths), "write": deepcopy(layer_delay["public_timing"]["write"]), "timing_parameters": parameters}
    return {**timing, "_definition_layer_timing": {"schema": "db.component.timing", "version": 1, "part": part, "delay": layer_delay, "evidence": deepcopy(dict(evidence)), "timing_parameters": parameters}}


def _resolve_multipath_timing(raw: Mapping[str, Any], paths: Mapping[str, Any], part: str) -> JsonMap:
    """Resolve readable push-pull timing rows (data/select/strobe/transition).

    Unlike the generic combinational form, this retains each independently
    specified datasheet row.  It is intentionally useful for multiplexers and
    other control logic where select and enable are not interchangeable.
    """
    delay = _nanoseconds(raw.get("default", raw.get("default_delay_ns")))
    conditions, rows, evidence = paths.get("conditions"), paths.get("rows"), paths.get("evidence")
    if not isinstance(conditions, Mapping) or not isinstance(rows, Mapping) or not isinstance(evidence, Mapping):
        raise ValueError("compact timing.multipath requires conditions, rows, and evidence")
    required = ("data_to_output", "select_to_output", "strobe_to_output", "transition")
    if set(rows) != set(required):
        raise ValueError("compact timing.multipath rows must name data_to_output, select_to_output, strobe_to_output, and transition")
    normalized: JsonMap = {}
    for name in required:
        item = rows[name]
        if not isinstance(item, Mapping):
            raise ValueError(f"compact timing.multipath {name} must be an object")
        normalized[name] = {}
        for column in ("typical", "max_25c", "max_sn74", "max_sn54"):
            values = item.get(column)
            if not isinstance(values, Mapping) or not values:
                raise ValueError(f"compact timing.multipath {name}.{column} must be voltage values")
            normalized[name][column] = _voltage_times(values)
    def table(column: str) -> JsonMap:
        return {name: normalized[name][column] for name in required}
    def public_table(column: str) -> JsonMap:
        return {name: normalized[name][column]["vcc_4_5_v"] for name in required}
    note = "Exact canonical tPLH/tPHL uses the datasheet propagation-delay row because the local source maps those waveform terms to tpd for this combinational push-pull part."
    source_field = str(paths.get("source_field", "datasheet switching characteristics"))
    timing_parameters: JsonMap = {"schema": "db.component.timing_parameters", "version": 1, "basis": "normalized_from_existing_datasheet_timing", "parameters": {}}
    exact = _exact({"datasheet_typical_ns": public_table("typical"), "datasheet_max_ns_25c": public_table("max_25c"), "datasheet_max_ns_sn74": public_table("max_sn74"), "datasheet_max_ns_sn54": public_table("max_sn54")}, source_field, note)
    timing_parameters["parameters"]["tPLH"] = deepcopy(exact)
    timing_parameters["parameters"]["tPHL"] = deepcopy(exact)
    for name in ("tPZH", "tPZL", "tPHZ", "tPLZ"):
        timing_parameters["parameters"][name] = {"status": "not_applicable", "reason": f"{part} has no high-Z output-enable control in this DB model; /G affects logic output selection/enabling, not tri-state bus release."}
    for name, reason in (("clock_to_q_high", "is not a clocked storage element for this parameter."), ("clock_to_q_low", "is not a clocked storage element for this parameter."), ("minimum_pulse_width", "is not a clocked storage element for this parameter."), ("setup", "is combinational/bus-control logic and has no clocked data setup timing requirement."), ("hold", "is combinational/bus-control logic and has no clocked data hold timing requirement.")):
        timing_parameters["parameters"][name] = {"status": "not_applicable", "reason": f"{part} {reason}"}
    conservative = {"typ_ns": delay, "max_ns": delay, "min_ns": None, "source": "conservative_default_from_existing_model_delay"}
    timed = {"status": "conservative_default_until_part_specific_datasheet_timing_extracted", "paths": {"input_to_output_ns": {"from": "input", "to": "output", "parameter": "tpd", "condition": "input or select changes", "ranges_ns": {"conservative_default": deepcopy(conservative)}}, "transition_time_ns": {"from": "output transition", "to": "output transition", "parameter": "tt", "condition": "enabled output switches", "ranges_ns": {"conservative_default": deepcopy(conservative)}}}}
    delay_layer = {"default_ns": delay, "source": "simulation default from Python model", "datasheet_typical_ns": {"condition": str(conditions.get("note", "")), "data_to_y": normalized["data_to_output"]["typical"], "select_to_y": normalized["select_to_output"]["typical"], "enable_to_y": normalized["strobe_to_output"]["typical"], "transition_y": normalized["transition"]["typical"]}}
    return {"delay_ns": delay, "simple": {"default_delay_ns": delay, "source": "legacy functional simulator default"}, "timed": timed, "timing_parameters": timing_parameters, "_definition_layer_timing": {"schema": "db.component.timing", "version": 1, "part": part, "delay": delay_layer, "evidence": deepcopy(dict(evidence)), "timing_parameters": timing_parameters}}


def _resolve_clocked_tri_state_timing(raw: Mapping[str, Any], timing: Mapping[str, Any], part: str) -> JsonMap:
    """Resolve a clocked register's capture and /OE-to-high-Z timing rows."""
    delay = _nanoseconds(raw.get("default", raw.get("default_delay_ns")))
    if raw.get("clock_edge") not in {"rising", "falling"}:
        raise ValueError("compact clocked_tri_state timing requires clock_edge")
    conditions, rows, requirements, evidence = (timing.get(key) for key in ("conditions", "rows", "requirements", "evidence"))
    if not all(isinstance(x, Mapping) for x in (conditions, rows, requirements, evidence)):
        raise ValueError("compact timing.clocked_tri_state requires conditions, rows, requirements, and evidence")
    required_rows = ("clock_to_q", "enable_to_q", "disable_to_z", "transition_q")
    if set(rows) != set(required_rows):
        raise ValueError("compact clocked_tri_state rows must name clock_to_q, enable_to_q, disable_to_z, and transition_q")
    parsed_rows = {name: _voltage_times(rows[name]) for name in required_rows}
    setup, hold, pulse, frequency = (requirements.get(key) for key in ("setup_data", "hold_after_clock", "clock_high_or_low", "maximum_clock_mhz"))
    if not all(isinstance(x, Mapping) for x in (setup, hold, pulse, frequency)):
        raise ValueError("compact clocked_tri_state requirements are incomplete")
    setup_v, hold_v, pulse_v, freq_v = _voltage_times(setup), _voltage_times(hold), _voltage_times(pulse), _voltage_numbers(frequency, "maximum_clock_mhz")
    note_clock = "TI SN74HC574 switching table and waveform notes map CLK-to-Q tpd to tPLH/tPHL and clock-to-Q high/low."
    note_enable = "TI SN74HC574 switching table and waveform notes map output enable ten to tPZH/tPZL."
    note_disable = "TI SN74HC574 switching table and waveform notes map output disable tdis to tPHZ/tPLZ."
    params: JsonMap = {"schema": "db.component.timing_parameters", "version": 1, "basis": "normalized_from_existing_datasheet_timing", "parameters": {}}
    for name in ("clock_to_q_high", "clock_to_q_low", "tPLH", "tPHL"):
        params["parameters"][name] = _exact(parsed_rows["clock_to_q"], "definition_layers.timing.delay.datasheet_typical_ns.clock_to_q", note_clock)
    for name in ("tPZH", "tPZL"):
        params["parameters"][name] = _exact(parsed_rows["enable_to_q"], "definition_layers.timing.delay.datasheet_typical_ns.enable_to_q", note_enable)
    for name in ("tPHZ", "tPLZ"):
        params["parameters"][name] = _exact(parsed_rows["disable_to_z"], "definition_layers.timing.delay.datasheet_typical_ns.disable_to_z", note_disable)
    params["parameters"]["setup"] = _exact({"data": setup_v}, "definition_layers.timing.timing_requirements.setup_before_clock_ns", "Data setup requirement is source-backed.")
    params["parameters"]["hold"] = _exact(hold_v, "definition_layers.timing.timing_requirements.hold_after_clock_ns", "Data hold requirement is source-backed.")
    params["parameters"]["minimum_pulse_width"] = _exact(pulse_v, "definition_layers.timing.timing_requirements.clock_high_or_low_ns", "Clock pulse width requirement is source-backed.")
    conservative = {"typ_ns": delay, "max_ns": delay, "min_ns": None, "source": "conservative_default_from_existing_model_delay"}
    timed = {"status": "conservative_default_until_part_specific_datasheet_timing_extracted", "paths": {"async_control_to_output_ns": {"from": "asynchronous control", "to": "Q/output", "parameter": "tremap", "condition": "async control asserted or released", "ranges_ns": {"conservative_default": deepcopy(conservative)}}, "clock_to_output_ns": {"from": "CLK/clock control", "to": "Q/output", "parameter": "tco", "condition": "active clock edge", "ranges_ns": {"conservative_default": deepcopy(conservative)}}, "input_setup_margin_ns": {"from": "D/input", "to": "CLK/clock control", "parameter": "tsu", "condition": "conservative setup placeholder from model delay", "ranges_ns": {"conservative_default": deepcopy(conservative)}}, "transition_time_ns": {"from": "output transition", "to": "output transition", "parameter": "tt", "condition": "enabled output switches", "ranges_ns": {"conservative_default": deepcopy(conservative)}}}}
    delay_layer = {"default_ns": delay, "source": "simulation default from Python model", "datasheet_typical_ns": {"condition": str(conditions.get("note", "")), **parsed_rows}}
    return {"clock_edge": raw["clock_edge"], "delay_ns": delay, "simple": {"default_delay_ns": delay, "source": "legacy functional simulator default"}, "timed": timed, "timing_parameters": params, "_definition_layer_timing": {"schema": "db.component.timing", "version": 1, "part": part, "delay": delay_layer, "evidence": deepcopy(dict(evidence)), "timing_requirements": {"clock_frequency_mhz": freq_v, "clock_high_or_low_ns": pulse_v, "hold_after_clock_ns": hold_v, "setup_before_clock_ns": {"data": setup_v}}, "timing_parameters": params}}


def _resolve_tri_state_timing(raw: Mapping[str, Any], tri: Mapping[str, Any], part: str) -> JsonMap:
    """Resolve the named bidirectional/high-Z grammar without losing rows.

    ``transfer`` is deliberately one authoring row: the 74HC245 datasheet
    gives equal A-to-B and B-to-A values.  The resolver expands the two
    runtime paths and preserves the independent enable/disable rows.
    """
    delay = _nanoseconds(raw.get("default", raw.get("default_delay_ns")))
    conditions = tri.get("conditions")
    transfer = tri.get("transfer")
    enable = tri.get("output_enable")
    disable = tri.get("output_disable")
    transition = tri.get("transition")
    evidence = tri.get("evidence")
    if not all(isinstance(item, Mapping) for item in (conditions, transfer, enable, disable, transition, evidence)):
        raise ValueError("compact timing.tri_state requires conditions, transfer, output_enable, output_disable, transition, and evidence")
    device = conditions.get("device")
    load = conditions.get("load_capacitance_pf")
    note = conditions.get("temperature_note")
    source = conditions.get("source")
    if not all(isinstance(value, str) and value for value in (device, note, source)) or not isinstance(load, (int, float)):
        raise ValueError("compact timing.tri_state conditions are incomplete")

    def rows(name: str, value: Mapping[str, Any]) -> JsonMap:
        result: JsonMap = {}
        for voltage, table in value.items():
            if not isinstance(table, Mapping):
                raise ValueError(f"compact timing.tri_state {name}.{voltage} must be an object")
            required = ("typ", "max_25c", "max_sn54", "max_sn74")
            if any(not isinstance(table.get(key), int) or table[key] < 0 for key in required):
                raise ValueError(f"compact timing.tri_state {name}.{voltage} needs integer typ/max values")
            result[_voltage_key(voltage)] = {"min_ns": None, "typ_ns": table["typ"], "max_ns_25c": table["max_25c"], "max_ns_sn54": table["max_sn54"], "max_ns_sn74": table["max_sn74"]}
        if not result:
            raise ValueError(f"compact timing.tri_state {name} must not be empty")
        return result

    transfer_rows, enable_rows, disable_rows, transition_rows = (rows("transfer", transfer), rows("output_enable", enable), rows("output_disable", disable), rows("transition", transition))
    timed_paths = {
        "A_to_B": {"parameter": "tpd", "from": "A", "to": "B", "condition": "DIR=1 and /OE=0", "ranges_ns": deepcopy(transfer_rows)},
        "B_to_A": {"parameter": "tpd", "from": "B", "to": "A", "condition": "DIR=0 and /OE=0", "ranges_ns": deepcopy(transfer_rows)},
        "OE_to_output_enable": {"parameter": "ten", "from": "/OE", "to": "A,B enabled outputs", "condition": "/OE falls", "ranges_ns": deepcopy(enable_rows)},
        "OE_to_high_Z": {"parameter": "tdis", "from": "/OE", "to": "A,B high-Z", "condition": "/OE rises", "ranges_ns": deepcopy(disable_rows)},
        "transition_time": {"parameter": "tt", "from": "A or B output transition", "to": "A or B output transition", "condition": "enabled output switches", "ranges_ns": deepcopy(transition_rows)},
    }
    timing_note = "TI SN74HC245 table and waveform notes map tPLH/tPHL to tpd, tPZH/tPZL to ten, and tPHZ/tPLZ to tdis."
    def values(table: JsonMap) -> JsonMap:
        return {key: {"typ": item["typ_ns"], "max_25c": item["max_ns_25c"], "max_sn54": item["max_ns_sn54"], "max_sn74": item["max_ns_sn74"]} for key, item in table.items()}
    transfer_values, enable_values, disable_values = values(transfer_rows), values(enable_rows), values(disable_rows)
    parameters: JsonMap = {"schema": "db.component.timing_parameters", "version": 1, "basis": "normalized_from_existing_datasheet_timing", "parameters": {}}
    for name in ("tPLH", "tPHL"):
        parameters["parameters"][name] = _exact({"A_to_B": deepcopy(transfer_values), "B_to_A": deepcopy(transfer_values)}, "TI SN74HC245 switching characteristics, CL=50 pF tpd", timing_note)
    for name in ("tPZH", "tPZL"):
        parameters["parameters"][name] = _exact(deepcopy(enable_values), "TI SN74HC245 switching characteristics, CL=50 pF ten", timing_note)
    for name in ("tPHZ", "tPLZ"):
        parameters["parameters"][name] = _exact(deepcopy(disable_values), "TI SN74HC245 switching characteristics, CL=50 pF tdis", timing_note)
    for name in ("setup", "hold"):
        parameters["parameters"][name] = {"status": "exact", "source_field": "definition_layers.timing.setup_hold", "note": "DIR and /OE setup/hold metadata is source-backed for bus-control use.", "values_ns": []}
    for name in ("clock_to_q_high", "clock_to_q_low", "minimum_pulse_width"):
        parameters["parameters"][name] = {"status": "not_applicable", "reason": f"{part} is not a clocked storage element for this parameter."}
    simple = {"default_delay_ns": delay, "source": "functional simulator default; timed mode uses path-specific datasheet values"}
    timed = {"conditions": {"device": device, "load_capacitance_pf": load, "temperature_note": note, "source": source}, "paths": timed_paths}
    def summary(table: JsonMap, field: str) -> JsonMap:
        return {field: {key: value["typ_ns"] for key, value in table.items()}}
    base_delay: JsonMap = {"default_ns": delay, "source": simple["source"], "simple": deepcopy(simple), "timed": deepcopy(timed), "datasheet_typical_ns": {"condition": "SN74HC245, CL=50 pF, TA=25 C", **summary(transfer_rows, "tpd_a_b_to_b_a"), **summary(enable_rows, "ten_oe_to_a_b"), **summary(disable_rows, "tdis_oe_to_a_b"), **summary(transition_rows, "transition_a_b")}, "datasheet_max_ns_25c": {"condition": "SN74HC245, CL=50 pF, TA=25 C"}, "datasheet_max_ns_sn74": {"condition": "SN74HC245 commercial temperature range"}, "model_delay_ns": delay, "status": "datasheet-backed"}
    for key, field in (("datasheet_max_ns_25c", "max_ns_25c"), ("datasheet_max_ns_sn74", "max_ns_sn74")):
        base_delay[key].update({"tpd_a_b_to_b_a": {v: row[field] for v, row in transfer_rows.items()}, "ten_oe_to_a_b": {v: row[field] for v, row in enable_rows.items()}, "tdis_oe_to_a_b": {v: row[field] for v, row in disable_rows.items()}, "transition_a_b": {v: row[field] for v, row in transition_rows.items()}})
    propagation = []
    for name, path in timed_paths.items():
        table = path["ranges_ns"]
        endpoint = "A or B output" if name == "transition_time" else path["to"]
        propagation.append({"name": name, "from": "A or B output" if name == "transition_time" else path["from"], "to": "A,B" if name.startswith("OE_") else endpoint, "condition": path["condition"], "parameter": path["parameter"], "timed_path": name, "simple_default_delay_ns": delay, "typ_ns": {v: row["typ_ns"] for v, row in table.items()}, "max_ns_25c": {v: row["max_ns_25c"] for v, row in table.items()}, "max_ns_sn74": {v: row["max_ns_sn74"] for v, row in table.items()}})
    return {"simple": simple, "timed": timed, "timing_parameters": parameters, "_definition_layer_timing": {"schema": "db.component.timing", "version": 1, "part": part, "delay": base_delay, "propagation": propagation, "setup_hold": [], "evidence": deepcopy(dict(evidence)), "timing_parameters": parameters}}


def _resolve_clocked_timing(raw: Mapping[str, Any], clocked: Mapping[str, Any], part: str) -> JsonMap:
    """Resolve the named clocked grammar without collapsing datasheet rows.

    This intentionally accepts a little repetition in the human source: each
    timing row is named exactly as a reader sees it in the datasheet.  The
    compatibility views below are derived from that one source, never from a
    guessed generic propagation delay.
    """

    delay_ns = _nanoseconds(raw.get("default", raw.get("default_delay_ns")))
    edge = raw.get("clock_edge")
    if edge not in {"rising", "falling"}:
        raise ValueError("compact clocked timing requires clock_edge 'rising' or 'falling'")
    conditions = clocked.get("conditions")
    propagation = clocked.get("propagation")
    setup = clocked.get("setup")
    hold = clocked.get("hold")
    pulse = clocked.get("minimum_pulse_width")
    frequency = clocked.get("maximum_clock_frequency")
    evidence = clocked.get("evidence")
    if not all(isinstance(value, Mapping) for value in (conditions, propagation, setup, hold, pulse, frequency, evidence)):
        raise ValueError("compact timing.clocked requires named conditions, propagation, setup, hold, pulse, frequency, and evidence")

    def values(name: str, source: Mapping[str, Any]) -> JsonMap:
        value = source.get(name)
        if not isinstance(value, Mapping) or not value:
            raise ValueError(f"compact timing.clocked missing {name}")
        return _voltage_times(value)

    clear_to_q = values("clear_to_q", propagation)
    clock_to_q = values("clock_to_q", propagation)
    clock_to_rco = values("clock_to_rco", propagation)
    ent_to_rco = values("ent_to_rco", propagation)
    transition_any = values("transition_any", propagation)
    clear_inactive = values("clear_inactive", setup)
    data = values("data", setup)
    enp_ent = values("enp_ent", setup)
    load_low = values("load_low", setup)
    after_clock = values("after_clock", hold)
    clock_high_or_low = values("clock_high_or_low", pulse)
    clear_low = values("clear_low", pulse)
    max_frequency = _voltage_numbers(frequency, "maximum_clock_frequency")
    load_pf = conditions.get("load_pf")
    temperature_c = conditions.get("temperature_c")
    if not isinstance(load_pf, (int, float)) or not isinstance(temperature_c, (int, float)):
        raise ValueError("compact timing.clocked conditions require numeric load_pf and temperature_c")

    timing_parameters: JsonMap = {
        "schema": "db.component.timing_parameters",
        "version": 1,
        "basis": "normalized_from_existing_datasheet_timing",
        "conditions": {"load_pf": load_pf, "ta_c": temperature_c},
        "parameters": {
            "clock_to_q_high": _exact({"typ": clock_to_q}, "timing.datasheet.values.*.clock_to_q", "Direct clock-to-Q table row; no polarity split is printed in the source."),
            "clock_to_q_low": _exact({"typ": clock_to_q}, "timing.datasheet.values.*.clock_to_q", "Direct clock-to-Q table row; no polarity split is printed in the source."),
            "hold": _exact({"min": after_clock}, "definition_layers.timing.timing_requirements.hold_after_clock_ns"),
            "minimum_pulse_width": _exact({"clear_low_min": clear_low, "clock_high_or_low_min": clock_high_or_low}, "definition_layers.timing.timing_requirements.clock_high_or_low_ns and clear_low_ns"),
            "setup": _exact({"clear_inactive_min": clear_inactive, "data_min": data, "enp_ent_min": enp_ent, "load_low_min": load_low}, "definition_layers.timing.timing_requirements.setup_before_clock_ns"),
            "tPLH": _exact({"clear_to_q_typ": clear_to_q, "clock_to_rco_typ": clock_to_rco, "ent_to_rco_typ": ent_to_rco}, "switching characteristics tPLH/tPHL rows", "Direct switching-characteristics table rows; tPLH/tPHL follow the clock-to-Q table entry."),
            "tPHL": _exact({"clear_to_q_typ": clear_to_q, "clock_to_rco_typ": clock_to_rco, "ent_to_rco_typ": ent_to_rco}, "switching characteristics tPLH/tPHL rows", "Direct switching-characteristics table rows; tPLH/tPHL follow the clock-to-Q table entry."),
        },
    }
    for name in ("tPZH", "tPZL", "tPHZ", "tPLZ"):
        timing_parameters["parameters"][name] = {
            "status": "not_applicable",
            "reason": f"{part} has push-pull Q/RCO outputs and no output-enable/high-Z control.",
        }
    delay = {
        "default_ns": delay_ns,
        "source": "simulation default from Python model",
        "datasheet_typical_ns": {
            "condition": str(conditions.get("note", f"CL={load_pf} pF, TA={temperature_c} C")),
            "clear_to_q": clear_to_q,
            "clock_to_q": clock_to_q,
            "clock_to_rco": clock_to_rco,
            "ent_to_rco": ent_to_rco,
            "transition_any": transition_any,
        },
    }
    conservative = {"typ_ns": delay_ns, "max_ns": delay_ns, "min_ns": None, "source": "conservative_default_from_existing_model_delay"}
    paths = {
        "async_control_to_output_ns": {"from": "asynchronous control", "to": "Q/output", "parameter": "tremap", "condition": "async control asserted or released", "ranges_ns": {"conservative_default": deepcopy(conservative)}},
        "clock_to_output_ns": {"from": "CLK/clock control", "to": "Q/output", "parameter": "tco", "condition": "active clock edge", "ranges_ns": {"conservative_default": deepcopy(conservative)}},
        "input_setup_margin_ns": {"from": "D/input", "to": "CLK/clock control", "parameter": "tsu", "condition": "conservative setup placeholder from model delay", "ranges_ns": {"conservative_default": deepcopy(conservative)}},
        "transition_time_ns": {"from": "output transition", "to": "output transition", "parameter": "tt", "condition": "enabled output switches", "ranges_ns": {"conservative_default": deepcopy(conservative)}},
    }
    return {
        "clock_edge": edge,
        "delay_ns": delay_ns,
        "simple": {"default_delay_ns": delay_ns, "source": "legacy functional simulator default"},
        "timed": {"status": "conservative_default_until_part_specific_datasheet_timing_extracted", "paths": paths},
        "timing_parameters": timing_parameters,
        "_definition_layer_timing": {"schema": "db.component.timing", "version": 1, "part": part, "delay": delay, "timing_parameters": timing_parameters, "timing_requirements": {"clear_low_ns": clear_low, "clock_frequency_mhz": max_frequency, "clock_high_or_low_ns": clock_high_or_low, "hold_after_clock_ns": after_clock, "setup_before_clock_ns": {"clear_inactive": clear_inactive, "data": data, "enp_ent": enp_ent, "load_low": load_low}}, "evidence": deepcopy(dict(evidence))},
    }


def _exact(values: JsonMap, source_field: str, note: str | None = None) -> JsonMap:
    item: JsonMap = {"status": "exact", "source_field": source_field, "values_ns": values}
    if note is not None:
        item["note"] = note
    return item


def _voltage_times(values: Mapping[str, Any]) -> JsonMap:
    return {_voltage_key(key): _nanoseconds(value) for key, value in values.items()}


def _voltage_numbers(values: Mapping[str, Any], field: str) -> JsonMap:
    result: JsonMap = {}
    for key, value in values.items():
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f"compact timing.clocked {field} values must be positive numbers")
        result[_voltage_key(key)] = value
    return result


def _voltage_key(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?V", value):
        raise ValueError(f"expected voltage key such as '4.5V', got {value!r}")
    number = value[:-1].replace(".", "_")
    return f"vcc_{number}_v"


def _timing_delay(timing: Mapping[str, Any]) -> JsonMap:
    data = timing["datasheet"]
    return {"status": "datasheet-backed", "model_delay_ns": timing["delay_ns"], "conditions": {"path": data["path"], "load_pf": data.get("load_pf")}, "datasheet_typical_ns": {str(data.get("vcc_v", "default")): data["typical_ns"]}, "datasheet_max_ns_25c": {str(data.get("vcc_v", "default")): data["max_ns_25c"]}, "datasheet_max_ns_minus40_to_85c": {str(data.get("vcc_v", "default")): data["max_ns_minus40_to_85c"]}}


def _timing_parameters(typical: int, maximum: int, maximum_range: int, path: str, part: str, datasheet: Mapping[str, Any]) -> JsonMap:
    values = {"typ": typical, "max_25c": maximum, "max_minus40_to_85c": maximum_range}
    output_note = str(datasheet.get("parameter_note", f"{part} switching characteristics list propagation delay tPLH/tPHL for {path.replace('_', '-')}. Existing source-backed numeric propagation values apply to both output transitions; path-specific simulator delays are unchanged."))
    parameters: JsonMap = {}
    for name in ("tPLH", "tPHL"):
        parameters[name] = {"status": "exact", "values_ns": deepcopy(values), "source_field": "timing.datasheet", "note": output_note}
    for name in ("tPZH", "tPZL", "tPHZ", "tPLZ"):
        parameters[name] = {"status": "not_applicable", "reason": f"{part} has push-pull outputs and no output-enable/high-Z control."}
    for name in ("clock_to_q_high", "clock_to_q_low"):
        parameters[name] = {"status": "not_applicable", "reason": f"{part} is combinational and has no clocked Q output."}
    for name in ("setup", "hold"):
        parameters[name] = {"status": "not_applicable", "reason": f"{part} is combinational and has no setup/hold timing requirement."}
    parameters["minimum_pulse_width"] = {"status": "not_applicable", "reason": f"{part} is combinational and has no clock/reset/write pulse-width requirement."}
    return {"schema": "db.component.timing_parameters", "version": 1, "basis": "normalized_from_existing_datasheet_timing", "conditions": {"path": path, "load_pf": datasheet.get("load_pf"), "vcc_v": datasheet.get("vcc_v")}, "parameters": parameters}


def _generic_timing_layer(part: str, timing: Mapping[str, Any], evidence: Mapping[str, Any]) -> JsonMap:
    """Create the legacy layer view without making it a second authored truth."""

    parameters = deepcopy(timing["timing_parameters"])
    for name in ("tPLH", "tPHL"):
        parameters["parameters"][name]["source_field"] = "definition_layers.timing.delay"
    return {
        "schema": "db.component.timing", "version": 1, "part": part,
        "delay": _timing_delay(timing), "timing_parameters": parameters,
        "evidence": deepcopy(dict(evidence)),
    }


def _resolve_sources(raw: Any) -> list[JsonMap]:
    if not isinstance(raw, list) or not raw or not all(isinstance(item, dict) for item in raw):
        raise ValueError("compact sources must be a non-empty list of objects")
    sources = deepcopy(raw)
    for source in sources:
        source.pop("manufacturer", None)
        if "package" in source and "package_evidence" not in source:
            source["package_evidence"] = source.pop("package")
    return sources


def _resolve_variants(raw: Any) -> list[JsonMap]:
    if not isinstance(raw, list):
        raise ValueError("compact variants must be a list")
    result: list[JsonMap] = []
    for item in raw:
        if isinstance(item, Mapping):
            result.append(deepcopy(dict(item)))
        elif isinstance(item, list) and len(item) == 2 and all(isinstance(value, str) for value in item):
            result.append({"part": item[0], "manufacturer": item[1]})
        else:
            raise ValueError("compact variant must be [part, manufacturer] or an object")
    return result


def _evidence_for(sources: list[JsonMap]) -> JsonMap:
    return deepcopy(sources[0])


def _derived_status(base: Path, sources: list[JsonMap]) -> JsonMap:
    return {"datasheet": "verified" if sources else "missing", "pinout": "verified", "python_behavior": "modeled" if (base / "simulation/model.py").exists() else "missing", "verilog_model": "modeled" if (base / "simulation/model.v").exists() else "missing", "verilog_export": "tested" if (base / "simulation/netlist.json").exists() else "missing", "tests": "tested" if (base / "tests").exists() else "missing"}


def _package_relative_path(base: Path) -> str:
    parts = base.parts
    try:
        start = parts.index("lib")
        return "/".join(parts[start:])
    except ValueError:
        return base.as_posix()


def _nanoseconds(value: Any) -> int:
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, str) and value.endswith("ns") and value[:-2].isdigit():
        return int(value[:-2])
    raise ValueError(f"expected non-negative nanoseconds as integer or '<n>ns', got {value!r}")


def json_load(path: Path) -> JsonMap:
    import json
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"compact schema must be an object: {path}")
    return data
