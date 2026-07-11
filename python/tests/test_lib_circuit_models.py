"""DB part-model smoke coverage for every RV8GR circuit-library package.

These probes instantiate individual DB models; they do not execute circuit.json
wiring.  Composite classification is metadata evidence only and requires local
package references plus wiring that passes the strict endpoint audit.  This module
deliberately does not introduce a second circuit simulator.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from chiplib import Z
from chiplib.core import Chip
from tests.test_lib_circuit_endpoints import audit_circuit_endpoints


ROOT = Path(__file__).resolve().parents[2]
CIRCUITS = ROOT / "examples" / "circuits"
DB = ROOT / "lib" / "standard"

BYTE_D = [2, 3, 4, 5, 6, 7, 8, 9]
BYTE_Q = [19, 18, 17, 16, 15, 14, 13, 12]
MEMORY_A = {0: 10, 1: 9, 2: 8, 3: 7, 4: 6, 5: 5, 6: 4, 7: 3, 8: 25,
            9: 24, 10: 21, 11: 23, 12: 2, 13: 26, 14: 1}
MEMORY_DQ = [11, 12, 13, 15, 16, 17, 18, 19]


# Every package has one classification.  "part-model-smoke" means only that its
# declared DB parts are probed in isolation, never that package wiring executes.
PACKAGE_CLASSIFICATION = {
    "RV8GR_AddressMux16": "part-model-smoke",
    "RV8GR_AluAccumulator": "part-model-smoke",
    "RV8GR_BootSequenceTrace": "part-model-smoke",
    "RV8GR_BranchJumpControl": "part-model-smoke",
    "RV8GR_BusOwnership": "part-model-smoke",
    "RV8GR_DataPageMemory": "part-model-smoke",
    "RV8GR_FetchCycleTrace": "part-model-smoke",
    "RV8GR_FullControlOpcodeSweep": "composition-plan-only",
    "RV8GR_IRQLatch": "part-model-smoke",
    "RV8GR_InstructionLatch": "part-model-smoke",
    "RV8GR_InterruptTrace": "part-model-smoke",
    "RV8GR_Lab13MarkerTrace": "part-model-smoke",
    "RV8GR_PC16": "part-model-smoke",
    "RV8GR_PageDataRegisters": "part-model-smoke",
    "RV8GR_PageJumpTrace": "part-model-smoke",
    "RV8GR_ResetClockBringup": "part-model-smoke",
    "RV8GR_RingCounter": "part-model-smoke",
    "RV8GR_RomDbusRead": "part-model-smoke",
    "RV8GR_StoreLoadBranchTrace": "part-model-smoke",
    "RV8GR_StorePath": "part-model-smoke",
    "RV8GR_VirtualTestHelpers": "service-only",
    "RV8GR_WholeSystemChipLevelVirtual": "wired-composite-metadata",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def circuit(package: str) -> dict:
    return load_json(CIRCUITS / package / "circuit.json")


def db_model(part: str, name: str = "U") -> Chip:
    matches = list(DB.glob(f"*/{part}/simulation/model.py"))
    assert len(matches) == 1, f"{part}: expected one live DB model, found {matches}"
    path = matches[0]
    spec = importlib.util.spec_from_file_location(f"test_live_db_{part}", path)
    assert spec is not None and spec.loader is not None, f"{part}: cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    chip = module.create(name)
    assert isinstance(chip, Chip), f"{part}: DB create() did not return Chip"
    assert chip.part.upper().replace("-", "") == part.upper().replace("-", "")
    assert Path(module.__file__).resolve() == path.resolve()
    return chip


def settle(chip: Chip) -> None:
    chip.update()
    chip.commit()


def set_bits(chip: Chip, pins: list[int], value: int) -> None:
    for bit, pin in enumerate(pins):
        chip.set_input(pin, (value >> bit) & 1)


def read_bits(chip: Chip, pins: list[int]) -> int:
    return sum((chip.read(pin) == 1) << bit for bit, pin in enumerate(pins))


def set_address(chip: Chip, address: int) -> None:
    for bit, pin in MEMORY_A.items():
        chip.set_input(pin, (address >> bit) & 1)


def component_parts(package: str) -> set[str]:
    return {item["part"] for item in circuit(package)["chips"]}


def physical_parts(package: str) -> set[str]:
    return {part for part in component_parts(package) if list(DB.glob(f"*/{part}/simulation/model.py"))}


def package_dependencies(package: str) -> set[str]:
    """Return machine-readable local package refs, not inferred architecture."""
    return component_parts(package) & PACKAGE_CLASSIFICATION.keys()


def probe_00() -> None:
    chip = db_model("74HC00")
    for a, b, expected in ((0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 0)):
        chip.set_input(1, a); chip.set_input(2, b); settle(chip)
        assert chip.read(3) == expected


def probe_04() -> None:
    chip = db_model("74HC04")
    for value in (0, 1):
        chip.set_input(1, value); settle(chip)
        assert chip.read(2) == 1 - value


def probe_21() -> None:
    chip = db_model("74HC21")
    for value in range(16):
        set_bits(chip, [1, 2, 4, 5], value); settle(chip)
        assert chip.read(6) == int(value == 15)


def probe_32() -> None:
    chip = db_model("74HC32")
    for a, b in ((0, 0), (0, 1), (1, 0), (1, 1)):
        chip.set_input(1, a); chip.set_input(2, b); settle(chip)
        assert chip.read(3) == (a | b)


def probe_74() -> None:
    chip = db_model("74HC74")
    chip.set_input(1, 1); chip.set_input(4, 1)
    for value in (1, 0):
        chip.set_input(2, value); chip.clock_edge(3); chip.commit()
        assert (chip.read(5), chip.read(6)) == (value, 1 - value)
    chip.set_input(1, 0); settle(chip)
    assert (chip.read(5), chip.read(6)) == (0, 1)


def probe_86() -> None:
    chip = db_model("74HC86")
    for a, b in ((0, 0), (0, 1), (1, 0), (1, 1)):
        chip.set_input(1, a); chip.set_input(2, b); settle(chip)
        assert chip.read(3) == (a ^ b)


def probe_157() -> None:
    chip = db_model("74HC157")
    chip.set_input(15, 0); chip.set_input(2, 0); chip.set_input(3, 1)
    for select in (0, 1):
        chip.set_input(1, select); settle(chip)
        assert chip.read(4) == select
    chip.set_input(15, 1); settle(chip)
    assert chip.read(4) == 0


def probe_161() -> None:
    chip = db_model("74HC161")
    chip.set_input(1, 1); chip.set_input(7, 1); chip.set_input(9, 1); chip.set_input(10, 1)
    for expected in range(1, 5):
        chip.clock_edge(2); chip.commit()
        assert read_bits(chip, [14, 13, 12, 11]) == expected
    chip.set_input(1, 0); settle(chip)
    assert read_bits(chip, [14, 13, 12, 11]) == 0


def probe_164() -> None:
    chip = db_model("74HC164")
    chip.set_input(9, 1); chip.set_input(1, 1); chip.set_input(2, 1)
    chip.clock_edge(8); chip.commit()
    assert read_bits(chip, [3, 4, 5, 6, 10, 11, 12, 13]) == 1
    chip.set_input(9, 0); settle(chip)
    assert read_bits(chip, [3, 4, 5, 6, 10, 11, 12, 13]) == 0


def probe_245() -> None:
    chip = db_model("74HC245")
    chip.set_input(19, 0); chip.set_input(1, 1); set_bits(chip, list(range(2, 10)), 0xA5); settle(chip)
    assert read_bits(chip, list(range(18, 10, -1))) == 0xA5
    chip.set_input(19, 1); settle(chip)
    assert all(chip.read(pin) == Z for pin in range(2, 10))
    assert all(chip.read(pin) == Z for pin in range(11, 19))


def probe_283() -> None:
    chip = db_model("74HC283")
    for a, b, carry in ((3, 5, 0), (15, 1, 0), (9, 6, 1)):
        set_bits(chip, [5, 3, 14, 12], a); set_bits(chip, [6, 2, 15, 11], b)
        chip.set_input(7, carry); settle(chip)
        result = a + b + carry
        assert read_bits(chip, [4, 1, 13, 10]) == (result & 15)
        assert chip.read(9) == ((result >> 4) & 1)


def probe_541() -> None:
    chip = db_model("74HC541")
    chip.set_input(1, 0); chip.set_input(19, 0); set_bits(chip, list(range(2, 10)), 0x3C); settle(chip)
    assert read_bits(chip, list(range(18, 10, -1))) == 0x3C
    chip.set_input(1, 1); settle(chip)
    assert all(chip.read(pin) == Z for pin in range(11, 19))


def probe_574() -> None:
    chip = db_model("74HC574")
    chip.set_input(1, 0); set_bits(chip, BYTE_D, 0x96); chip.clock_edge(11); chip.commit()
    assert read_bits(chip, BYTE_Q) == 0x96
    chip.set_input(1, 1); settle(chip)
    assert all(chip.read(pin) == Z for pin in BYTE_Q)


def probe_688() -> None:
    chip = db_model("74HC688")
    chip.set_input(1, 0)
    a_pins, b_pins = [2, 4, 6, 8, 11, 13, 15, 17], [3, 5, 7, 9, 12, 14, 16, 18]
    set_bits(chip, a_pins, 0x5A); set_bits(chip, b_pins, 0x5A); settle(chip)
    assert chip.read(19) == 0
    set_bits(chip, b_pins, 0x5B); settle(chip)
    assert chip.read(19) == 1


def probe_memory(part: str) -> None:
    chip = db_model(part)
    address, value = 0x1234, 0xA6
    chip.data[address] = value
    set_address(chip, address); chip.set_input(20, 0); chip.set_input(22, 0); chip.set_input(27, 1); settle(chip)
    assert read_bits(chip, MEMORY_DQ) == value
    chip.set_input(20, 1); settle(chip)
    assert all(chip.read(pin) == Z for pin in MEMORY_DQ)


PART_PROBES = {
    "74HC00": probe_00, "74HC04": probe_04, "74HC21": probe_21,
    "74HC32": probe_32, "74HC74": probe_74, "74HC86": probe_86,
    "74HC157": probe_157, "74HC161": probe_161, "74HC164": probe_164,
    "74HC245": probe_245, "74HC283": probe_283, "74HC541": probe_541,
    "74HC574": probe_574, "74HC688": probe_688,
    "62256": lambda: probe_memory("62256"),
    "AT28C256": lambda: probe_memory("AT28C256"),
}


def test_audit_has_exactly_all_22_circuit_packages() -> None:
    actual = {path.parent.name for path in CIRCUITS.glob("RV8GR_*/circuit.json")}
    assert len(actual) == 22
    assert set(PACKAGE_CLASSIFICATION) == actual


def test_part_model_smoke_probes_cover_declared_live_db_models() -> None:
    exercised: set[str] = set()
    for package, classification in PACKAGE_CLASSIFICATION.items():
        if classification != "part-model-smoke":
            continue
        parts = physical_parts(package)
        assert parts, f"{package}: part-model-smoke package has no DB model"
        missing = parts - PART_PROBES.keys()
        assert not missing, f"{package}: DB models lack behavioral probes: {sorted(missing)}"
        for part in sorted(parts):
            PART_PROBES[part]()
            exercised.add(part)
    declared = set().union(*(physical_parts(package) for package in PACKAGE_CLASSIFICATION))
    assert exercised == declared, f"unexecuted circuit DB parts: {sorted(declared - exercised)}"


def test_non_trace_part_model_smoke_inventory_is_explicit() -> None:
    expected_paths = {
        "RV8GR_AddressMux16": {"74HC157"},
        "RV8GR_AluAccumulator": {"74HC00", "74HC74", "74HC86", "74HC157", "74HC283", "74HC541", "74HC574", "74HC688"},
        "RV8GR_BranchJumpControl": {"74HC00", "74HC04", "74HC86"},
        "RV8GR_BusOwnership": {"74HC245", "74HC541", "62256", "AT28C256"},
        "RV8GR_DataPageMemory": {"74HC04", "74HC21", "74HC157", "74HC245", "74HC574", "62256", "AT28C256"},
        "RV8GR_IRQLatch": {"74HC74"},
        "RV8GR_InstructionLatch": {"74HC574"},
        "RV8GR_PC16": {"74HC161"},
        "RV8GR_PageDataRegisters": {"74HC00", "74HC21", "74HC32", "74HC574"},
        "RV8GR_ResetClockBringup": {"74HC04", "74HC32", "74HC161", "74HC164"},
        "RV8GR_RingCounter": {"74HC04", "74HC164"},
        "RV8GR_RomDbusRead": {"74HC245", "AT28C256"},
        "RV8GR_StorePath": {"74HC00", "74HC04", "74HC86", "74HC245", "74HC541", "62256", "AT28C256"},
    }
    actual = {
        package: physical_parts(package)
        for package, classification in PACKAGE_CLASSIFICATION.items()
        if classification == "part-model-smoke" and not package.endswith("Trace")
    }
    assert actual == expected_paths


def test_composite_classification_requires_wiring_and_endpoint_gate() -> None:
    findings = audit_circuit_endpoints()
    assert not findings, "package classification requires the endpoint gate to pass"

    for package, classification in PACKAGE_CLASSIFICATION.items():
        dependencies = package_dependencies(package)
        data = circuit(package)
        if classification == "wired-composite-metadata":
            assert dependencies, f"{package}: composite has no local package refs"
            assert data.get("wiring"), f"{package}: composite has no package wiring"
        elif classification == "composition-plan-only":
            assert dependencies, f"{package}: composition plan has no local package refs"
            assert not data.get("wiring"), f"{package}: wired plan must use composite classification"


def test_non_db_components_are_explicitly_classified_not_silently_skipped() -> None:
    virtual_services = {"ClockSource", "Switch", "Probe", "BusProbe", "RCParasitic", "DelayNoise", "OutputAssert"}
    symbolic = {"Virtual", "virtual_control_word", "RV8GR_VIRTUAL_BENCH_PLAN"}
    package_refs = set(PACKAGE_CLASSIFICATION)
    for package in PACKAGE_CLASSIFICATION:
        for part in component_parts(package) - physical_parts(package):
            assert (
                part in virtual_services
                or part in symbolic
                or part in package_refs
                or part.startswith("74HCxx ")
            ), f"{package}: unclassified non-executable component {part}"


if __name__ == "__main__":
    test_audit_has_exactly_all_22_circuit_packages()
    test_part_model_smoke_probes_cover_declared_live_db_models()
    test_non_trace_part_model_smoke_inventory_is_explicit()
    test_composite_classification_requires_wiring_and_endpoint_gate()
    test_non_db_components_are_explicitly_classified_not_silently_skipped()
    print("lib circuit DB part-model smoke tests: PASS")
