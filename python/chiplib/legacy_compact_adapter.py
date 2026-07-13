"""Lossless bridge used while timing-rich canonical records migrate to compact.

This module is deliberately a *proof adapter*, not a background converter.
It converts an existing canonical Device record to a candidate compact source,
retaining its canonical timing and timing-layer objects as one compatibility
payload.  ``resolve_compact_definition`` then returns them verbatim.  A package
may only be rewritten after the equivalence gate proves this candidate resolves
back to the original canonical record (apart from the generated ``authoring``
marker).
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


def legacy_to_compact_candidate(legacy: Mapping[str, Any]) -> dict[str, Any]:
    """Return a compact candidate preserving legacy canonical device truth."""

    part = str(legacy["part"])
    metadata = _mapping(legacy.get("metadata"))
    evidence = _mapping(legacy.get("evidence"))
    package = _mapping(legacy.get("package"))
    generation = _mapping(legacy.get("generation"))
    python = _mapping(generation.get("python"))
    verilog = _mapping(generation.get("verilog"))
    layers = _mapping(legacy.get("definition_layers"))
    timing = _mapping(legacy.get("timing"))
    timing_layer = _mapping(layers.get("timing"))
    if not timing or not timing_layer:
        raise ValueError(f"{part}: legacy candidate requires canonical timing and definition_layers.timing")
    electrical = _without_envelope(_mapping(layers.get("electrical")))
    default_delay = timing.get("delay_ns")
    if not isinstance(default_delay, int):
        raise ValueError(f"{part}: legacy canonical timing.delay_ns must be an integer")
    sources = []
    for source in _mapping(legacy.get("datasheet")).get("sources", []):
        item = deepcopy(dict(source))
        if "package_evidence" in item:
            item["package"] = item.pop("package_evidence")
        sources.append(item)
    if not sources:
        raise ValueError(f"{part}: legacy candidate requires datasheet sources")
    return {
        "schema": "db.component.digital.compact",
        "version": "0.2",
        "profile": "74hc.digital@0.2",
        "part": part,
        "about": {
            "title": str(metadata["title"]), "family": str(metadata["family"]),
            "group": str(metadata["group"]), "role": str(metadata["role"]),
            "manufacturer": str(evidence.get("manufacturer", "")),
        },
        "package": {"kind": str(package["kind"]), "default": str(package["default"])},
        "pins": _compact_pins(legacy.get("pins"), part),
        "logic": deepcopy(_mapping(legacy.get("logic"))),
        "timing": {
            "default": f"{default_delay}ns",
            "legacy_canonical": {
                "timing": deepcopy(timing), "definition_layer": deepcopy(timing_layer),
            },
        },
        "model": {"python": str(python["class"]), "verilog": str(verilog["module"])},
        "electrical": electrical,
        "verify": deepcopy(_mapping(legacy.get("verification"))),
        "sources": sources,
        "variants": deepcopy(legacy.get("variants", [])),
        "procurement": deepcopy(_mapping(legacy.get("procurement"))),
    }


def legacy_memory_to_compact_candidate(legacy: Mapping[str, Any]) -> dict[str, Any]:
    """Return a strict-memory compact candidate without weakening legacy truth.

    The memory profile has a useful human-facing vocabulary (parallel SRAM or
    EEPROM, address/data widths, read/write/tri-state controls).  Older
    canonical records predate that vocabulary, so this adapter writes the
    vocabulary as a resolver envelope and carries their complete canonical
    logic and timing objects verbatim.  It is a migration proof, never an
    implicit source rewrite.
    """

    part = str(legacy["part"])
    metadata = _mapping(legacy.get("metadata"))
    if metadata.get("group") != "memory":
        raise ValueError(f"{part}: legacy memory candidate requires metadata.group=memory")
    logic = _mapping(legacy.get("logic"))
    kind = str(logic.get("type", "")).lower()
    if "ram" in kind:
        memory_type = "parallel_sram"
    elif "eeprom" in kind or "rom" in kind:
        memory_type = "parallel_eeprom"
    else:
        raise ValueError(f"{part}: legacy memory logic type is not SRAM/EEPROM: {logic.get('type')!r}")
    package = _mapping(legacy.get("package"))
    generation = _mapping(legacy.get("generation"))
    python = _mapping(generation.get("python"))
    verilog = _mapping(generation.get("verilog"))
    layers = _mapping(legacy.get("definition_layers"))
    timing = _mapping(legacy.get("timing"))
    timing_layer = _mapping(layers.get("timing"))
    delay = _mapping(timing_layer.get("delay"))
    default_delay = delay.get("model_delay_ns")
    if not isinstance(default_delay, int):
        raise ValueError(f"{part}: definition_layers.timing.delay.model_delay_ns must be an integer")
    sources = _sources(legacy, part)
    address_width, data_width = _memory_widths(legacy.get("pins"), part)
    evidence = _mapping(legacy.get("evidence"))
    return {
        "schema": "db.component.memory.compact",
        "version": "0.2",
        "profile": "memory.async@0.2",
        "part": part,
        "about": {
            "title": str(metadata["title"]), "family": str(metadata["family"]),
            "group": "memory", "role": str(metadata["role"]),
            "manufacturer": str(evidence.get("manufacturer", "")),
        },
        "package": {"kind": str(package["kind"]), "default": str(package["default"])},
        "pins": _compact_pins(legacy.get("pins"), part),
        "logic": {
            "type": memory_type, "address_width": address_width, "data_width": data_width,
            "read": {"enable": ["/CE", "/OE"]}, "write": {"enable": "/WE"},
            "tristate": {"data": "I/O"}, "legacy_canonical": deepcopy(dict(logic)),
        },
        "timing": {
            "default": f"{default_delay}ns",
            "asynchronous_memory": _legacy_memory_timing_envelope(timing, timing_layer, default_delay, part),
            "legacy_canonical": {"timing": deepcopy(dict(timing)), "definition_layer": deepcopy(dict(timing_layer))},
        },
        "model": {"python": str(python["class"]), "verilog": str(verilog["module"])},
        "electrical": _without_envelope(_mapping(layers.get("electrical"))),
        "verify": deepcopy(_mapping(legacy.get("verification"))),
        "sources": sources, "variants": deepcopy(legacy.get("variants", [])),
        "procurement": deepcopy(_mapping(legacy.get("procurement"))),
    }


def non_derived_view(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return fields migration must preserve exactly.

    ``status`` depends on local artifact existence and ``authoring`` is new
    resolver provenance.  All other canonical fields are device truth or
    compatibility contracts and therefore remain in the comparison.
    """

    return {key: deepcopy(value) for key, value in record.items() if key not in {"status", "authoring"}}


