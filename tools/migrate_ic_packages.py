#!/usr/bin/env python3
"""Migrate legacy IC chip.json manifests to standalone package folders."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil

from chiplib.db import generate_component_artifacts, load_component


ROOT = Path(__file__).resolve().parents[1]
PARTS = [
    "74HC00",
    "74HC04",
    "74HC21",
    "74HC32",
    "74HC74",
    "74HC86",
    "74HC164",
    "74HC283",
    "74HC541",
    "74HC688",
    "62256",
    "AS6C62256",
    "SST39SF010A",
]
SEED_PARTS = {"74HC161", "74HC157", "74HC245", "74HC574", "AT28C256"}

CLASS_NAMES = {
    "74HC00": "HC00",
    "74HC04": "HC04",
    "74HC21": "HC21",
    "74HC32": "HC32",
    "74HC74": "HC74",
    "74HC86": "HC86",
    "74HC164": "HC164",
    "74HC283": "HC283",
    "74HC541": "HC541",
    "74HC688": "HC688",
    "62256": "SRAM62256",
    "AS6C62256": "AS6C62256",
    "SST39SF010A": "SST39SF010A",
}

ROLES = {
    "74HC00": "nand_gate",
    "74HC04": "inverter",
    "74HC21": "and_gate",
    "74HC32": "or_gate",
    "74HC74": "flip_flop",
    "74HC86": "xor_gate",
    "74HC164": "shift_register",
    "74HC283": "adder",
    "74HC541": "buffer",
    "74HC688": "comparator",
    "62256": "sram",
    "AS6C62256": "sram",
    "SST39SF010A": "flash",
}

LOGIC_TYPES = {
    "74HC00": "quad_2_input_nand",
    "74HC04": "hex_inverter",
    "74HC21": "dual_4_input_and",
    "74HC32": "quad_2_input_or",
    "74HC74": "dual_d_flip_flop",
    "74HC86": "quad_2_input_xor",
    "74HC164": "serial_in_parallel_out_shift_register",
    "74HC283": "four_bit_binary_adder",
    "74HC541": "octal_buffer",
    "74HC688": "eight_bit_identity_comparator",
    "62256": "32k_x_8_sram",
    "AS6C62256": "32k_x_8_sram",
    "SST39SF010A": "128k_x_8_flash",
}

DELAYS = {
    "74HC00": 12,
    "74HC04": 12,
    "74HC21": 15,
    "74HC32": 12,
    "74HC74": 20,
    "74HC86": 15,
    "74HC164": 20,
    "74HC283": 35,
    "74HC541": 12,
    "74HC688": 30,
    "62256": 70,
    "AS6C62256": 70,
    "SST39SF010A": 70,
}


def _target_parts() -> list[str]:
    legacy_parts = {
        path.parent.name
        for path in [*ROOT.glob("DB/74xx/*/chip.json"), *ROOT.glob("DB/Memory/*/chip.json")]
    }
    migrated_parts = {
        path.parents[1].name
        for path in [*ROOT.glob("DB/74xx/*/definition/definition.json"), *ROOT.glob("DB/Memory/*/definition/definition.json")]
        if path.parents[1].name not in SEED_PARTS
    }
    return sorted(set(PARTS) | legacy_parts | migrated_parts)


def _class_name(part: str) -> str:
    if part in CLASS_NAMES:
        return CLASS_NAMES[part]
    if part.startswith("74HC"):
        return f"HC{part[4:]}"
    clean = re.sub(r"\W+", "", part)
    if clean and clean[0].isdigit():
        clean = f"Chip{clean}"
    return clean or "LocalChip"


def _role(part: str, manifest: dict) -> str:
    if part in ROLES:
        return ROLES[part]
    if part.startswith("74"):
        title = str(manifest.get("title", "logic")).lower()
        if "counter" in title:
            return "counter"
        if "register" in title or "latch" in title or "flip-flop" in title:
            return "register"
        if "decoder" in title or "demultiplexer" in title:
            return "decoder"
        if "multiplexer" in title or "selector" in title:
            return "multiplexer"
        if "buffer" in title or "driver" in title:
            return "buffer"
        if "comparator" in title:
            return "comparator"
        if "adder" in title or "alu" in title:
            return "alu"
        return "logic"
    return "memory"


def _logic_type(part: str, manifest: dict) -> str:
    if part in LOGIC_TYPES:
        return LOGIC_TYPES[part]
    title = str(manifest.get("title", part)).lower()
    words = re.findall(r"[a-z0-9]+", title)
    return "_".join(words[:8]) or part.lower()


def _delay(part: str, base: Path) -> int:
    if part in DELAYS:
        return DELAYS[part]
    return 70 if base.parent.name == "Memory" else 15


def main() -> None:
    for part in _target_parts():
        base = _base_for(part)
        manifest_path = base / "chip.json"
        manifest = _read_json(manifest_path) if manifest_path.exists() else load_component(part)
        definition = _definition_from_manifest(manifest, base)
        _write_json(base / "definition" / "definition.json", definition)
        _write_json(base / "simulation" / "model.json", _simulation_model(definition))
        _write_json(base / "simulation" / "netlist.json", _netlist(definition, manifest))
        _write_text(base / "simulation" / "model.py", _model_py(part, manifest))
        source_verilog = ROOT / manifest["verilog"]["file"]
        target_verilog = base / "simulation" / "model.v"
        if source_verilog.resolve() != target_verilog.resolve():
            shutil.copyfile(source_verilog, target_verilog)
        _write_json(base / "symbol" / "dip.json", _symbol(definition))
        for test_name in ("truth_table", "timing", "tri_state", "bus_fight", "propagation"):
            _write_json(base / "tests" / f"{test_name}.json", _test_record(definition, test_name))
        _write_json(base / "generated" / "artifacts.json", generate_component_artifacts(part))
        if manifest_path.exists():
            manifest_path.unlink()


def _base_for(part: str) -> Path:
    for group in ("74xx", "Memory"):
        candidate = ROOT / "DB" / group / part
        if candidate.exists():
            return candidate
    raise FileNotFoundError(part)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _definition_from_manifest(manifest: dict, base: Path) -> dict:
    part = manifest["part"]
    group = base.parent.name.lower()
    pins = [_pin(pin) for pin in manifest["pins"]]
    package_id = "N" if group == "74xx" else "DIP"
    generation = {
        "targets": [
            "json",
            "python_simulator",
            "verilog_wrapper",
            "kicad_symbol",
            "svg_pinout",
            "documentation",
            "unit_test",
            "interactive_demo",
        ],
        "python": {
            "factory": "create",
            "part": part,
            "file": f"DB/{base.parent.name}/{part}/simulation/model.py",
            "class": _class_name(part),
        },
        "verilog": {
            "module": manifest["verilog"]["module"],
            "file": f"DB/{base.parent.name}/{part}/simulation/model.v",
            "netlist": f"DB/{base.parent.name}/{part}/simulation/netlist.json",
        },
    }
    sources = []
    for source in manifest.get("sources", []):
        item = dict(source)
        if not item.get("package_evidence"):
            item["package_evidence"] = "datasheet-required"
        item.setdefault("used_for", ["pins", "package", "logic"])
        sources.append(item)
    definition = {
        "schema": "db.component.digital",
        "version": 1,
        "part": part,
        "metadata": {
            "title": manifest["title"],
            "family": manifest.get("family", ""),
            "group": group,
            "role": _role(part, manifest),
        },
        "package": {
            "kind": manifest["package"]["kind"],
            "pins": manifest["package"]["pins"],
            "default": package_id,
        },
        "pins": pins,
        "logic": {
            "type": _logic_type(part, manifest),
            "description": manifest["title"],
        },
        "timing": {"delay_ns": _delay(part, base)},
        "generation": generation,
        "verification": {
            "tests": _applicable_tests(pins),
            "required_vectors": ["basic_function", "disabled_or_high_z"] if _has_tristate(pins) else ["basic_function"],
        },
        "datasheet": {
            "schema": "db.component.datasheet.sources",
            "version": 1,
            "part": part,
            "sources": sources,
        },
        "definition_layers": _definition_layers(manifest, pins, package_id),
        "status": manifest["status"],
    }
    return definition


def _pin(pin: dict) -> dict:
    item = dict(pin)
    name = str(item.get("name", ""))
    if name in {"VCC", "VDD", "GND", "VSS"}:
        item["rail"] = name
    if name.startswith("/"):
        item["active_low"] = True
    return item


def _definition_layers(manifest: dict, pins: list[dict], package_id: str) -> dict:
    part = manifest["part"]
    group = "74xx" if part.startswith("74") else "memory"
    power = [pin for pin in pins if pin.get("direction") == "power"]
    timing = {
        "schema": "db.component.timing",
        "version": 1,
        "part": part,
        "delay": {
            "model_delay_ns": _delay(part, _base_for(part)),
            "status": "model-derived",
        },
        "evidence": _first_source(manifest),
    }
    electrical = {
        "schema": "db.component.electrical",
        "version": 1,
        "part": part,
        "voltage": {"vcc": {"status": "datasheet-required"}},
        "current": {"status": "datasheet-required"},
        "loading": {"status": "datasheet-required"},
        "evidence": _first_source(manifest),
    }
    return {
        "component": {
            "schema": "db.component.definition",
            "version": 1,
            "part": part,
            "title": manifest["title"],
            "family": manifest.get("family", ""),
            "group": group,
            "kind": manifest.get("kind", "ic"),
            "role": _role(part, manifest),
        },
        "package": {
            "schema": "db.component.package",
            "version": 1,
            "part": part,
            "packages": [{"id": package_id, "kind": manifest["package"]["kind"], "pins": manifest["package"]["pins"]}],
            "default_package": package_id,
        },
        "pins": {
            "schema": "db.component.pins",
            "version": 1,
            "part": part,
            "pins": pins,
        },
        "power": {
            "schema": "db.component.power",
            "version": 1,
            "part": part,
            "rails": power,
        },
        "logic": {
            "schema": "db.component.logic",
            "version": 1,
            "part": part,
            "logic": {"type": _logic_type(part, manifest), "description": manifest["title"]},
        },
        "timing": timing,
        "electrical": electrical,
    }


def _first_source(manifest: dict) -> dict:
    sources = manifest.get("sources", [])
    return dict(sources[0]) if sources else {"status": "datasheet-required"}


def _simulation_model(definition: dict) -> dict:
    part = definition["part"]
    py = definition["generation"]["python"]
    verilog = definition["generation"]["verilog"]
    implements = ["propagation_delay"]
    if _has_tristate(definition["pins"]):
        implements.extend(["tristate", "bidirectional"])
    return {
        "schema": "db.component.simulation",
        "version": 1,
        "part": part,
        "python": {
            "factory": "create",
            "class": py["class"],
            "file": py["file"],
            "implements": implements,
        },
        "verilog": {
            "module": verilog["module"],
            "file": verilog["file"],
            "implements": implements,
        },
        "netlist_generation": {
            "source": verilog["netlist"],
            "status": "tested",
        },
    }


def _netlist(definition: dict, manifest: dict) -> dict:
    verilog = definition["generation"]["verilog"]
    return {
        "schema": "db.component.simulation.netlist",
        "version": 1,
        "part": definition["part"],
        "source": f"DB/{definition['metadata']['group'] if definition['metadata']['group'] != 'memory' else 'Memory'}/{definition['part']}/definition/definition.json",
        "simulation": {
            "python": definition["generation"]["python"]["file"],
            "verilog": verilog["file"],
        },
        "verilog": {
            "module": verilog["module"],
            "export": manifest["verilog"]["export"],
        },
        "pins": definition["pins"],
    }


def _symbol(definition: dict) -> dict:
    pins = definition["pins"]
    midpoint = len(pins) // 2
    return {
        "schema": "db.component.symbol.dip",
        "version": 1,
        "part": definition["part"],
        "shape": "dip",
        "package": definition["package"],
        "pins": pins,
        "layout": {
            "left": [pin["number"] for pin in pins[:midpoint]],
            "right": [pin["number"] for pin in pins[midpoint:]],
        },
    }


def _test_record(definition: dict, test_name: str) -> dict:
    applicable = test_name in _applicable_tests(definition["pins"])
    record = {
        "schema": f"db.component.test.{test_name}",
        "version": 1,
        "part": definition["part"],
        "applicable": applicable,
    }
    if applicable:
        if test_name == "truth_table":
            record["vectors"] = [{"name": "basic_function", "description": "Covered by Python model and Verilog smoke tests"}]
        elif test_name == "timing":
            record["checks"] = [{"name": "model_delay", "expect_delay_ns": definition["timing"]["delay_ns"]}]
        elif test_name == "propagation":
            record["checks"] = [{"name": "model_propagation", "expect_delay_ns": definition["timing"]["delay_ns"]}]
        elif test_name == "tri_state":
            record["checks"] = [{"name": "disabled_outputs_release_bus"}]
        elif test_name == "bus_fight":
            record["checks"] = [{"name": "external_driver_conflict_is_detectable"}]
    else:
        record["reason"] = f"{test_name} is not applicable to {definition['part']}"
    return record


def _applicable_tests(pins: list[dict]) -> list[str]:
    tests = ["truth_table", "timing", "propagation"]
    if _has_tristate(pins):
        tests.extend(["tri_state", "bus_fight"])
    return tests


def _has_tristate(pins: list[dict]) -> bool:
    return any(pin.get("direction") == "bidirectional" for pin in pins) or any(str(pin.get("name", "")).startswith("/OE") for pin in pins)


def _model_py(part: str, manifest: dict) -> str:
    if part not in MODEL_BODIES:
        return _catalog_model_py(part, manifest)
    pins_literal = _pins_literal(manifest["pins"])
    delay = _delay(part, _base_for(part))
    cls = _class_name(part)
    body = MODEL_BODIES[part]
    return f'''"""Local behavior model for {part}."""

from __future__ import annotations

from chiplib.core import Chip, Delay, Z, bit, pins_from


class {cls}(Chip):
    part = "{part}"

    def __init__(self, name: str):
        pins = {pins_literal}
        super().__init__(name, pins_from(pins), Delay({delay}))
{body}


def create(name: str = "U") -> {cls}:
    return {cls}(name)
'''


def _pins_literal(pins: list[dict]) -> str:
    items = []
    direction_map = {"input": "in", "output": "out", "bidirectional": "bidir", "power": "power", "nc": "nc"}
    for pin in pins:
        number = pin["number"]
        name = pin["name"]
        direction = direction_map.get(pin["direction"], pin["direction"])
        items.append(f'{number}: ("{name}", "{direction}")')
    return "{" + ", ".join(items) + "}"


def _catalog_model_py(part: str, manifest: dict) -> str:
    pins_literal = _pins_literal(manifest["pins"])
    cls = _class_name(part)
    delay = _delay(part, _base_for(part))
    support = _catalog_support_source()
    return f'''"""Local behavior model for {part}."""

from __future__ import annotations

import re

from chiplib.core import Chip, Delay, Z, bit, pins_from


{support}


class {cls}(LocalCatalogChip):
    part = "{part}"

    def __init__(self, name: str):
        pins = {pins_literal}
        super().__init__("{part}", name, pins, {delay})


def create(name: str = "U") -> {cls}:
    return {cls}(name)
'''


def _catalog_support_source() -> str:
    text = (ROOT / "python" / "chiplib" / "catalog.py").read_text(encoding="utf-8")
    methods_start = text.index("    def has")
    methods_end = text.index("\ndef _natural_key")
    helpers_start = text.index("def _natural_key")
    helpers_end = text.index("\n\nCATALOG_PARTS")
    methods = text[methods_start:methods_end]
    helpers = text[helpers_start:helpers_end].replace("CatalogChip", "LocalCatalogChip")
    header = '''class LocalCatalogChip(Chip):
    def __init__(self, part: str, name: str, pins: dict[int, tuple[str, str]], delay_ns: int = 15):
        self.part = part
        super().__init__(name, pins_from(pins), Delay(delay_ns))
        self._state = 0
        self._state2 = 0
        self._state_by_block: dict[int, int] = {}
        self._scan_col = 0
        self._prev_we = 1
        self.data = bytearray(1 << (17 if part == "SST39SF010A" else 15))
'''
    return header + methods + "\n\n" + helpers


MODEL_BODIES = {
    "74HC00": '''
    def update(self) -> None:
        for a, b, y in [(1, 2, 3), (4, 5, 6), (9, 10, 8), (12, 13, 11)]:
            self.output(y, 1 - (bit(self.read(a)) & bit(self.read(b))))
''',
    "74HC04": '''
    def update(self) -> None:
        for a, y in [(1, 2), (3, 4), (5, 6), (9, 8), (11, 10), (13, 12)]:
            self.output(y, 1 - bit(self.read(a)))
''',
    "74HC21": '''
    def update(self) -> None:
        self.output(6, bit(self.read(1)) & bit(self.read(2)) & bit(self.read(4)) & bit(self.read(5)))
        self.output(8, bit(self.read(9)) & bit(self.read(10)) & bit(self.read(12)) & bit(self.read(13)))
''',
    "74HC32": '''
    def update(self) -> None:
        for a, b, y in [(1, 2, 3), (4, 5, 6), (9, 10, 8), (12, 13, 11)]:
            self.output(y, bit(self.read(a)) | bit(self.read(b)))
''',
    "74HC86": '''
    def update(self) -> None:
        for a, b, y in [(1, 2, 3), (4, 5, 6), (9, 10, 8), (12, 13, 11)]:
            self.output(y, bit(self.read(a)) ^ bit(self.read(b)))
''',
    "74HC283": '''
    def update(self) -> None:
        a = _byte_from_pins(self, [5, 3, 14, 12])
        b = _byte_from_pins(self, [6, 2, 15, 11])
        result = a + b + bit(self.read(7))
        _write_pins(self, [4, 1, 13, 10], result)
        self.output(9, (result >> 4) & 1)


def _byte_from_pins(chip: Chip, pins: list[int]) -> int:
    value = 0
    for index, pin in enumerate(pins):
        value |= bit(chip.read(pin)) << index
    return value


def _write_pins(chip: Chip, pins: list[int], value: int) -> None:
    for index, pin in enumerate(pins):
        chip.output(pin, (value >> index) & 1)
''',
    "74HC688": '''
    def update(self) -> None:
        if bit(self.read(1)):
            self.output(11, 1)
            return
        p_value = _byte_from_pins(self, [2, 4, 6, 8, 19, 17, 15, 13])
        q_value = _byte_from_pins(self, [3, 5, 7, 9, 18, 16, 14, 12])
        self.output(11, 0 if p_value == q_value else 1)


def _byte_from_pins(chip: Chip, pins: list[int]) -> int:
    value = 0
    for index, pin in enumerate(pins):
        value |= bit(chip.read(pin)) << index
    return value
''',
    "74HC541": '''
    def update(self) -> None:
        enabled = not bit(self.read(1)) and not bit(self.read(19))
        for index in range(8):
            self.output(18 - index, bit(self.read(2 + index)) if enabled else Z)
''',
    "74HC164": '''
        self._sr = [0] * 8
        self._q_pins = [3, 4, 5, 6, 10, 11, 12, 13]

    def clock_edge(self, pin: int | str | None = None) -> None:
        if not bit(self.read(9)):
            self._sr = [0] * 8
        else:
            self._sr = [bit(self.read(1)) & bit(self.read(2))] + self._sr[:7]
        self.update()

    def update(self) -> None:
        if not bit(self.read(9)):
            self._sr = [0] * 8
        for index, pin in enumerate(self._q_pins):
            self.output(pin, self._sr[index])
''',
    "74HC74": '''
        self._q = [0, 0]

    def clock_edge(self, pin: int | str | None = None) -> None:
        blocks = [0, 1]
        if pin is not None:
            number = self.pin_number(pin)
            blocks = [0] if number == 3 else ([1] if number == 11 else [])
        for block in blocks:
            if block == 0:
                if not bit(self.read(1)):
                    self._q[0] = 0
                elif not bit(self.read(4)):
                    self._q[0] = 1
                else:
                    self._q[0] = bit(self.read(2))
            else:
                if not bit(self.read(13)):
                    self._q[1] = 0
                elif not bit(self.read(10)):
                    self._q[1] = 1
                else:
                    self._q[1] = bit(self.read(12))
        self.update()

    def update(self) -> None:
        if not bit(self.read(1)):
            self._q[0] = 0
        elif not bit(self.read(4)):
            self._q[0] = 1
        if not bit(self.read(13)):
            self._q[1] = 0
        elif not bit(self.read(10)):
            self._q[1] = 1
        self.output(5, self._q[0])
        self.output(6, 1 - self._q[0])
        self.output(9, self._q[1])
        self.output(8, 1 - self._q[1])
''',
    "62256": '''
        self.data = bytearray(32768)

    def update(self) -> None:
        selected = not bit(self.read("/CE"))
        address = _memory_address(self)
        if selected and not bit(self.read("/WE")):
            self.data[address] = _byte_from_pins(self, MEMORY_DQ_PINS)
        read_enabled = selected and bit(self.read("/WE")) and not bit(self.read("/OE"))
        if read_enabled:
            _write_pins(self, MEMORY_DQ_PINS, self.data[address])
        else:
            for pin in MEMORY_DQ_PINS:
                self.output(pin, Z)


MEMORY_ADDR_PINS = {0: 10, 1: 9, 2: 8, 3: 7, 4: 6, 5: 5, 6: 4, 7: 3, 8: 25, 9: 24, 10: 21, 11: 23, 12: 2, 13: 26, 14: 1}
MEMORY_DQ_PINS = [11, 12, 13, 15, 16, 17, 18, 19]


def _memory_address(chip: Chip) -> int:
    value = 0
    for index, pin in MEMORY_ADDR_PINS.items():
        value |= bit(chip.read(pin)) << index
    return value


def _byte_from_pins(chip: Chip, pins: list[int]) -> int:
    value = 0
    for index, pin in enumerate(pins):
        value |= bit(chip.read(pin)) << index
    return value


def _write_pins(chip: Chip, pins: list[int], value: int) -> None:
    for index, pin in enumerate(pins):
        chip.output(pin, (value >> index) & 1)
''',
    "AS6C62256": '''
        self.data = bytearray(32768)

    def update(self) -> None:
        selected = not bit(self.read("/CE"))
        address = _memory_address(self)
        if selected and not bit(self.read("/WE")):
            self.data[address] = _byte_from_pins(self, MEMORY_DQ_PINS)
        read_enabled = selected and bit(self.read("/WE")) and not bit(self.read("/OE"))
        if read_enabled:
            _write_pins(self, MEMORY_DQ_PINS, self.data[address])
        else:
            for pin in MEMORY_DQ_PINS:
                self.output(pin, Z)


MEMORY_ADDR_PINS = {0: 10, 1: 9, 2: 8, 3: 7, 4: 6, 5: 5, 6: 4, 7: 3, 8: 25, 9: 24, 10: 21, 11: 23, 12: 2, 13: 26, 14: 1}
MEMORY_DQ_PINS = [11, 12, 13, 15, 16, 17, 18, 19]


def _memory_address(chip: Chip) -> int:
    value = 0
    for index, pin in MEMORY_ADDR_PINS.items():
        value |= bit(chip.read(pin)) << index
    return value


def _byte_from_pins(chip: Chip, pins: list[int]) -> int:
    value = 0
    for index, pin in enumerate(pins):
        value |= bit(chip.read(pin)) << index
    return value


def _write_pins(chip: Chip, pins: list[int], value: int) -> None:
    for index, pin in enumerate(pins):
        chip.output(pin, (value >> index) & 1)
''',
    "SST39SF010A": '''
        self.data = bytearray(131072)

    def update(self) -> None:
        selected = not bit(self.read("/CE"))
        address = _memory_address(self)
        if selected and not bit(self.read("/WE")):
            self.data[address] = _byte_from_pins(self, MEMORY_DQ_PINS)
        read_enabled = selected and bit(self.read("/WE")) and not bit(self.read("/OE"))
        if read_enabled:
            _write_pins(self, MEMORY_DQ_PINS, self.data[address])
        else:
            for pin in MEMORY_DQ_PINS:
                self.output(pin, Z)


MEMORY_ADDR_PINS = {0: 12, 1: 11, 2: 10, 3: 9, 4: 8, 5: 7, 6: 6, 7: 5, 8: 27, 9: 26, 10: 23, 11: 25, 12: 4, 13: 28, 14: 29, 15: 3, 16: 2}
MEMORY_DQ_PINS = [13, 14, 15, 17, 18, 19, 20, 21]


def _memory_address(chip: Chip) -> int:
    value = 0
    for index, pin in MEMORY_ADDR_PINS.items():
        value |= bit(chip.read(pin)) << index
    return value


def _byte_from_pins(chip: Chip, pins: list[int]) -> int:
    value = 0
    for index, pin in enumerate(pins):
        value |= bit(chip.read(pin)) << index
    return value


def _write_pins(chip: Chip, pins: list[int], value: int) -> None:
    for index, pin in enumerate(pins):
        chip.output(pin, (value >> index) & 1)
''',
}


if __name__ == "__main__":
    main()
