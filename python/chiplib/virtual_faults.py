"""Virtual physical-system fault checks for circuit packages."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from .db import ROOT, load_component, load_package_definition


JsonMap = dict[str, Any]
CONNECTION_RE = re.compile(r"^(?P<ref>[A-Za-z][A-Za-z0-9_]*)\.(?P<pin>[^,\s]+)$")
NUMERIC_RANGE_RE = re.compile(r"^(?P<start>\d+)\.\.(?P<end>\d+)$")
NAME_RANGE_RE = re.compile(r"^(?P<prefix>/?[A-Za-z_]+)(?P<start>\d+)\.\.(?P=prefix)(?P<end>\d+)$")
ACTIVE_LOW_WORDS = ("active-low", "active low", "low enables", "low only", "low-to-high")
BUS_PROOF_WORDS = (
    "one active",
    "exactly one",
    "no more than one",
    "single-driver",
    "disabled",
    "enable",
    "high-z",
    "contention",
    "bus fight",
    "bus-fight",
)
DELAY_WORDS = ("rcparasitic", "delaynoise", "deadband", "setup/hold", "settle", "float")


@dataclass(frozen=True)
class PinRef:
    ref: str
    part: str
    token: str
    pin: JsonMap | None
    resolved: bool

    @property
    def direction(self) -> str:
        if self.pin is None:
            return "unknown"
        return str(self.pin.get("direction", "unknown")).lower()


def load_circuit_fault_report(path: str | Path) -> JsonMap:
    """Load a circuit JSON file and run virtual physical-system checks."""

    circuit_path = Path(path)
    circuit = json.loads(circuit_path.read_text(encoding="utf-8"))
    report = check_virtual_physical_faults(circuit)
    report["source"] = circuit_path.relative_to(ROOT).as_posix() if circuit_path.is_absolute() and ROOT in circuit_path.parents else str(circuit_path)
    return report


def check_virtual_physical_faults(circuit: JsonMap) -> JsonMap:
    """Return a report for the four required virtual physical-system traps."""

    ref_parts = _ref_parts(circuit)
    component_pins = _component_pin_maps(ref_parts)
    findings: list[JsonMap] = []

    pin_refs_by_net = _resolve_wiring(circuit, ref_parts, component_pins, findings)
    _check_output_output_contention(circuit, pin_refs_by_net, findings)
    _check_edge_polarity(circuit, ref_parts, findings)
    _check_propagation_delay(circuit, pin_refs_by_net, findings)

    traps = _trap_coverage(findings)
    return {
        "schema": "components.virtual_physical_fault_report",
        "version": 1,
        "circuit": circuit.get("id", ""),
        "ok": not findings,
        "checks": traps,
        "findings": findings,
        "fix_methods": {
            "pin_number_truth": "Fix the chip definition or source-backed pin map first; do not move circuit wires to hide bad data.",
            "output_output_bus_contention": "Add tri-state enables, buffer/transceiver direction control, or bus-owner sequencing.",
            "edge_polarity": "Move the signal to the correct clock phase or add an intentional inverter tied to the datasheet edge.",
            "propagation_delay_deadband": "Add phase separation, disable the old driver earlier, enable the new driver later, buffer/shorten the net, or reduce clock speed.",
        },
    }


def _ref_parts(circuit: JsonMap) -> dict[str, str]:
    return {
        str(chip["ref"]): str(chip["part"])
        for chip in circuit.get("chips", [])
        if isinstance(chip, dict) and chip.get("ref") and chip.get("part")
    }


def _component_pin_maps(ref_parts: dict[str, str]) -> dict[str, JsonMap]:
    maps: dict[str, JsonMap] = {}
    for part in set(ref_parts.values()):
        try:
            manifest = load_component(part)
        except KeyError:
            continue
        pins = list(manifest.get("pins", []))
        by_number = {str(pin.get("number")): pin for pin in pins if pin.get("number") is not None}
        by_name = {_norm_pin_name(str(pin.get("name", ""))): pin for pin in pins if pin.get("name")}
        maps[part] = {"by_number": by_number, "by_name": by_name}
    return maps


def _resolve_wiring(
    circuit: JsonMap,
    ref_parts: dict[str, str],
    component_pins: dict[str, JsonMap],
    findings: list[JsonMap],
) -> dict[str, list[PinRef]]:
    refs_by_net: dict[str, list[PinRef]] = {}
    for row in circuit.get("wiring", []):
        if not isinstance(row, dict):
            continue
        net = str(row.get("net", ""))
        refs_by_net[net] = []
        for connection in row.get("connections", []):
            for pin_ref in _resolve_connection(str(connection), ref_parts, component_pins):
                refs_by_net[net].append(pin_ref)
                if not pin_ref.resolved:
                    findings.append(_finding(
                        "pin_number_truth",
                        "error",
                        f"{net}: {pin_ref.ref}.{pin_ref.token} does not match known pins for {pin_ref.part}",
                        "Fix the component pin map or the circuit connection token.",
                    ))
                elif pin_ref.token.startswith("/") and pin_ref.pin and not bool(pin_ref.pin.get("active_low", False)):
                    findings.append(_finding(
                        "pin_number_truth",
                        "error",
                        f"{net}: {pin_ref.ref}.{pin_ref.token} is written active-low but the DB pin is not active-low",
                        "Fix the active-low marker in the DB or the circuit pin name.",
                    ))
    return refs_by_net


def _resolve_connection(connection: str, ref_parts: dict[str, str], component_pins: dict[str, JsonMap]) -> list[PinRef]:
    match = CONNECTION_RE.match(connection)
    if not match:
        return []
    ref = match.group("ref")
    token = match.group("pin")
    part = ref_parts.get(ref)
    if part is None:
        return [PinRef(ref, "unknown", token, None, False)]
    pin_map = component_pins.get(part)
    if pin_map is None:
        return []

    numeric_range = NUMERIC_RANGE_RE.match(token)
    if numeric_range:
        start = int(numeric_range.group("start"))
        end = int(numeric_range.group("end"))
        step = 1 if end >= start else -1
        refs = []
        for number in range(start, end + step, step):
            pin = pin_map["by_number"].get(str(number))
            refs.append(PinRef(ref, part, str(number), pin, pin is not None))
        return refs

    name_range = NAME_RANGE_RE.match(token)
    if name_range:
        prefix = name_range.group("prefix")
        start = int(name_range.group("start"))
        end = int(name_range.group("end"))
        step = 1 if end >= start else -1
        refs = []
        for number in range(start, end + step, step):
            name = f"{prefix}{number}"
            pin = pin_map["by_name"].get(_norm_pin_name(name))
            if pin is not None:
                refs.append(PinRef(ref, part, name, pin, True))
        return refs

    pin = pin_map["by_number"].get(token) or pin_map["by_name"].get(_norm_pin_name(token))
    if pin is None and _looks_like_pin_token(token):
        return [PinRef(ref, part, token, None, False)]
    if pin is not None:
        return [PinRef(ref, part, token, pin, True)]
    return []


def _check_output_output_contention(circuit: JsonMap, pin_refs_by_net: dict[str, list[PinRef]], findings: list[JsonMap]) -> None:
    circuit_text = _text_blob(circuit)
    for net, refs in pin_refs_by_net.items():
        drivers = [ref for ref in refs if ref.direction in {"output", "bidirectional"}]
        if len(drivers) < 2:
            continue
        net_text = f"{net} {_wiring_rule_text(circuit, net)} {circuit_text}".lower()
        if any(word in net_text for word in BUS_PROOF_WORDS):
            continue
        names = ", ".join(f"{ref.ref}.{ref.token}" for ref in drivers)
        findings.append(_finding(
            "output_output_bus_contention",
            "error",
            f"{net}: multiple possible drivers without explicit bus/enable proof: {names}",
            "Add a named bus ownership rule proving at most one active driver, or change the wiring to output-to-input.",
        ))


def _check_edge_polarity(circuit: JsonMap, ref_parts: dict[str, str], findings: list[JsonMap]) -> None:
    edge_parts = {
        part: _part_trigger_edge(part)
        for part in set(ref_parts.values())
        if _part_trigger_edge(part) in {"rising", "falling"}
    }
    if not edge_parts:
        return
    text = _text_blob(circuit).lower()
    for edge in set(edge_parts.values()):
        if edge == "rising" and ("rising" in text or "positive-edge" in text or "positive edge" in text):
            continue
        if edge == "falling" and ("falling" in text or "negative-edge" in text or "negative edge" in text):
            continue
        parts = sorted(part for part, part_edge in edge_parts.items() if part_edge == edge)
        findings.append(_finding(
            "edge_polarity",
            "error",
            f"edge-sensitive parts {parts} require {edge} edge text in circuit behavior/timing/verification",
            "State the datasheet trigger edge and prove the opposite edge holds.",
        ))


def _part_trigger_edge(part: str) -> str:
    try:
        package = load_package_definition(part, required=False)
    except KeyError:
        return ""
    if package is None:
        return ""
    truth_path = ROOT / str(package.get("definition_path", "")).replace("definition/definition.json", "tests/truth_table.json")
    if not truth_path.exists():
        return ""
    data = json.loads(truth_path.read_text(encoding="utf-8"))
    edge = data.get("edge_criteria", {}).get("trigger_edge", "")
    return str(edge).lower()


def _check_propagation_delay(circuit: JsonMap, pin_refs_by_net: dict[str, list[PinRef]], findings: list[JsonMap]) -> None:
    text = _text_blob(circuit).lower()
    has_shared_bus = any(
        len([ref for ref in refs if ref.direction in {"output", "bidirectional"}]) >= 2
        for refs in pin_refs_by_net.values()
    )
    timing = circuit.get("timing", {})
    stress_nets = timing.get("stress_nets", []) if isinstance(timing, dict) else []
    if not has_shared_bus and not stress_nets:
        return
    if any(word in text for word in DELAY_WORDS):
        return
    findings.append(_finding(
        "propagation_delay_deadband",
        "error",
        "shared bus or stress nets lack R/C, DelayNoise, setup/hold, or deadband coverage",
        "Add virtual R/C or delay-noise coverage and document the positive disable-to-enable deadband.",
    ))


def _trap_coverage(findings: list[JsonMap]) -> JsonMap:
    ids = ("pin_number_truth", "output_output_bus_contention", "edge_polarity", "propagation_delay_deadband")
    return {
        item: {
            "status": "pass" if not any(finding["id"] == item for finding in findings) else "fail",
            "finding_count": sum(1 for finding in findings if finding["id"] == item),
        }
        for item in ids
    }


def _finding(finding_id: str, severity: str, message: str, fix_method: str) -> JsonMap:
    return {"id": finding_id, "severity": severity, "message": message, "fix_method": fix_method}


def _norm_pin_name(name: str) -> str:
    return name.strip().replace("_bar", "").replace("bar", "").replace(" ", "").upper()


def _looks_like_pin_token(token: str) -> bool:
    return token.isdigit() or token.startswith("/") or bool(re.match(r"^[A-Za-z_]+\d*$", token))


def _wiring_rule_text(circuit: JsonMap, net: str) -> str:
    for row in circuit.get("wiring", []):
        if isinstance(row, dict) and row.get("net") == net:
            return " ".join(str(value) for key, value in row.items() if key != "connections")
    return ""


def _text_blob(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_text_blob(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_text_blob(item) for item in value)
    return str(value)
