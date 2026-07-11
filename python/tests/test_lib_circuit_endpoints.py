"""Strict endpoint validation for library circuit wiring.

This audit intentionally rejects endpoint text that cannot be resolved.  Circuit
JSON owners must make symbolic package boundaries explicit instead of relying on
the permissive heuristics used by older fault checks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import re

from chiplib.db import load_component


ROOT = Path(__file__).resolve().parents[2]
CIRCUIT_ROOT = ROOT / "examples" / "circuits"
REAL_PIN_RE = re.compile(r"^(?P<ref>[A-Za-z][A-Za-z0-9_]*)\.(?P<start>[0-9]+)(?:\.\.(?P<end>[0-9]+))?$")
SYMBOLIC_REF_RE = re.compile(r"^(?P<ref>[A-Za-z][A-Za-z0-9_]*)\.(?P<token>[^\s,]+)$")
NAME_RANGE_RE = re.compile(r"^(?P<prefix>/?[A-Za-z_]+)(?P<start>[0-9]+)\.\.(?:(?P=prefix))?(?P<end>[0-9]+)$")


@dataclass(frozen=True, order=True)
class EndpointFinding:
    circuit: str
    wiring_index: int
    net: str
    endpoint: str
    reason: str
    fix: str

    def line(self) -> str:
        return (
            f"{self.circuit}: wiring[{self.wiring_index}] net {self.net!r}, "
            f"endpoint {self.endpoint!r}: {self.reason}; FIX: {self.fix}"
        )


def _load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path}: circuit JSON must be an object")
    return data


def _circuit_paths() -> list[Path]:
    return sorted(CIRCUIT_ROOT.glob("*/circuit.json"))


def _circuit_packages() -> dict[str, dict]:
    packages: dict[str, dict] = {}
    for path in _circuit_paths():
        data = _load_json(path)
        packages[path.parent.name] = data
    return packages


def _pin_maps(part: str) -> tuple[dict[int, dict], dict[str, int]] | None:
    try:
        component = load_component(part)
    except KeyError:
        return None
    pins = component.get("pins", [])
    by_number = {
        int(pin["number"]): pin
        for pin in pins
        if isinstance(pin, dict) and isinstance(pin.get("number"), int)
    }
    by_name = {
        str(pin["name"]).upper(): int(pin["number"])
        for pin in pins
        if isinstance(pin, dict)
        and isinstance(pin.get("number"), int)
        and isinstance(pin.get("name"), str)
    }
    return by_number, by_name


def _declared_symbols(circuit: dict) -> set[str]:
    return _declared_ports(circuit) | {
        str(row["net"])
        for row in circuit.get("wiring", [])
        if isinstance(row, dict) and isinstance(row.get("net"), str)
    }


def _declared_ports(circuit: dict) -> set[str]:
    return {
        str(port["name"])
        for port in circuit.get("ports", [])
        if isinstance(port, dict) and isinstance(port.get("name"), str)
    }


def _numeric_fix(ref: str, token: str, by_name: dict[str, int]) -> str | None:
    direct = by_name.get(token.upper())
    if direct is not None:
        return f"replace with {ref}.{direct}"
    match = NAME_RANGE_RE.fullmatch(token)
    if match is None:
        return None
    start = int(match.group("start"))
    end = int(match.group("end"))
    step = 1 if end >= start else -1
    names = [f"{match.group('prefix')}{bit}".upper() for bit in range(start, end + step, step)]
    if not all(name in by_name for name in names):
        return None
    endpoints = [f"{ref}.{by_name[name]}" for name in names]
    return "replace with " + ", ".join(endpoints)


def _documented_endpoints(chip: dict) -> set[str]:
    value = chip.get("symbolic_endpoints", [])
    if not isinstance(value, list):
        return set()
    return {str(item) for item in value if isinstance(item, str)}


def audit_circuit_endpoints() -> list[EndpointFinding]:
    packages = _circuit_packages()
    findings: list[EndpointFinding] = []
    for path in _circuit_paths():
        circuit = _load_json(path)
        relative = path.relative_to(ROOT).as_posix()
        symbols = _declared_symbols(circuit)
        chips = {
            str(chip["ref"]): chip
            for chip in circuit.get("chips", [])
            if isinstance(chip, dict) and isinstance(chip.get("ref"), str)
        }
        for index, row in enumerate(circuit.get("wiring", [])):
            if not isinstance(row, dict):
                findings.append(EndpointFinding(relative, index, "", repr(row), "wiring row is not an object", "replace it with an object containing net and connections"))
                continue
            net = row.get("net")
            connections = row.get("connections")
            if not isinstance(net, str) or not net:
                findings.append(EndpointFinding(relative, index, str(net), "", "net is missing or not a string", "declare a non-empty string net"))
                continue
            if not isinstance(connections, list):
                findings.append(EndpointFinding(relative, index, net, repr(connections), "connections is not a list", "replace connections with a list of endpoint strings"))
                continue
            for endpoint_value in connections:
                endpoint = str(endpoint_value)
                if not isinstance(endpoint_value, str) or not endpoint:
                    findings.append(EndpointFinding(relative, index, net, endpoint, "endpoint is not a non-empty string", "use a non-empty endpoint string"))
                    continue
                if endpoint in symbols:
                    continue

                numeric = REAL_PIN_RE.fullmatch(endpoint)
                if numeric:
                    ref = numeric.group("ref")
                    chip = chips.get(ref)
                    if chip is None:
                        findings.append(EndpointFinding(relative, index, net, endpoint, f"chip ref {ref!r} is not declared", f"add {ref!r} to chips or correct the endpoint ref"))
                        continue
                    part = str(chip.get("part", ""))
                    maps = _pin_maps(part)
                    if maps is None:
                        findings.append(EndpointFinding(relative, index, net, endpoint, f"part {part!r} has no DB pin definition", f"add {endpoint.split('.', 1)[1]!r} to chips[{ref!r}].symbolic_endpoints or use a resolvable circuit-package port"))
                        continue
                    by_number, _ = maps
                    start = int(numeric.group("start"))
                    end = int(numeric.group("end") or start)
                    step = 1 if end >= start else -1
                    missing = [pin for pin in range(start, end + step, step) if pin not in by_number]
                    if missing:
                        findings.append(EndpointFinding(relative, index, net, endpoint, f"numeric pin(s) {missing} do not exist on {part}", "replace them with numeric pins present in the DB definition"))
                    continue

                symbolic = SYMBOLIC_REF_RE.fullmatch(endpoint)
                if symbolic:
                    ref = symbolic.group("ref")
                    token = symbolic.group("token")
                    chip = chips.get(ref)
                    if chip is None:
                        findings.append(EndpointFinding(relative, index, net, endpoint, f"chip ref {ref!r} is not declared", f"add {ref!r} to chips or correct the endpoint ref"))
                        continue
                    part = str(chip.get("part", ""))
                    package = packages.get(part)
                    package_ports = _declared_ports(package) if package is not None else set()
                    if token in package_ports or token in _documented_endpoints(chip):
                        continue
                    maps = _pin_maps(part)
                    if maps is not None:
                        _, by_name = maps
                        fix = _numeric_fix(ref, token, by_name) or f"replace with numeric {part} pins from the DB definition"
                        findings.append(EndpointFinding(relative, index, net, endpoint, "real DB chip endpoints must use numeric package pins", fix))
                    else:
                        findings.append(EndpointFinding(relative, index, net, endpoint, f"{token!r} is not a declared port of circuit package {part!r} and is not documented on this chip instance", f"add {token!r} to chips[{ref!r}].symbolic_endpoints or declare the port in {part}/circuit.json"))
                    continue

                findings.append(EndpointFinding(relative, index, net, endpoint, "endpoint is neither a declared symbolic boundary nor a parsed chip endpoint", f"replace it with a declared port/net, a real REF.numeric-pin endpoint, or an explicit chips[].symbolic_endpoints reference"))
    return sorted(findings)


def test_all_lib_circuit_wiring_endpoints_are_explicit_and_resolvable() -> None:
    findings = audit_circuit_endpoints()
    assert not findings, "Unknown or unparsed circuit wiring endpoints:\n" + "\n".join(
        finding.line() for finding in findings
    )


if __name__ == "__main__":
    problems = audit_circuit_endpoints()
    if problems:
        print("\n".join(problem.line() for problem in problems))
        raise SystemExit(1)
    print("All library circuit wiring endpoints are explicit and resolvable")
