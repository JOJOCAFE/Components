"""Component resolver engine — ResolutionContext and dispatch.

The resolver takes a parsed AST and validates it against the chip DB,
building an immutable resolved topology. It dispatches each node to its
registered handler, which mutates the context.

To add support for a new statement kind: add a handler to
statement_handlers.py and register it in HANDLER_REGISTRY. This file
never changes.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .parser_engine import Diagnostic
from .statement_handlers import HANDLER_REGISTRY

JsonMap = dict[str, Any]
_BUS_MEMBER_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\[(\d+)\]$")

# Library namespace -> DB group mapping
LIBRARY_GROUPS: dict[str, set[str] | None] = {
    "standard.digital": {"74xx"},
    "standard.memory": {"memory"},
    "standard.virtual": {"virtual"},
    "standard.passive": {"passive"},
    "standard.discrete": {"discrete"},
    "standard.support": {"support"},
    "project": None,
}


class ResolutionContext:
    """Mutable context that accumulates resolved topology during resolution."""

    def __init__(self, ast: JsonMap):
        self.ast = ast
        self.diagnostics: list[Diagnostic] = []
        self.imports: dict[str, str] = {}
        self.library_groups = LIBRARY_GROUPS

        # Topology collections
        self.devices: dict[str, JsonMap] = {}
        self.nets: dict[str, JsonMap] = {}
        self.buses: dict[str, JsonMap] = {}
        self.ports: list[JsonMap] = []
        self.instances_list: list[JsonMap] = []
        self.connections: list[JsonMap] = []

        # Observation
        self.observations: list[JsonMap] = []
        self.displays: list[JsonMap] = []

        # Stimulus & safety (deferred to runtime)
        self.clocks: list[JsonMap] = []
        self.channels: list[JsonMap] = []
        self.derives: list[JsonMap] = []
        self.stimulus: list[JsonMap] = []
        self.safety: list[JsonMap] = []
        self.tests: list[JsonMap] = []

        # Meta
        self.title: str | None = None

        # Load prior diagnostics from parse phase
        for item in ast.get("diagnostics", []):
            self.diagnostics.append(Diagnostic(
                item["code"], item["message"],
                item.get("span", {}).get("line", 1),
                item.get("severity", "error"),
            ))

    def declare(self, name: str, category: str, line: int) -> bool:
        """Check uniqueness in the local namespace."""
        if name in self.devices or name in self.nets or name in self.buses:
            self.error("resolver.duplicate_symbol", f"duplicate {category} symbol {name!r}", line)
            return False
        if any(item["id"] == name for item in self.observations):
            self.error("resolver.duplicate_symbol", f"duplicate {category} symbol {name!r}", line)
            return False
        if name in self.imports:
            self.error("resolver.local_shadows_import", f"{category} symbol {name!r} shadows import alias", line)
            return False
        return True

    def error(self, code: str, message: str, line: int) -> None:
        self.diagnostics.append(Diagnostic(code, message, line, "error"))

    def warn(self, code: str, message: str, line: int) -> None:
        self.diagnostics.append(Diagnostic(code, message, line, "warning"))

    def make_hierarchy_device(self, node: JsonMap) -> JsonMap:
        """Create a device entry for hierarchy references (no DB resolution)."""
        return {
            "id": node["name"], "part": node["locator"].rsplit(".", 1)[-1],
            "locator": node["locator"],
            "parameters": node.get("parameters") or {}, "pins": [],
            "definition_path": None, "definition_digest": "hierarchy",
            "provenance": {"source_span": node["span"], "resolved_definition": "hierarchy"},
        }

    def resolve_endpoint(self, token: str, line: int) -> JsonMap | None:
        """Resolve a connection endpoint to a typed reference."""
        # Net reference
        if token in self.nets:
            return {"kind": "net", "id": token, "signal_kind": self.nets[token]["kind"]}

        # Bus reference (bus-to-bus shorthand)
        if token in self.buses:
            return {"kind": "bus", "id": token, "signal_kind": self.buses[token]["kind"],
                    "width": self.buses[token]["width"]}

        # Bus member reference
        if (m := _BUS_MEMBER_RE.fullmatch(token)):
            bus_name, bit = m.group(1), int(m.group(2))
            if bus_name in self.buses:
                if bit < self.buses[bus_name]["width"]:
                    member_id = f"{bus_name}[{bit}]"
                    if member_id in self.nets:
                        return {"kind": "net", "id": member_id, "signal_kind": self.nets[member_id]["kind"]}
                else:
                    self.error("topology.bus_member_out_of_range",
                              f"{token!r} exceeds bus {bus_name!r} width {self.buses[bus_name]['width']}", line)
                    return None

        # Power rail
        if token.lower() in ("vcc", "gnd"):
            return {"kind": "net", "id": token, "signal_kind": "power"}

        # Device port reference (INSTANCE.PORT)
        if "." not in token:
            self.error("resolver.unknown_endpoint", f"unknown net or endpoint {token!r}", line)
            return None

        instance, selector = token.split(".", 1)
        device = self.devices.get(instance)
        if device is None:
            self.error("resolver.unknown_device", f"unknown Device instance {instance!r}", line)
            return None

        # Hierarchy devices accept any selector
        if not device.get("pins"):
            return {"kind": "device_port", "instance": instance, "port": selector, "pin": 0, "direction": "inout"}

        # Virtual bus devices accept indexed selectors
        if device.get("part") in ("BusProbe", "BusDriver", "SequenceGenerator", "LogicAnalyzer"):
            return {"kind": "device_port", "instance": instance, "port": selector, "pin": 0, "direction": "inout"}

        # Handle quoted selectors
        if selector.startswith('"'):
            try:
                selector = json.loads(selector)
            except json.JSONDecodeError:
                self.error("resolver.invalid_port_selector", f"invalid quoted selector {selector!r}", line)
                return None

        # Physical pin selector (@N)
        pins = device["pins"]
        if selector.startswith("@"):
            try:
                number = int(selector[1:])
            except ValueError:
                number = -1
            pin = next((p for p in pins if p.get("number") == number), None)
            if pin is None:
                self.error("resolver.unknown_physical_pin", f"{instance} has no physical pin {selector}", line)
                return None
            return {"kind": "device_port", "instance": instance, "port": pin["name"],
                    "pin": pin["number"], "direction": pin["direction"]}

        # Named port lookup
        pin = next((p for p in pins if p.get("name") == selector), None)
        if pin:
            return {"kind": "device_port", "instance": instance, "port": pin["name"],
                    "pin": pin["number"], "direction": pin["direction"]}

        # Bus-port prefix shorthand (e.g., A for A0-A14)
        has_prefix_pins = any(p.get("name", "").startswith(selector) for p in pins)
        if has_prefix_pins or len(selector) <= 2:
            return {"kind": "device_port", "instance": instance, "port": selector, "pin": 0, "direction": "inout"}

        self.error("resolver.unknown_port", f"{instance} has no port {selector!r}", line)
        return None

    def to_resolved(self) -> JsonMap:
        """Build the final resolved-component JSON."""
        component = self.ast.get("component", {})
        library_lock = [
            {"instance": d["id"], "locator": d["locator"],
             "resolved_definition": d["definition_path"], "definition_digest": d["definition_digest"]}
            for d in self.devices.values() if d.get("definition_path")
        ]
        output_devices = [{k: v for k, v in d.items() if k != "pins"} for d in self.devices.values()]

        return {
            "schema": "components.resolved-component@1",
            "schema_version": 1,
            "ok": not any(d.severity == "error" for d in self.diagnostics),
            "source": self.ast.get("source"),
            "component_id": component.get("name"),
            "profile": component.get("profile"),
            "library_lock": library_lock,
            "ports": self.ports,
            "instances": output_devices + self.instances_list,
            "nets": list(self.nets.values()),
            "buses": list(self.buses.values()),
            "edges": self.connections,
            "observations": self.observations,
            "display_bindings": self.displays,
            "tests": self.tests,
            "clocks": self.clocks,
            "channels": self.channels,
            "derives": self.derives,
            "stimulus": self.stimulus,
            "safety": self.safety,
            "diagnostics": [d.as_dict() for d in self.diagnostics],
            "execution": "deferred-operation-runtime",
            "provenance": {"ast_schema": self.ast.get("schema"),
                          "component_span": component.get("span")},
        }


def resolve(ast: JsonMap) -> JsonMap:
    """Resolve a parsed Component AST against the DB.

    Main entry point for the resolver engine.
    """
    component = ast.get("component")
    if not ast.get("ok") or not isinstance(component, dict):
        return {
            "schema": "components.resolved-component@1",
            "ok": False,
            "source": ast.get("source"),
            "diagnostics": ast.get("diagnostics", []),
        }

    ctx = ResolutionContext(ast)

    # Process imports
    for use in ast.get("uses", []):
        alias = use.get("alias")
        library = use.get("library")
        line = use.get("span", {}).get("line", 1)
        if not alias or not library:
            ctx.error("resolver.import_alias_required", "require 'use Library as alias;'", line)
        elif alias in ctx.imports:
            ctx.error("resolver.duplicate_import_alias", f"duplicate import alias {alias!r}", line)
        else:
            ctx.imports[alias] = library

    # Pass 1: Declarations (everything except connect)
    for node in component["body"]:
        kind = node["kind"]
        if kind == "connect":
            continue  # Defer to pass 2
        handler = HANDLER_REGISTRY.get(kind)
        if handler:
            handler.resolve(node, ctx)
        # Unknown kinds are silently ignored (already flagged by parser)

    # Pass 2: Connections (after all nets/devices/derives are registered)
    for node in component["body"]:
        if node["kind"] == "connect":
            HANDLER_REGISTRY["connect"].resolve(node, ctx)

    # Pass 3: Validate observations and displays
    for obs in ctx.observations:
        target = obs["target"]
        if target not in ctx.buses:
            ctx.resolve_endpoint(target, component["span"]["line"])

    known_targets = {item["id"] for item in ctx.observations} | {d["id"] for d in ctx.derives}
    for display in ctx.displays:
        if display["target"] not in known_targets:
            ctx.error("schema.display_requires_probe",
                      f"display target {display['target']!r} must name a probe/watch or derive",
                      component["span"]["line"])

    # Pass 4: Topology validation
    _validate_topology(ctx)

    return ctx.to_resolved()


def _validate_topology(ctx: ResolutionContext) -> None:
    """Static topology checks (output ownership, power isolation)."""
    attached: dict[str, list[JsonMap]] = {net_id: [] for net_id in ctx.nets}
    for edge in ctx.connections:
        for endpoint in (edge["source_endpoint"], edge["target_endpoint"]):
            if endpoint["kind"] == "net":
                if endpoint["id"] in attached:
                    attached[endpoint["id"]].append(endpoint)
            elif endpoint["kind"] == "device_port":
                other = edge["target_endpoint"] if endpoint is edge["source_endpoint"] else edge["source_endpoint"]
                if other["kind"] == "net" and other["id"] in attached:
                    attached[other["id"]].append(endpoint)

    for net_id, endpoints in attached.items():
        net = ctx.nets[net_id]
        if net["kind"] == "power":
            non_power = [ep for ep in endpoints if ep.get("direction") not in ("power", "input", "inout", None)]
            if non_power:
                ctx.error("validation.power_isolation",
                          f"power net {net_id!r} may connect only to power or input ports", 1)
        outputs = [ep for ep in endpoints if ep.get("direction") == "output"]
        if len(outputs) > 1:
            names = ", ".join(f"{item['instance']}.{item['port']}" for item in outputs)
            ctx.error("validation.output_ownership",
                      f"net {net_id!r} has multiple output owners: {names}", 1)
