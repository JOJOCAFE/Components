"""Strict, runtime-independent parser for ``components.lib.circuit`` packages."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .db import load_component


ROOT = Path(__file__).resolve().parents[2]
CIRCUIT_ROOT = ROOT / "examples" / "circuits"
REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
NUMERIC_ENDPOINT_RE = re.compile(
    r"^(?P<ref>[A-Za-z][A-Za-z0-9_]*)\.(?P<start>[0-9]+)(?:\.\.(?P<end>[0-9]+))?$"
)
SYMBOLIC_ENDPOINT_RE = re.compile(
    r"^(?P<ref>[A-Za-z][A-Za-z0-9_]*)\.(?P<name>[^\s,]+)$"
)
PORT_DIRECTIONS = {
    "input", "output", "input/output", "input_output", "bidirectional", "internal", "passive", "power", "absent", "unknown"
}


@dataclass(frozen=True)
class CircuitPackageIssue:
    code: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


class CircuitPackageValidationError(ValueError):
    """Raised after collecting all structural and reference errors in a package."""

    def __init__(self, issues: list[CircuitPackageIssue], source: Path | None = None):
        self.issues = tuple(issues)
        self.source = source
        prefix = f"{source}: " if source else ""
        detail = "; ".join(f"{item.path} [{item.code}] {item.message}" for item in issues)
        super().__init__(f"{prefix}invalid circuit package: {detail}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": "invalid_circuit_package",
            "source": str(self.source) if self.source else None,
            "issues": [item.to_dict() for item in self.issues],
        }


@dataclass(frozen=True)
class CircuitChip:
    ref: str
    part: str
    role: str
    symbolic_endpoints: tuple[str, ...] = ()


@dataclass(frozen=True)
class CircuitPort:
    name: str
    direction: str
    active_low: bool = False
    edge: str | None = None
    description: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class NumericEndpoint:
    text: str
    ref: str
    start: int
    end: int

    @property
    def pins(self) -> tuple[int, ...]:
        step = 1 if self.end >= self.start else -1
        return tuple(range(self.start, self.end + step, step))


@dataclass(frozen=True)
class SymbolicEndpoint:
    text: str
    ref: str
    name: str


@dataclass(frozen=True)
class BoundaryEndpoint:
    text: str


CircuitEndpoint = NumericEndpoint | SymbolicEndpoint | BoundaryEndpoint


def expand_boundary_name(name: str) -> tuple[str, ...]:
    """Expand an ordered ``NAME0..NAMEn`` boundary, preserving direction."""

    match = re.fullmatch(r"(.*?)(\d+)\.\.(?:\1)?(\d+)", name)
    if match is None:
        return (name,)
    prefix, start_text, end_text = match.groups()
    start, end = int(start_text), int(end_text)
    step = 1 if end >= start else -1
    return tuple(f"{prefix}{index}" for index in range(start, end + step, step))


@dataclass(frozen=True)
class CircuitWiring:
    net: str
    connections: tuple[CircuitEndpoint, ...]
    rule: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class VerificationReference:
    path: str
    resolved_path: Path


@dataclass(frozen=True)
class CircuitPackage:
    schema: str
    version: int
    id: str
    title: str
    source_path: Path | None
    source_project_name: str
    sources: tuple[Path, ...]
    chips: tuple[CircuitChip, ...]
    ports: tuple[CircuitPort, ...]
    wiring: tuple[CircuitWiring, ...]
    verification: tuple[VerificationReference, ...]
    raw: Mapping[str, Any]


def load_circuit_package(path: str | Path) -> CircuitPackage:
    """Load and validate one package without constructing simulation objects."""

    source = Path(path).resolve()
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issue = CircuitPackageIssue("invalid_json", "$", str(exc))
        raise CircuitPackageValidationError([issue], source) from exc
    return parse_circuit_package(data, source_path=source)


def parse_circuit_package(
    data: Any,
    *,
    source_path: str | Path | None = None,
    check_files: bool = True,
) -> CircuitPackage:
    """Validate already-decoded package data and return immutable typed records."""

    source = Path(source_path).resolve() if source_path is not None else None
    issues: list[CircuitPackageIssue] = []

    def issue(code: str, path: str, message: str) -> None:
        issues.append(CircuitPackageIssue(code, path, message))

    if not isinstance(data, dict):
        raise CircuitPackageValidationError(
            [CircuitPackageIssue("type", "$", "package must be a JSON object")], source
        )

    schema = _required_string(data, "schema", "$", issue)
    if schema and schema != "components.lib.circuit":
        issue("schema", "$.schema", "must equal 'components.lib.circuit'")
    version = data.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        issue("type", "$.version", "must be a positive integer")
        version = 0
    package_id = _required_string(data, "id", "$", issue)
    title = _required_string(data, "title", "$", issue)

    source_project = data.get("source_project")
    source_name = ""
    source_paths: list[Path] = []
    if not isinstance(source_project, dict):
        issue("type", "$.source_project", "must be an object")
    else:
        source_name = _required_string(source_project, "name", "$.source_project", issue)
        values = _required_list(source_project, "paths", "$.source_project", issue)
        for index, value in enumerate(values):
            item_path = f"$.source_project.paths[{index}]"
            if not isinstance(value, str) or not value.strip():
                issue("type", item_path, "must be a non-empty path string")
                continue
            resolved = _resolve_source(value)
            source_paths.append(resolved)
            if check_files and not resolved.is_file():
                issue("source_not_found", item_path, f"source file does not exist: {value}")

    chips = _parse_chips(data.get("chips"), issue)
    ports = _parse_ports(data.get("ports"), issue)
    wiring = _parse_wiring(data.get("wiring", []), issue)
    verification = _parse_verification(data.get("verification"), source, check_files, issue)
    _validate_endpoints(chips, ports, wiring, issue)

    if issues:
        raise CircuitPackageValidationError(issues, source)
    return CircuitPackage(
        schema=schema,
        version=version,
        id=package_id,
        title=title,
        source_path=source,
        source_project_name=source_name,
        sources=tuple(source_paths),
        chips=tuple(chips),
        ports=tuple(ports),
        wiring=tuple(wiring),
        verification=tuple(verification),
        raw=data,
    )


def _required_string(obj: Mapping[str, Any], key: str, base: str, issue: Any) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        issue("type", f"{base}.{key}", "must be a non-empty string")
        return ""
    return value


def _required_list(obj: Mapping[str, Any], key: str, base: str, issue: Any) -> list[Any]:
    value = obj.get(key)
    if not isinstance(value, list) or not value:
        issue("type", f"{base}.{key}", "must be a non-empty list")
        return []
    return value


def _parse_chips(value: Any, issue: Any) -> list[CircuitChip]:
    if not isinstance(value, list) or not value:
        issue("type", "$.chips", "must be a non-empty list")
        return []
    result: list[CircuitChip] = []
    refs: set[str] = set()
    for index, row in enumerate(value):
        base = f"$.chips[{index}]"
        if not isinstance(row, dict):
            issue("type", base, "must be an object")
            continue
        ref = _required_string(row, "ref", base, issue)
        part = _required_string(row, "part", base, issue)
        role = _required_string(row, "role", base, issue)
        if ref and not REF_RE.fullmatch(ref):
            issue("invalid_ref", f"{base}.ref", "must start with a letter and contain only letters, digits, or underscore")
        if ref in refs:
            issue("duplicate_ref", f"{base}.ref", f"chip ref {ref!r} is already declared")
        refs.add(ref)
        symbols = row.get("symbolic_endpoints", [])
        if not isinstance(symbols, list) or any(not isinstance(item, str) or not item for item in symbols):
            issue("type", f"{base}.symbolic_endpoints", "must be a list of non-empty strings")
            symbols = []
        if len(symbols) != len(set(symbols)):
            issue("duplicate_symbolic_endpoint", f"{base}.symbolic_endpoints", "contains duplicate names")
        result.append(CircuitChip(ref, part, role, tuple(symbols)))
    return result


def _parse_ports(value: Any, issue: Any) -> list[CircuitPort]:
    if not isinstance(value, list) or not value:
        issue("type", "$.ports", "must be a non-empty list")
        return []
    result: list[CircuitPort] = []
    names: set[str] = set()
    for index, row in enumerate(value):
        base = f"$.ports[{index}]"
        if not isinstance(row, dict):
            issue("type", base, "must be an object")
            continue
        name = _required_string(row, "name", base, issue)
        direction = _required_string(row, "direction", base, issue)
        if direction and direction not in PORT_DIRECTIONS:
            issue("invalid_direction", f"{base}.direction", f"unsupported direction {direction!r}")
        if name in names:
            issue("duplicate_port", f"{base}.name", f"port {name!r} is already declared")
        names.add(name)
        active_low = row.get("active_low", False)
        if not isinstance(active_low, bool):
            issue("type", f"{base}.active_low", "must be boolean")
            active_low = False
        optional: dict[str, str | None] = {}
        for key in ("edge", "description", "source"):
            item = row.get(key)
            if item is not None and (not isinstance(item, str) or not item):
                issue("type", f"{base}.{key}", "must be a non-empty string when present")
                item = None
            optional[key] = item
        result.append(CircuitPort(name, direction, active_low, **optional))
    return result


def _parse_wiring(value: Any, issue: Any) -> list[CircuitWiring]:
    if not isinstance(value, list):
        issue("type", "$.wiring", "must be a list")
        return []
    result: list[CircuitWiring] = []
    nets: set[str] = set()
    for index, row in enumerate(value):
        base = f"$.wiring[{index}]"
        if not isinstance(row, dict):
            issue("type", base, "must be an object")
            continue
        net = _required_string(row, "net", base, issue)
        if net in nets:
            issue("duplicate_net", f"{base}.net", f"net {net!r} is already declared")
        nets.add(net)
        values = _required_list(row, "connections", base, issue)
        endpoints: list[CircuitEndpoint] = []
        seen: set[str] = set()
        for endpoint_index, text in enumerate(values):
            path = f"{base}.connections[{endpoint_index}]"
            if not isinstance(text, str) or not text:
                issue("type", path, "must be a non-empty endpoint string")
                continue
            if text in seen:
                issue("duplicate_endpoint", path, f"endpoint {text!r} is repeated on this net")
            seen.add(text)
            numeric = NUMERIC_ENDPOINT_RE.fullmatch(text)
            symbolic = SYMBOLIC_ENDPOINT_RE.fullmatch(text)
            if numeric:
                endpoints.append(NumericEndpoint(text, numeric["ref"], int(numeric["start"]), int(numeric["end"] or numeric["start"])))
            elif symbolic:
                endpoints.append(SymbolicEndpoint(text, symbolic["ref"], symbolic["name"]))
            else:
                endpoints.append(BoundaryEndpoint(text))
        optional = {}
        for key in ("rule", "description"):
            item = row.get(key)
            if item is not None and (not isinstance(item, str) or not item):
                issue("type", f"{base}.{key}", "must be a non-empty string when present")
                item = None
            optional[key] = item
        result.append(CircuitWiring(net, tuple(endpoints), **optional))
    return result


def _parse_verification(value: Any, source: Path | None, check_files: bool, issue: Any) -> list[VerificationReference]:
    if not isinstance(value, dict):
        issue("type", "$.verification", "must be an object")
        return []
    tests = _required_list(value, "tests", "$.verification", issue)
    result: list[VerificationReference] = []
    seen: set[str] = set()
    for index, item in enumerate(tests):
        path = f"$.verification.tests[{index}]"
        if not isinstance(item, str) or not item:
            issue("type", path, "must be a non-empty path string")
            continue
        if item in seen:
            issue("duplicate_verification_ref", path, f"verification reference {item!r} is repeated")
        seen.add(item)
        base = source.parent if source else ROOT
        resolved = (base / item).resolve() if not Path(item).is_absolute() else Path(item).resolve()
        if check_files and not resolved.is_file():
            issue("proof_not_found", path, f"verification file does not exist: {item}")
        result.append(VerificationReference(item, resolved))
    return result


def _validate_endpoints(chips: list[CircuitChip], ports: list[CircuitPort], wiring: list[CircuitWiring], issue: Any) -> None:
    chip_map = {chip.ref: chip for chip in chips}
    boundaries = {port.name for port in ports} | {row.net for row in wiring}
    package_ports = _package_port_map()
    db_pins: dict[str, set[int] | None] = {}
    boundary_bindings: dict[str, tuple[str, ...]] = {}
    for wire_index, wire in enumerate(wiring):
        for endpoint_index, endpoint in enumerate(wire.connections):
            path = f"$.wiring[{wire_index}].connections[{endpoint_index}]"
            if endpoint.text in boundaries:
                if isinstance(endpoint, BoundaryEndpoint) and endpoint.text.upper() not in {"VCC", "GND"}:
                    lines = expand_boundary_name(wire.net)
                    endpoint_width = len(expand_boundary_name(endpoint.text))
                    if endpoint_width not in {1, len(lines)}:
                        issue(
                            "ambiguous_boundary_width", path,
                            f"boundary {endpoint.text!r} has width {endpoint_width}, expected {len(lines)} for {wire.net!r}",
                        )
                    previous = boundary_bindings.get(endpoint.text)
                    if previous is not None and previous != lines:
                        issue(
                            "ambiguous_boundary_mapping", path,
                            f"boundary {endpoint.text!r} maps to both {previous!r} and {lines!r}",
                        )
                    boundary_bindings[endpoint.text] = lines
                continue
            if isinstance(endpoint, BoundaryEndpoint):
                issue("undeclared_boundary", path, f"symbolic boundary {endpoint.text!r} is not a declared port or net")
                continue
            chip = chip_map.get(endpoint.ref)
            if chip is None:
                issue("unknown_ref", path, f"chip ref {endpoint.ref!r} is not declared")
                continue
            if isinstance(endpoint, NumericEndpoint):
                pins = db_pins.get(chip.part)
                if chip.part not in db_pins:
                    try:
                        component = load_component(chip.part)
                    except KeyError:
                        pins = None
                    else:
                        pins = {pin["number"] for pin in component.get("pins", []) if isinstance(pin, dict) and isinstance(pin.get("number"), int)}
                    db_pins[chip.part] = pins
                if pins is None:
                    issue("numeric_endpoint_without_db_part", path, f"part {chip.part!r} has no production DB pin definition")
                else:
                    missing = [pin for pin in endpoint.pins if pin not in pins]
                    if missing:
                        issue("unknown_pin", path, f"pin(s) {missing} do not exist on {chip.part}")
                continue
            allowed = set(chip.symbolic_endpoints) | package_ports.get(chip.part, set())
            if endpoint.name not in allowed:
                issue("undeclared_symbolic_endpoint", path, f"{endpoint.name!r} is not declared for {chip.ref} ({chip.part})")


def _package_port_map() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for path in CIRCUIT_ROOT.glob("*/circuit.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        result[path.parent.name] = {
            row["name"] for row in data.get("ports", [])
            if isinstance(row, dict) and isinstance(row.get("name"), str)
        }
    return result


def _resolve_source(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()
