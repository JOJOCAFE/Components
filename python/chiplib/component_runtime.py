"""Bounded runtime adapter for validated leaf Resolved Components.

This reuses the Components digital Board kernel.  It deliberately accepts no
raw AST, Board layout, or implicit wiring; declared test-language execution is
still a later Operation contract.
"""
from __future__ import annotations

import re
from typing import Any

from .core import Board, LogicSource, normalize_logic
from .model_loader import ModelLoadError, create_live_db_chip


class ComponentRuntimeError(ValueError):
    pass


class ComponentRuntimeSession:
    def __init__(self, resolved: dict[str, Any]):
        if not resolved.get("ok"):
            raise ComponentRuntimeError("Component must resolve without errors before runtime instantiation")
        self.resolved = resolved
        self.board = Board()
        self.chips: dict[str, Any] = {}
        self.sources: dict[str, LogicSource] = {}
        self.groups: dict[str, str] = {}
        self._build()

    def _build(self) -> None:
        parent: dict[str, str] = {}
        def find(value: str) -> str:
            parent.setdefault(value, value)
            if parent[value] != value: parent[value] = find(parent[value])
            return parent[value]
        def union(left: str, right: str) -> None:
            left, right = find(left), find(right)
            if left != right: parent[right] = left
        def key(endpoint: dict[str, Any]) -> str:
            return f"net:{endpoint['id']}" if endpoint["kind"] == "net" else f"port:{endpoint['instance']}.{endpoint['port']}"
        for edge in self.resolved.get("edges", []): union(key(edge["source_endpoint"]), key(edge["target_endpoint"]))
        for net in self.resolved.get("nets", []): find(f"net:{net['id']}")
        for edge in self.resolved.get("edges", []):
            for endpoint in (edge["source_endpoint"], edge["target_endpoint"]): find(key(endpoint))
        names: dict[str, str] = {}
        for item in list(parent):
            root = find(item)
            if root not in names:
                net = next((n["id"] for n in self.resolved.get("nets", []) if find(f"net:{n['id']}") == root), None)
                names[root] = net or f"component_net_{len(names)}"
            self.groups[item] = names[root]
        for instance in self.resolved.get("instances", []):
            part, ident = instance["part"], instance["id"]
            if part in {"ClockSource", "Probe"}: continue
            try: self.chips[ident] = create_live_db_chip(part, ident)
            except ModelLoadError as exc: raise ComponentRuntimeError(f"{ident} ({part}) is not executable: {exc}") from exc
            self.board.add_chip(ident, self.chips[ident])
        for edge in self.resolved.get("edges", []):
            for endpoint in (edge["source_endpoint"], edge["target_endpoint"]):
                if endpoint["kind"] != "device_port" or endpoint["instance"] not in self.chips: continue
                self.board.connect(self.groups[key(endpoint)], self.chips[endpoint["instance"]], endpoint["pin"])
        for net in self.resolved.get("nets", []):
            if net["kind"] == "power":
                name = self.groups[f"net:{net['id']}"]
                if net["id"].lower() in {"vcc", "vdd", "power"}: self.board.attach_rail("VCC", name)
                elif net["id"].lower() in {"gnd", "ground"}: self.board.attach_rail("GND", name)
        self.board.settle()

    def drive(self, target: str, value: int | str) -> dict[str, Any]:
        key = f"net:{target}" if f"net:{target}" in self.groups else f"port:{target}"
        if key not in self.groups: raise ComponentRuntimeError(f"unknown resolved net or Device port {target!r}")
        source = self.sources.get(target)
        if source is None:
            source = self.board.logic_source(f"operation:{target}", self.groups[key], 0)
            self.sources[target] = source
        logical = int(value) if isinstance(value, str) and value in {"0", "1"} else value
        source.value = normalize_logic(logical); self.board.settle()
        return self.snapshot()

    def probe(self, name: str | None = None) -> dict[str, Any]:
        observations = self.resolved.get("observations", [])
        result: dict[str, Any] = {}
        for item in observations:
            if name and item["id"] != name: continue
            target = item["target"]
            if target in {bus["id"] for bus in self.resolved.get("buses", [])}:
                width = next(bus["width"] for bus in self.resolved["buses"] if bus["id"] == target)
                result[item["id"]] = [self.board.net(self.groups[f"net:{target}[{bit}]"]).value for bit in range(width)]
            else:
                key = f"net:{target}" if f"net:{target}" in self.groups else f"port:{target}"
                result[item["id"]] = self.board.net(self.groups[key]).value
        if name and name not in result: raise ComponentRuntimeError(f"unknown probe/watch {name!r}")
        return {"component_id": self.resolved["component_id"], "time_ns": self.board.time_ns, "probes": result}

    def run_declared_test(self, name: str) -> dict[str, Any]:
        """Run the small, bounded beginner test subset from a resolved test."""
        test = next((item for item in self.resolved.get("tests", []) if item["id"] == name), None)
        if test is None or "text" not in test:
            raise ComponentRuntimeError(f"declared test {name!r} is unavailable")
        actions: list[dict[str, Any]] = []
        text = str(test["text"])
        for statement in re.findall(r"(?:set\s+[^;]+|pulse\s+[^;]+|wait\s+[^;]+|settle|assert\s+[^;]+);", text):
            statement = re.sub(r"^arrange\s*\{\s*", "", statement.strip()).rstrip(";").rstrip("}").strip()
            if statement.startswith("set "):
                match = re.fullmatch(r"set\s+([^\s=]+)\s*=\s*([01ZX])", statement)
                if not match: raise ComponentRuntimeError(f"test {name!r}: use 'set target = 0|1|Z|X'")
                self.drive(match.group(1), match.group(2)); actions.append({"action": "set", "target": match.group(1), "value": match.group(2)})
            elif statement.startswith("pulse "):
                target = statement.removeprefix("pulse ").strip()
                self.drive(target, 0); self.drive(target, 1); self.board.time_ns += 1; self.board.settle(); self.drive(target, 0)
                actions.append({"action": "pulse", "target": target, "width_ns": 1})
            elif statement.startswith("wait "):
                match = re.fullmatch(r"wait\s+(\d+)\s+ns", statement)
                if not match: raise ComponentRuntimeError(f"test {name!r}: wait needs a whole number of ns")
                self.board.time_ns += int(match.group(1)); self.board.settle(); actions.append({"action": "wait", "ns": int(match.group(1))})
            elif statement == "settle":
                self.board.settle(); actions.append({"action": "settle"})
            elif statement.startswith("assert "):
                match = re.fullmatch(r"assert\s+([A-Za-z_][A-Za-z0-9_]*)\s*==\s*([01])", statement)
                if not match: raise ComponentRuntimeError(f"test {name!r}: assert needs 'probe_name == 0|1'")
                actual = self.probe(match.group(1))["probes"][match.group(1)]
                expected = int(match.group(2))
                if actual != expected: raise ComponentRuntimeError(f"test {name!r}: {match.group(1)} expected {expected}, got {actual!r}")
                actions.append({"action": "assert", "probe": match.group(1), "expected": expected, "actual": actual})
        return {"ok": True, "test": name, "actions": actions, "probe": self.probe(), "time_ns": self.board.time_ns}

    def snapshot(self) -> dict[str, Any]:
        return {"format": "components.component-runtime@1", "component_id": self.resolved["component_id"], "time_ns": self.board.time_ns, "board": self.board.snapshot(), "execution_boundary": "digital model only; declared Component tests, Board, and physical signoff remain deferred"}
