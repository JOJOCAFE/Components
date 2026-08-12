"""
Component Language — Statement Handlers
========================================

One handler class per statement kind.  Each handler knows how to resolve
its node type against the chip DB and register results in the ResolutionContext.

HOW TO ADD A NEW HANDLER
-------------------------

1. Create a class that inherits from StatementHandler:

    class MyHandler(StatementHandler):
        def resolve(self, node, ctx):
            # node = parsed AST node (dict with "kind", "name", "span", etc.)
            # ctx  = ResolutionContext (has .nets, .devices, .connections, etc.)
            ctx.stimulus.append({"kind": "my_thing", ...})

2. Register it at the bottom of this file:

    HANDLER_REGISTRY["my_keyword"] = MyHandler()
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .resolver_engine import ResolutionContext

JsonMap = dict[str, Any]
_ROOT = Path(__file__).resolve().parents[2]


# =============================================================================
# BASE CLASS
# =============================================================================

class StatementHandler:
    """Base class.  Override resolve() to handle a specific statement kind."""

    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        """Process this node and update the resolution context."""
        pass


# =============================================================================
# TOPOLOGY HANDLERS
# =============================================================================

class DeviceHandler(StatementHandler):
    """Resolves `device Name, Library.Part, {params};` against the chip DB."""

    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        from .db import load_component

        name = node["name"]
        line = node["span"]["line"]
        if not ctx.declare(name, "Device instance", line):
            return

        locator = node["locator"]
        alias, sep, _ = locator.partition(".")

        # Unaliased hierarchy references (child.X, project.X)
        if sep and alias.lower() in ("child", "project"):
            ctx.devices[name] = ctx.make_hierarchy_device(node)
            return

        # Must start with a declared import alias
        if not sep or alias not in ctx.imports:
            ctx.error("resolver.unknown_import_alias",
                      f"Device locator {locator!r} must start with a declared import alias", line)
            return

        library = ctx.imports[alias]

        # Hierarchy imports skip DB resolution
        if library.startswith("project") or library == "project":
            ctx.devices[name] = ctx.make_hierarchy_device(node)
            return

        # Resolve part from DB
        part = locator.rsplit(".", 1)[-1]
        try:
            definition = load_component(part)
        except (KeyError, ValueError) as exc:
            ctx.error("resolver.unknown_device", f"cannot resolve {locator!r}: {exc}", line)
            return

        # Verify library ownership
        groups = ctx.library_groups.get(library)
        if groups is not None and definition.get("group") not in groups:
            ctx.error("resolver.library_ownership",
                      f"{locator!r} is not owned by imported library {library!r}", line)
            return

        # Validate parameters (minimal — only catch clearly wrong values)
        parameters = node.get("parameters") or {}
        if "period_ns" in parameters:
            val = parameters["period_ns"]
            if not isinstance(val, (int, float)) or val <= 0:
                ctx.error("resolver.invalid_parameter",
                          f"{name!r}.period_ns must be positive", line)

        # Register device with resolved definition
        definition_path = definition.get("db_path")
        raw = (_ROOT / definition_path).read_bytes() if definition_path else b""
        ctx.devices[name] = {
            "id": name,
            "part": part,
            "locator": locator,
            "parameters": parameters,
            "pins": deepcopy(definition.get("pins", [])),
            "definition_path": definition_path,
            "definition_digest": f"sha256:{hashlib.sha256(raw).hexdigest()}",
            "provenance": {"source_span": node["span"],
                          "resolved_definition": definition_path},
        }


class NetHandler(StatementHandler):
    """Resolves `net name : kind;`."""

    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        name = node["name"]
        if not ctx.declare(name, "net", node["span"]["line"]):
            return
        ctx.nets[name] = {"id": name, "kind": node["signal_kind"]}


class BusHandler(StatementHandler):
    """Resolves `bus name[width] : kind;` — creates bus + member nets."""

    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        name = node["name"]
        line = node["span"]["line"]
        if not ctx.declare(name, "bus", line):
            return
        width = node["width"]
        if width < 1:
            ctx.error("validation.bus_width", f"bus {name!r} must have width >= 1", line)
            return
        ctx.buses[name] = {"id": name, "width": width, "kind": node["signal_kind"]}
        for bit in range(width):
            member = f"{name}[{bit}]"
            ctx.nets[member] = {"id": member, "kind": node["signal_kind"],
                               "bus": name, "bit": bit}


class PortHandler(StatementHandler):
    """Resolves `port name[width] : kind, direction;` — creates boundary nets."""

    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        name = node["name"]
        line = node["span"]["line"]
        width = node.get("width")

        if not ctx.declare(name, "port", line):
            return

        if width:
            ctx.buses[name] = {"id": name, "width": width,
                              "kind": node["signal_kind"], "port": True}
            for bit in range(width):
                member = f"{name}[{bit}]"
                ctx.nets[member] = {"id": member, "kind": node["signal_kind"],
                                   "bus": name, "bit": bit, "port": True}
        else:
            ctx.nets[name] = {"id": name, "kind": node["signal_kind"],
                             "port": True, "direction": node.get("direction")}

        ctx.ports.append({
            "id": name, "width": width,
            "signal_kind": node["signal_kind"],
            "direction": node.get("direction"),
            "metadata": node.get("metadata") or {},
        })


class InstanceHandler(StatementHandler):
    """Resolves `instance name, Ref;` — registers a hierarchy sub-circuit."""

    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        name = node["name"]
        if not ctx.declare(name, "instance", node["span"]["line"]):
            return
        ctx.instances_list.append({
            "id": name, "source_ref": node["source_ref"],
            "provenance": {"source_span": node["span"]},
        })
        # Register in devices so connect can reference instance.port
        ctx.devices[name] = {
            "id": name, "part": node["source_ref"],
            "locator": f"instance.{node['source_ref']}",
            "parameters": {}, "pins": [],
            "definition_path": None, "definition_digest": "hierarchy",
            "provenance": {"source_span": node["span"],
                          "resolved_definition": "hierarchy"},
        }


class ConnectHandler(StatementHandler):
    """Resolves `connect source -> target;` — validates endpoints and creates edges."""

    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        line = node["span"]["line"]
        src = ctx.resolve_endpoint(node["source"], line)
        tgt = ctx.resolve_endpoint(node["target"], line)
        if src and tgt:
            if node["source"] == node["target"]:
                ctx.error("validation.self_connection",
                          f"connection {node['source']!r} cannot target itself", line)
            else:
                ctx.connections.append({
                    "from": node["source"], "to": node["target"],
                    "source_endpoint": src, "target_endpoint": tgt,
                    "provenance": {"source_span": node["span"]},
                })


# =============================================================================
# STIMULUS HANDLERS
# =============================================================================

class ClockHandler(StatementHandler):
    """Resolves `clock name, endpoint, {params};`."""
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        ctx.clocks.append({
            "id": node["name"], "endpoint": node["endpoint"],
            "parameters": node.get("parameters") or {},
            "provenance": {"source_span": node["span"]},
        })


class ChannelHandler(StatementHandler):
    """Resolves `channel name, endpoint, {params};`."""
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        ctx.channels.append({
            "id": node["name"], "endpoint": node["endpoint"],
            "parameters": node.get("parameters") or {},
            "provenance": {"source_span": node["span"]},
        })


class DeriveHandler(StatementHandler):
    """Resolves `derive name = expression;` — creates a read-only computed net."""
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        name = node["name"]
        if not ctx.declare(name, "derived signal", node["span"]["line"]):
            return
        ctx.nets[name] = {"id": name, "kind": "digital",
                         "derived": True, "expression": node["expression"]}
        ctx.derives.append({
            "id": name, "expression": node["expression"],
            "provenance": {"source_span": node["span"]},
        })


class ReleaseHandler(StatementHandler):
    """Resolves `release endpoint;` — marks endpoint for tri-state release."""
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        ctx.stimulus.append({
            "kind": "release", "endpoint": node["endpoint"],
            "provenance": {"source_span": node["span"]},
        })


class RepeatHandler(StatementHandler):
    """Resolves `repeat count { body }` — bounded iteration block."""
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        ctx.stimulus.append({
            "kind": "repeat", "name": node.get("name"),
            "body": node.get("body", ""),
            "provenance": {"source_span": node["span"]},
        })


# =============================================================================
# OBSERVATION HANDLERS
# =============================================================================

class ProbeHandler(StatementHandler):
    """Resolves `probe name, target;` — read-only observation point."""
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        name = node["name"]
        if not ctx.declare(name, "probe", node["span"]["line"]):
            return
        ctx.observations.append({
            "id": name, "target": node["target"],
            "read_only": True, "declared_as": "probe",
        })


class BusProbeHandler(StatementHandler):
    """Resolves `bus_probe name, bus, {params};` — bus observation with policy."""
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        ctx.observations.append({
            "id": node["name"], "target": node["bus"],
            "read_only": True, "declared_as": "bus_probe",
            "parameters": node.get("parameters") or {},
        })


class DisplayHandler(StatementHandler):
    """Resolves `display target as kind, {opts};` — presentation binding."""
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        ctx.displays.append({
            "target": node["target"],
            "kind": node.get("display_kind"),
            "options": node.get("options") or {},
            "read_only": True,
        })


# =============================================================================
# META & BLOCK HANDLERS
# =============================================================================

class TitleHandler(StatementHandler):
    """Resolves `title "text";`."""
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        ctx.title = node.get("value")


class TestHandler(StatementHandler):
    """Resolves `test name { body }` — stores bounded test for deferred execution."""
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        ctx.tests.append({
            "id": node.get("name"),
            "text": node.get("text") or node.get("body", ""),
            "bounded": True,
            "execution": "bounded-component-runtime",
            "provenance": {"source_span": node["span"]},
        })


class BlockHandler(StatementHandler):
    """Generic handler for block statements (stores body for deferred runtime).

    Used for: input, reset, step, sequence, memory, clock_profile,
    bus_safety, policy, edge_criteria, timing_check.
    """

    def __init__(self, collection: str):
        """
        Args:
            collection: Name of the ctx attribute to append to
                        ("stimulus" or "safety")
        """
        self.collection = collection

    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        entry: JsonMap = {
            "kind": node["kind"],
            "name": node.get("name"),
            "body": node.get("body", ""),
            "provenance": {"source_span": node["span"]},
        }
        if node.get("after"):
            entry["after"] = node["after"]
        getattr(ctx, self.collection).append(entry)


# =============================================================================
# HANDLER REGISTRY — maps statement kind → handler instance
# =============================================================================

HANDLER_REGISTRY: dict[str, StatementHandler] = {
    # Topology
    "device":   DeviceHandler(),
    "net":      NetHandler(),
    "bus":      BusHandler(),
    "port":     PortHandler(),
    "instance": InstanceHandler(),
    "connect":  ConnectHandler(),

    # Stimulus (single-line)
    "clock":    ClockHandler(),
    "channel":  ChannelHandler(),
    "derive":   DeriveHandler(),
    "release":  ReleaseHandler(),
    "repeat":   RepeatHandler(),

    # Observation
    "probe":     ProbeHandler(),
    "bus_probe": BusProbeHandler(),
    "display":   DisplayHandler(),

    # Meta
    "title": TitleHandler(),
    "test":  TestHandler(),

    # Block statements → deferred to runtime
    "input":         BlockHandler("stimulus"),
    "reset":         BlockHandler("stimulus"),
    "step":          BlockHandler("stimulus"),
    "sequence":      BlockHandler("stimulus"),
    "memory":        BlockHandler("stimulus"),
    "clock_profile": BlockHandler("stimulus"),
    "bus_safety":    BlockHandler("safety"),
    "policy":        BlockHandler("safety"),
    "edge_criteria": BlockHandler("safety"),
    "timing_check":  BlockHandler("safety"),
}
