"""Text-first ``component:component`` parser and resolver.

This is intentionally a small leaf-profile implementation.  It turns the
human-readable Component fixtures into AST and immutable topology JSON, but it
does not execute tests, create Board state, or replace the existing JSON design
and circuit runners.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .db import load_component


JsonMap = dict[str, Any]
_ROOT = Path(__file__).resolve().parents[2]
_HEADER = re.compile(r"component:component\s+([A-Za-z_][A-Za-z0-9_]*)\s+(?:is\s+([A-Za-z_][A-Za-z0-9_.]*))?\s*\{")
_DEVICE = re.compile(r"device\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:is|,)\s*([A-Za-z_][A-Za-z0-9_.]*)(?:\s*,\s*(\{.*\}))?$")
_NET = re.compile(r"net\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([A-Za-z_][A-Za-z0-9_]*)$")
_BUS = re.compile(r"bus\s+([A-Za-z_][A-Za-z0-9_]*)\[(\d+)\]\s*:\s*([A-Za-z_][A-Za-z0-9_]*)$")
_CONNECT = re.compile(r"connect\s+(.+?)\s*->\s*(.+)$")
_OBSERVE = re.compile(r"(probe|watch)\s+([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(.+)$")
_DISPLAY = re.compile(r"display\s+(.+?)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s*,\s*(\{.*\}))?$")
_TITLE = re.compile(r'title\s+("(?:[^"\\]|\\.)*")$')
_BUS_MEMBER = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\[(\d+)\]$")


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    line: int
    severity: str = "error"

    def as_dict(self) -> JsonMap:
        return {"code": self.code, "message": self.message, "severity": self.severity, "span": {"line": self.line}}


def _without_comments(source: str) -> str:
    return "\n".join(line.split("//", 1)[0] for line in source.splitlines())


def _line(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def _span(line: int, text: str) -> JsonMap:
    """A compact, stable source span without making offsets path-dependent."""
    return {"line": line, "end_line": line + text.count("\n")}


def _body_statements(source: str, start: int) -> tuple[list[tuple[str, int]], list[Diagnostic]]:
    """Split top-level Component statements, retaining nested test bodies."""
    items: list[tuple[str, int]] = []
    errors: list[Diagnostic] = []
    depth, statement_start = 1, start
    for index in range(start, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                tail = source[statement_start:index].strip()
                if tail:
                    tail_start = statement_start + len(source[statement_start:index]) - len(source[statement_start:index].lstrip())
                    if tail.startswith("test ") and tail.endswith("}"):
                        items.append((tail, _line(source, tail_start)))
                    else:
                        errors.append(Diagnostic("parser.missing_semicolon", "expected ';' before Component closing brace", _line(source, tail_start)))
                return items, errors
        elif char == ";" and depth == 1:
            text = source[statement_start:index].strip()
            if text:
                item_start = statement_start + len(source[statement_start:index]) - len(source[statement_start:index].lstrip())
                items.append((text, _line(source, item_start)))
            statement_start = index + 1
    errors.append(Diagnostic("parser.unclosed_component", "Component body has no closing '}'", _line(source, start)))
    return items, errors


def parse_component_text(source: str, *, source_name: str = "<memory>") -> JsonMap:
    """Parse the supported Component profile into AST-only JSON."""
    clean = _without_comments(source)
    match = _HEADER.search(clean)
    diagnostics: list[Diagnostic] = []
    if not match:
        diagnostics.append(Diagnostic("parser.component_header", "expected 'component:component Name is profile {'", 1))
        return {"schema": "components.component-ast@1", "source": source_name, "ok": False, "uses": [], "component": None, "diagnostics": [d.as_dict() for d in diagnostics]}
    uses = []
    for use in re.finditer(r"\buse\s+([A-Za-z_][A-Za-z0-9_.]*)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*;", clean):
        uses.append({"kind": "use", "library": use.group(1), "alias": use.group(2), "span": {"line": _line(clean, use.start())}})
    statements, errors = _body_statements(clean, match.end())
    diagnostics.extend(errors)
    nodes: list[JsonMap] = []
    for text, line in statements:
        node: JsonMap = {"kind": "unknown", "text": text, "span": _span(line, text)}
        found = _DEVICE.fullmatch(text)
        if found:
            parameters: JsonMap = {}
            if found.group(3):
                try:
                    parameters = json.loads(found.group(3))
                except json.JSONDecodeError:
                    diagnostics.append(Diagnostic("parser.device_parameters", "Device parameters must be a JSON object", line))
                if not isinstance(parameters, dict):
                    diagnostics.append(Diagnostic("parser.device_parameters", "Device parameters must be a JSON object", line))
                    parameters = {}
            node = {"kind": "device", "name": found.group(1), "locator": found.group(2), "parameters": parameters, "span": _span(line, text)}
        elif (found := _NET.fullmatch(text)):
            node = {"kind": "net", "name": found.group(1), "signal_kind": found.group(2), "span": _span(line, text)}
        elif (found := _BUS.fullmatch(text)):
            node = {"kind": "bus", "name": found.group(1), "width": int(found.group(2)), "signal_kind": found.group(3), "span": _span(line, text)}
        elif (found := _CONNECT.fullmatch(text)):
            node = {"kind": "connect", "source": found.group(1).strip(), "target": found.group(2).strip(), "span": _span(line, text)}
        elif (found := _OBSERVE.fullmatch(text)):
            node = {"kind": found.group(1), "name": found.group(2), "target": found.group(3).strip(), "span": _span(line, text)}
        elif (found := _DISPLAY.match(text)):
            options: JsonMap = {}
            if found.group(3):
                try:
                    options = json.loads(found.group(3))
                except json.JSONDecodeError:
                    diagnostics.append(Diagnostic("parser.display_options", "display options must be a JSON object", line))
            node = {"kind": "display", "target": found.group(1).strip(), "display_kind": found.group(2), "options": options, "span": _span(line, text)}
        elif text.startswith("test "):
            test_name = re.match(r"test\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{", text)
            if not test_name:
                diagnostics.append(Diagnostic("parser.test_declaration", "test requires an identifier and body", line))
            node = {"kind": "test", "name": test_name.group(1) if test_name else None, "text": text, "span": _span(line, text), "execution": "deferred-operation-runtime"}
        elif (found := _TITLE.fullmatch(text)):
            node = {"kind": "title", "value": json.loads(found.group(1)), "span": _span(line, text)}
        else:
            diagnostics.append(Diagnostic("parser.unsupported_statement", f"unsupported Component statement: {text.split()[0]!r}", line))
        nodes.append(node)
    component = {"kind": "component", "name": match.group(1), "profile": match.group(2), "body": nodes, "span": _span(_line(clean, match.start()), match.group(0))}
    return {"schema": "components.component-ast@1", "source": source_name, "ok": not diagnostics, "uses": uses, "component": component, "diagnostics": [d.as_dict() for d in diagnostics]}


def parse_component_file(path: str | Path) -> JsonMap:
    file_path = Path(path)
    return parse_component_text(file_path.read_text(encoding="utf-8"), source_name=str(file_path))


def _part(locator: str) -> str:
    return locator.rsplit(".", 1)[-1]


def _endpoint(token: str, *, nets: dict[str, JsonMap], buses: dict[str, JsonMap], devices: dict[str, JsonMap], line: int, diagnostics: list[Diagnostic]) -> JsonMap | None:
    if token in nets:
        return {"kind": "net", "id": token, "signal_kind": nets[token]["kind"]}
    if token in buses:
        diagnostics.append(Diagnostic("topology.width_mismatch", f"{token!r} is a bus; choose an explicit member such as {token}[0]", line))
        return None
    if (member := _BUS_MEMBER.fullmatch(token)) and member.group(1) in buses:
        diagnostics.append(Diagnostic("topology.bus_member_out_of_range", f"{token!r} is outside declared bus {member.group(1)!r}", line))
        return None
    if "." not in token:
        diagnostics.append(Diagnostic("resolver.unknown_endpoint", f"unknown net or endpoint {token!r}", line))
        return None
    instance, selector = token.split(".", 1)
    device = devices.get(instance)
    if device is None:
        diagnostics.append(Diagnostic("resolver.unknown_device", f"unknown Device instance {instance!r}", line))
        return None
    pins = device["pins"]
    if selector.startswith("@"):
        try:
            number = int(selector[1:])
        except ValueError:
            number = -1
        pin = next((pin for pin in pins if pin.get("number") == number), None)
        if pin is None:
            diagnostics.append(Diagnostic("resolver.unknown_physical_pin", f"{instance} has no physical pin {selector}", line))
            return None
    else:
        pin = next((pin for pin in pins if pin.get("name") == selector), None)
        if pin is None:
            diagnostics.append(Diagnostic("resolver.unknown_port", f"{instance} has no port {selector!r}", line))
            return None
    return {"kind": "device_port", "instance": instance, "port": pin["name"], "pin": pin["number"], "direction": pin["direction"]}


def resolve_component(ast: JsonMap) -> JsonMap:
    """Resolve a parsed leaf Component against active Components DB records."""
    diagnostics = [Diagnostic(item["code"], item["message"], item.get("span", {}).get("line", 1), item.get("severity", "error")) for item in ast.get("diagnostics", [])]
    component = ast.get("component")
    if not ast.get("ok") or not isinstance(component, dict):
        return {"schema": "components.resolved-component@1", "ok": False, "source": ast.get("source"), "diagnostics": [d.as_dict() for d in diagnostics]}
    nets: dict[str, JsonMap] = {}
    buses: dict[str, JsonMap] = {}
    devices: dict[str, JsonMap] = {}
    observations: list[JsonMap] = []
    displays: list[JsonMap] = []
    connections: list[JsonMap] = []
    tests: list[JsonMap] = []
    for node in component["body"]:
        kind, line = node["kind"], node["span"]["line"]
        if kind == "device":
            if node["name"] in devices:
                diagnostics.append(Diagnostic("resolver.duplicate_symbol", f"duplicate Device instance {node['name']!r}", line)); continue
            part = _part(node["locator"])
            try:
                definition = load_component(part)
            except (KeyError, ValueError) as exc:
                diagnostics.append(Diagnostic("resolver.unknown_device", f"cannot resolve {node['locator']!r}: {exc}", line)); continue
            parameters = node.get("parameters", {})
            if parameters:
                # The virtual clock's published period is the sole leaf
                # profile parameter currently represented by active records.
                allowed = {"period_ns"} if part == "ClockSource" else set()
                unknown = sorted(set(parameters) - allowed)
                if unknown:
                    diagnostics.append(Diagnostic("resolver.unknown_parameter", f"{node['name']!r} has unsupported parameter(s): {', '.join(unknown)}", line))
                if "period_ns" in parameters and (not isinstance(parameters["period_ns"], (int, float)) or parameters["period_ns"] <= 0):
                    diagnostics.append(Diagnostic("resolver.invalid_parameter", f"{node['name']!r}.period_ns must be positive", line))
            definition_path = definition.get("db_path")
            raw_definition = (_ROOT / definition_path).read_bytes() if definition_path else b""
            devices[node["name"]] = {
                "id": node["name"], "part": part, "locator": node["locator"],
                "parameters": parameters, "pins": deepcopy(definition.get("pins", [])),
                "definition_path": definition_path,
                "definition_digest": f"sha256:{hashlib.sha256(raw_definition).hexdigest()}",
                "provenance": {"source_span": node["span"], "resolved_definition": definition_path},
            }
        elif kind == "net":
            if node["name"] in nets or node["name"] in buses:
                diagnostics.append(Diagnostic("resolver.duplicate_symbol", f"duplicate net {node['name']!r}", line)); continue
            nets[node["name"]] = {"id": node["name"], "kind": node["signal_kind"]}
        elif kind == "bus":
            if node["name"] in nets or node["name"] in buses:
                diagnostics.append(Diagnostic("resolver.duplicate_symbol", f"duplicate bus {node['name']!r}", line)); continue
            buses[node["name"]] = {"id": node["name"], "width": node["width"], "kind": node["signal_kind"]}
            for bit in range(node["width"]):
                nets[f"{node['name']}[{bit}]"] = {"id": f"{node['name']}[{bit}]", "kind": node["signal_kind"], "bus": node["name"], "bit": bit}
        elif kind in {"probe", "watch"}:
            observations.append({"id": node["name"], "target": node["target"], "read_only": True, "declared_as": kind})
        elif kind == "display":
            displays.append({"target": node["target"], "kind": node["display_kind"], "read_only": True})
        elif kind == "test":
            tests.append({"id": node["name"], "bounded": True, "execution": "deferred-operation-runtime", "provenance": {"source_span": node["span"]}})
    for node in component["body"]:
        if node["kind"] != "connect":
            continue
        line = node["span"]["line"]
        source = _endpoint(node["source"], nets=nets, buses=buses, devices=devices, line=line, diagnostics=diagnostics)
        target = _endpoint(node["target"], nets=nets, buses=buses, devices=devices, line=line, diagnostics=diagnostics)
        if source and target:
            connections.append({"from": node["source"], "to": node["target"], "source_endpoint": source, "target_endpoint": target, "provenance": {"source_span": node["span"]}})
    for observation in observations:
        # A probe/watch may observe an ordered bus as one read-only value.  A
        # connection may not use that shorthand because it would hide bit
        # mapping, so bus expansion remains forbidden in ``connect``.
        if observation["target"] not in buses:
            _endpoint(observation["target"], nets=nets, buses=buses, devices=devices, line=component["span"]["line"], diagnostics=diagnostics)
    for display in displays:
        if display["target"] not in {item["id"] for item in observations}:
            diagnostics.append(Diagnostic("schema.display_requires_probe_or_read_only_endpoint", f"display target {display['target']!r} must name a probe/watch", component["span"]["line"]))
    _validate_topology(nets, connections, diagnostics)
    library_lock = [{"instance": device["id"], "locator": device["locator"], "resolved_definition": device["definition_path"], "definition_digest": device["definition_digest"]} for device in devices.values()]
    output_devices = [{key: value for key, value in device.items() if key != "pins"} for device in devices.values()]
    return {"schema": "components.resolved-component@1", "schema_version": 1, "ok": not any(d.severity == "error" for d in diagnostics), "source": ast.get("source"), "component_id": component["name"], "profile": component.get("profile"), "library_lock": library_lock, "instances": output_devices, "nets": list(nets.values()), "buses": list(buses.values()), "edges": connections, "observations": observations, "display_bindings": displays, "tests": tests, "diagnostics": [d.as_dict() for d in diagnostics], "execution": "deferred-operation-runtime", "provenance": {"ast_schema": ast.get("schema"), "component_span": component["span"]}}


def _validate_topology(nets: dict[str, JsonMap], connections: list[JsonMap], diagnostics: list[Diagnostic]) -> None:
    """Run only static leaf-profile checks; runtime contention stays deferred."""
    attached: dict[str, list[JsonMap]] = {net_id: [] for net_id in nets}
    for edge in connections:
        for endpoint in (edge["source_endpoint"], edge["target_endpoint"]):
            if endpoint["kind"] == "net":
                continue
            other = edge["target_endpoint"] if endpoint is edge["source_endpoint"] else edge["source_endpoint"]
            if other["kind"] == "net":
                attached[other["id"]].append(endpoint)
    for net_id, endpoints in attached.items():
        net = nets[net_id]
        line = 1
        if net["kind"] == "power" and any(endpoint["direction"] != "power" for endpoint in endpoints):
            diagnostics.append(Diagnostic("validation.power_isolation", f"power net {net_id!r} may connect only to power ports", line))
        outputs = [endpoint for endpoint in endpoints if endpoint["direction"] == "output"]
        if len(outputs) > 1:
            names = ", ".join(f"{item['instance']}.{item['port']}" for item in outputs)
            diagnostics.append(Diagnostic("validation.output_ownership", f"net {net_id!r} has multiple output owners: {names}", line))


def component_ide_snapshot(path: str | Path) -> JsonMap:
    """Return a text-IDE friendly, serializable source/AST/resolution snapshot."""
    ast = parse_component_file(path)
    resolved = resolve_component(ast)
    return {"format": "components.text_ide@1", "ok": bool(resolved.get("ok")), "source": ast.get("source"), "ast": ast, "resolved": resolved, "capabilities": {"parse": True, "resolve": True, "validate": True, "run": False, "board": False}, "next": "Fix diagnostics, then use the existing JSON circuit runner for executable packages; Component Runtime execution is deferred."}
