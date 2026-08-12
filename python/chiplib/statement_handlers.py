"""Statement handlers — one class per statement kind.

Each handler knows how to resolve its node type against the DB and
produce resolved topology entries. Adding a new statement means adding
a handler here and registering it in HANDLER_REGISTRY at the bottom.

Handlers are stateless — all mutable state lives in ResolutionContext.
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


class StatementHandler:
    """Base class for statement handlers."""

    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        """Resolve this node and register results in context."""
        pass  # Default: no-op (node is stored as-is)


class DeviceHandler(StatementHandler):
    """Resolves device declarations against the chip DB."""

    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        from .db import load_component

        name = node["name"]
        line = node["span"]["line"]
        if not ctx.declare(name, "Device instance", line):
            return

        locator = node["locator"]
        alias, sep, _ = locator.partition(".")
        if not sep or alias not in ctx.imports:
            # Check for unaliased hierarchy references
            if sep and alias.lower() in ("child", "project"):
                ctx.devices[name] = ctx.make_hierarchy_device(node)
                return
            ctx.error("resolver.unknown_import_alias",
                      f"Device locator {locator!r} must start with a declared import alias", line)
            return

        library = ctx.imports[alias]
        # Hierarchy imports skip DB resolution
        if library.startswith("project") or library == "project":
            ctx.devices[name] = ctx.make_hierarchy_device(node)
            return

        part = locator.rsplit(".", 1)[-1]
        try:
            definition = load_component(part)
        except (KeyError, ValueError) as exc:
            ctx.error("resolver.unknown_device", f"cannot resolve {locator!r}: {exc}", line)
            return

        groups = ctx.library_groups.get(library)
        if groups is not None and definition.get("group") not in groups:
            ctx.error("resolver.library_ownership",
                      f"{locator!r} is not owned by imported library {library!r}", line)
            return

        # Validate parameters for virtual devices (relaxed)
        parameters = node.get("parameters") or {}
        if parameters and "period_ns" in parameters:
            if not isinstance(parameters["period_ns"], (int, float)) or parameters["period_ns"] <= 0:
                ctx.error("resolver.invalid_parameter", f"{name!r}.period_ns must be positive", line)

        definition_path = definition.get("db_path")
        raw_definition = (_ROOT / definition_path).read_bytes() if definition_path else b""
        ctx.devices[name] = {
            "id": name, "part": part, "locator": locator,
            "parameters": parameters, "pins": deepcopy(definition.get("pins", [])),
            "definition_path": definition_path,
            "definition_digest": f"sha256:{hashlib.sha256(raw_definition).hexdigest()}",
            "provenance": {"source_span": node["span"], "resolved_definition": definition_path},
        }


class NetHandler(StatementHandler):
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        name = node["name"]
        if not ctx.declare(name, "net", node["span"]["line"]):
            return
        ctx.nets[name] = {"id": name, "kind": node["signal_kind"]}


class BusHandler(StatementHandler):
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
            member_id = f"{name}[{bit}]"
            ctx.nets[member_id] = {"id": member_id, "kind": node["signal_kind"], "bus": name, "bit": bit}


class PortHandler(StatementHandler):
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        name = node["name"]
        line = node["span"]["line"]
        width = node.get("width")
        if width:
            if not ctx.declare(name, "port", line):
                return
            ctx.buses[name] = {"id": name, "width": width, "kind": node["signal_kind"], "port": True}
            for bit in range(width):
                member_id = f"{name}[{bit}]"
                ctx.nets[member_id] = {"id": member_id, "kind": node["signal_kind"], "bus": name, "bit": bit, "port": True}
        else:
            if not ctx.declare(name, "port", line):
                return
            ctx.nets[name] = {"id": name, "kind": node["signal_kind"], "port": True, "direction": node.get("direction")}
        ctx.ports.append({
            "id": name, "width": width, "signal_kind": node["signal_kind"],
            "direction": node.get("direction"), "metadata": node.get("metadata") or {},
        })


class InstanceHandler(StatementHandler):
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        name = node["name"]
        if not ctx.declare(name, "instance", node["span"]["line"]):
            return
        ctx.instances_list.append({"id": name, "source_ref": node["source_ref"],
                                   "provenance": {"source_span": node["span"]}})
        # Register in devices so connect can reference instance.port
        ctx.devices[name] = {
            "id": name, "part": node["source_ref"], "locator": f"instance.{node['source_ref']}",
            "parameters": {}, "pins": [],
            "definition_path": None, "definition_digest": "hierarchy",
            "provenance": {"source_span": node["span"], "resolved_definition": "hierarchy"},
        }


class ConnectHandler(StatementHandler):
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        line = node["span"]["line"]
        source = ctx.resolve_endpoint(node["source"], line)
        target = ctx.resolve_endpoint(node["target"], line)
        if source and target:
            if node["source"] == node["target"]:
                ctx.error("validation.self_connection",
                          f"connection {node['source']!r} cannot target itself", line)
            else:
                ctx.connections.append({
                    "from": node["source"], "to": node["target"],
                    "source_endpoint": source, "target_endpoint": target,
                    "provenance": {"source_span": node["span"]},
                })


class ClockHandler(StatementHandler):
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        ctx.clocks.append({
            "id": node["name"], "endpoint": node["endpoint"],
            "parameters": node.get("parameters") or {},
            "provenance": {"source_span": node["span"]},
        })


class ChannelHandler(StatementHandler):
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        ctx.channels.append({
            "id": node["name"], "endpoint": node["endpoint"],
            "parameters": node.get("parameters") or {},
            "provenance": {"source_span": node["span"]},
        })


class DeriveHandler(StatementHandler):
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        name = node["name"]
        if not ctx.declare(name, "derived signal", node["span"]["line"]):
            return
        ctx.nets[name] = {"id": name, "kind": "digital", "derived": True, "expression": node["expression"]}
        ctx.derives.append({"id": name, "expression": node["expression"],
                           "provenance": {"source_span": node["span"]}})


class ReleaseHandler(StatementHandler):
    """Handles release statements (stimulus — remove driver from endpoint)."""
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        ctx.stimulus.append({
            "kind": "release", "endpoint": node["endpoint"],
            "provenance": {"source_span": node["span"]},
        })


class RepeatHandler(StatementHandler):
    """Handles repeat blocks (bounded iteration)."""
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        ctx.stimulus.append({
            "kind": "repeat", "name": node.get("name"),
            "body": node.get("body", ""),
            "provenance": {"source_span": node["span"]},
        })


class ProbeHandler(StatementHandler):
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        name = node["name"]
        if not ctx.declare(name, "probe", node["span"]["line"]):
            return
        ctx.observations.append({"id": name, "target": node["target"],
                                 "read_only": True, "declared_as": "probe"})


class BusProbeHandler(StatementHandler):
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        ctx.observations.append({"id": node["name"], "target": node["bus"],
                                 "read_only": True, "declared_as": "bus_probe",
                                 "parameters": node.get("parameters") or {}})


class DisplayHandler(StatementHandler):
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        ctx.displays.append({"target": node["target"], "kind": node.get("display_kind"),
                            "options": node.get("options") or {}, "read_only": True})


class TitleHandler(StatementHandler):
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        ctx.title = node.get("value")


class BlockHandler(StatementHandler):
    """Generic handler for block statements (stimulus, safety, test)."""

    def __init__(self, collection: str):
        self.collection = collection

    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        entry = {
            "kind": node["kind"],
            "name": node.get("name"),
            "body": node.get("body", ""),
            "provenance": {"source_span": node["span"]},
        }
        if node.get("after"):
            entry["after"] = node["after"]
        if node.get("text"):
            entry["text"] = node["text"]
        getattr(ctx, self.collection).append(entry)


class TestHandler(StatementHandler):
    def resolve(self, node: JsonMap, ctx: "ResolutionContext") -> None:
        ctx.tests.append({
            "id": node.get("name"),
            "text": node.get("text") or node.get("body", ""),
            "bounded": True,
            "execution": "bounded-component-runtime",
            "provenance": {"source_span": node["span"]},
        })


# ============================================================================
# HANDLER REGISTRY — maps statement kind to handler instance
# ============================================================================

HANDLER_REGISTRY: dict[str, StatementHandler] = {
    "device": DeviceHandler(),
    "net": NetHandler(),
    "bus": BusHandler(),
    "port": PortHandler(),
    "instance": InstanceHandler(),
    "connect": ConnectHandler(),
    "clock": ClockHandler(),
    "channel": ChannelHandler(),
    "derive": DeriveHandler(),
    "release": ReleaseHandler(),
    "repeat": RepeatHandler(),
    "probe": ProbeHandler(),
    "bus_probe": BusProbeHandler(),
    "display": DisplayHandler(),
    "title": TitleHandler(),
    "test": TestHandler(),
    # Block handlers for stimulus and safety
    "input": BlockHandler("stimulus"),
    "reset": BlockHandler("stimulus"),
    "step": BlockHandler("stimulus"),
    "sequence": BlockHandler("stimulus"),
    "memory": BlockHandler("stimulus"),
    "clock_profile": BlockHandler("stimulus"),
    "bus_safety": BlockHandler("safety"),
    "policy": BlockHandler("safety"),
    "edge_criteria": BlockHandler("safety"),
    "timing_check": BlockHandler("safety"),
}