def _compact_pins(raw: Any, part: str) -> dict[str, list[Any]]:
    if not isinstance(raw, list):
        raise ValueError(f"{part}: legacy pins must be a list")
    directions = {"input": "in", "output": "out", "bidirectional": "io"}
    allowed = {"active_low": "active", "clock": "edge", "rail": "rail", "bus": "bus", "bit": "bit", "function": "function", "drive": "drive", "enable": "enable"}
    result: dict[str, list[Any]] = {}
    for pin in raw:
        if not isinstance(pin, Mapping):
            raise ValueError(f"{part}: legacy pin is not an object")
        name, direction, number = str(pin["name"]), str(pin["direction"]), int(pin["number"])
        compact_direction = directions.get(direction, direction)
        metadata: dict[str, Any] = {}
        for old, new in allowed.items():
            if old not in pin:
                continue
            value = pin[old]
            if old == "active_low" and value:
                metadata[new] = "low"
            elif old == "clock" and value:
                # Legacy canonical has a boolean clock flag but no edge field.
                # This bridge refuses to guess its edge rather than fabricate it.
                raise ValueError(f"{part}: pin {number} has clock=true without an explicit legacy edge")
            elif old not in {"active_low", "clock"}:
                metadata[new] = deepcopy(value)
        result[str(number)] = [name, compact_direction, metadata] if metadata else [name, compact_direction]
    return result


def _sources(legacy: Mapping[str, Any], part: str) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for source in _mapping(legacy.get("datasheet")).get("sources", []):
        item = deepcopy(dict(source))
        if "package_evidence" in item:
            item["package"] = item.pop("package_evidence")
        sources.append(item)
    if not sources:
        raise ValueError(f"{part}: legacy candidate requires datasheet sources")
    return sources


def _memory_widths(raw: Any, part: str) -> tuple[int, int]:
    if not isinstance(raw, list):
        raise ValueError(f"{part}: legacy pins must be a list")
    names = {str(pin.get("name", "")) for pin in raw if isinstance(pin, Mapping)}
    address_bits = [name for name in names if name.startswith("A") and name[1:].isdigit()]
    data_bits = [name for name in names if name.startswith("I/O") and name[3:].isdigit()]
    if len(address_bits) != 15 or len(data_bits) != 8:
        raise ValueError(f"{part}: expected 15 address and 8 I/O pins, got {len(address_bits)} and {len(data_bits)}")
    return 15, 8


def _legacy_memory_timing_envelope(
    timing: Mapping[str, Any], timing_layer: Mapping[str, Any], default_delay: int, part: str
) -> dict[str, Any]:
    """Make the strict compact schema check a legacy payload without using it.

    The shared resolver detects ``legacy_canonical`` first.  These values are
    therefore a schema envelope only, copied from already canonical paths so
    validation cannot accidentally invent a faster or weaker timing claim.
    """

    paths = _mapping(timing.get("paths"))
    write = _mapping(timing.get("write"))
    evidence = _mapping(timing_layer.get("evidence"))
    variant = str(timing.get("variant", f"{part}-legacy"))
    address = paths.get("address_to_data_valid_ns", default_delay)
    ce = paths.get("ce_to_data_valid_ns", default_delay)
    oe = paths.get("oe_to_data_valid_ns", default_delay)
    float_time = paths.get("ce_or_oe_to_high_z_ns", default_delay)
    if not all(isinstance(value, int) and value >= 0 for value in (address, ce, oe, float_time)):
        raise ValueError(f"{part}: canonical memory read timing must be non-negative integers")
    return {
        "variant": {
            "selected": variant, "available": {variant: default_delay},
            "physical_signoff_requires": "legacy canonical timing retained verbatim; verify installed speed grade before physical use",
        },
        "read": {"address": f"{address}ns", "ce": f"{ce}ns", "oe": f"{oe}ns", "float": f"{float_time}ns"},
        "write": deepcopy(dict(write)),
        "model": {"fidelity_level": "legacy_canonical_compatibility"},
        "evidence": deepcopy(dict(evidence)),
    }


def _without_envelope(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: deepcopy(item) for key, item in value.items() if key not in {"schema", "version", "part"}}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
