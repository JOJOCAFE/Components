"""Focused tests for the concrete circuit-package runner vertical slice."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import random
import tempfile
import unittest

from chiplib import CircuitRunner, CircuitRunnerError, load_circuit_runner
from chiplib.circuit_package import parse_circuit_package


ROOT = Path(__file__).resolve().parents[2]
RING = ROOT / "examples" / "circuits" / "RV8GR_RingCounter" / "circuit.json"
PACKAGE_ROOT = ROOT / "examples" / "circuits"


def package_data() -> dict:
    return {
        "schema": "components.lib.circuit",
        "version": 1,
        "id": "runner-fixture",
        "title": "Runner fixture",
        "source_project": {"name": "Components", "paths": ["python/chiplib/core.py"]},
        "chips": [{"ref": "U1", "part": "74HC04", "role": "inverter"}],
        "ports": [{"name": "IN", "direction": "input"}, {"name": "OUT", "direction": "output"}],
        "wiring": [
            {"net": "IN", "connections": ["IN", "U1.1"]},
            {"net": "OUT", "connections": ["U1.2", "OUT"]},
        ],
        "verification": {"tests": ["python/tests/test_circuit_runner.py"]},
    }


class CircuitRunnerTests(unittest.TestCase):
    def test_executes_ring_counter_through_live_models_and_wiring(self) -> None:
        runner = load_circuit_runner(RING)
        self.assertEqual({"T0": 0, "T1": 0, "T2": 0}, runner.reset())
        runner.set_input("/CLR", 1)
        expected = (
            {"T0": 1, "T1": 0, "T2": 0},
            {"T0": 0, "T1": 1, "T2": 0},
            {"T0": 0, "T1": 0, "T2": 1},
        )
        for state in expected:
            self.assertEqual(state, runner.pulse_clock())
        self.assertEqual(1, runner.read("T2"))
        snapshot = runner.snapshot()
        self.assertEqual("rv8gr_ring_counter", snapshot["circuit"])
        self.assertEqual({"74HC164", "74HC04"}, {item["part"] for item in snapshot["provenance"].values()})
        self.assertTrue(all(item["source"] == "live_db_package" for item in snapshot["provenance"].values()))

    def test_ring_counter_holds_without_a_rising_edge(self) -> None:
        runner = load_circuit_runner(RING)
        runner.reset()
        runner.set_input("/CLR", 1)
        runner.pulse_clock()
        before = runner.read()
        runner.set_input("CLK", 0)
        self.assertEqual(before, runner.read())
        runner.set_input("CLK", 0)
        self.assertEqual(before, runner.read())

    def test_sessions_are_isolated(self) -> None:
        first = load_circuit_runner(RING)
        second = load_circuit_runner(RING)
        first.reset()
        second.reset()
        first.set_input("/CLR", 1)
        first.pulse_clock()
        self.assertEqual({"T0": 1, "T1": 0, "T2": 0}, first.read())
        self.assertEqual({"T0": 0, "T1": 0, "T2": 0}, second.read())
        self.assertIsNot(first.board, second.board)
        self.assertIsNot(first.board.chips["U8"], second.board.chips["U8"])

    def test_shuffled_package_order_is_deterministic(self) -> None:
        original = json.loads(RING.read_text(encoding="utf-8"))
        traces = []
        for seed in range(8):
            data = deepcopy(original)
            random.Random(seed).shuffle(data["chips"])
            random.Random(seed + 100).shuffle(data["wiring"])
            package = parse_circuit_package(data, source_path=RING)
            runner = CircuitRunner(package)
            runner.reset()
            runner.set_input("/CLR", 1)
            traces.append([runner.pulse_clock() for _ in range(6)])
        self.assertTrue(all(trace == traces[0] for trace in traces[1:]))

    def test_executes_declared_package_proof_vectors(self) -> None:
        result = load_circuit_runner(RING).run_package_proofs()
        self.assertTrue(result["passed"], result)
        self.assertEqual("rv8gr_ring_counter", result["circuit"])
        proof = result["proofs"][0]
        self.assertTrue(proof["source"].endswith("tests/ring_counter.json"))
        names = {check["name"] for check in proof["checks"]}
        self.assertTrue({"reset", "clock_6", "falling_edge_holds", "no_rising_edge_holds", "illegal_state_recovery_000"} <= names)
        self.assertEqual(4, len(proof["unexercised"]))
        self.assertTrue(all(item["reason"] == "live model has no public state-load interface" for item in proof["unexercised"]))

    def test_scalar_input_output_and_operation_errors(self) -> None:
        runner = CircuitRunner(parse_circuit_package(package_data(), source_path=ROOT / "fixture.json"))
        self.assertEqual(1, runner.read("OUT"))
        runner.set_input("IN", 1)
        self.assertEqual(0, runner.read("OUT"))
        with self.assertRaises(CircuitRunnerError) as caught:
            runner.set_input("MISSING", 0)
        self.assertEqual("unknown_input", caught.exception.issues[0].code)

    def test_vector_ports_preserve_order_integer_x_and_z(self) -> None:
        data = package_data()
        data["chips"] = [{"ref": "U1", "part": "74HC04", "role": "four inverters"}]
        data["ports"] = [
            {"name": "IN0..IN3", "direction": "input"},
            {"name": "OUT0..OUT3", "direction": "output"},
        ]
        data["wiring"] = [
            {"net": "IN0..IN3", "connections": ["U1.1", "U1.3", "U1.5", "U1.9"]},
            {"net": "OUT0..OUT3", "connections": ["U1.2", "U1.4", "U1.6", "U1.8"]},
        ]
        runner = CircuitRunner(parse_circuit_package(data, source_path=ROOT / "fixture.json"))
        self.assertEqual((1, 1, 1, 1), runner.read("OUT0..OUT3"))
        self.assertEqual((0, 1, 0, 1), runner.set_input("IN0..IN3", 0b1010))
        self.assertEqual((1, 0, 1, 0), runner.read("OUT0..OUT3"))
        runner.set_input("IN0..IN3", ["X", 0, 1, "Z"])
        self.assertEqual(("X", 0, 1, "Z"), runner.snapshot()["ports"]["inputs"]["IN0..IN3"])
        self.assertEqual((1, 1, 0, 1), runner.read("OUT0..OUT3"))
        with self.assertRaises(CircuitRunnerError) as caught:
            runner.set_input("IN0..IN3", [0, 1])
        self.assertEqual("vector_width_mismatch", caught.exception.issues[0].code)

    def test_requested_bus_and_inout_packages_are_loadable(self) -> None:
        requested = {
            "RV8GR_StorePath": "rv8gr_store_path",
            "RV8GR_BranchJumpControl": "rv8gr_branch_jump_control",
            "RV8GR_RomDbusRead": "rv8gr_rom_dbus_read",
            "RV8GR_IRQLatch": "rv8gr_irq_latch",
        }
        for name, package_id in requested.items():
            with self.subTest(package=name):
                runner = load_circuit_runner(PACKAGE_ROOT / name / "circuit.json")
                self.assertEqual(package_id, runner.package.id)

        rom = load_circuit_runner(PACKAGE_ROOT / "RV8GR_RomDbusRead" / "circuit.json")
        rom.set_input("WR_DIR", 1)
        rom.set_input("BUF_OE_N", 1)
        self.assertEqual(("Z",) * 8, rom.release_input("DBUS0..DBUS7"))
        self.assertEqual(("Z",) * 8, rom.read("DBUS0..DBUS7"))

    def test_rejects_ranges_symbolic_aggregates_and_unresolved_outputs(self) -> None:
        cases = []
        ranged = package_data()
        ranged["wiring"][0]["connections"][1] = "U1.1..2"
        cases.append((ranged, "ambiguous_range_width"))
        symbolic = package_data()
        symbolic["chips"][0]["symbolic_endpoints"] = ["A"]
        symbolic["wiring"][0]["connections"][1] = "U1.A"
        cases.append((symbolic, "ambiguous_symbolic_width"))
        unresolved = package_data()
        unresolved["ports"][1]["name"] = "MISSING"
        cases.append((unresolved, "unresolved_output"))
        for data, code in cases:
            with self.subTest(code=code), self.assertRaises(CircuitRunnerError) as caught:
                CircuitRunner(parse_circuit_package(data, source_path=ROOT / "fixture.json"))
            self.assertIn(code, {issue.code for issue in caught.exception.issues})
            self.assertEqual("circuit_runner_error", caught.exception.to_dict()["error"])

    def test_symbolic_endpoint_resolves_exact_public_pin_name(self) -> None:
        data = package_data()
        data["chips"][0]["symbolic_endpoints"] = ["1A"]
        data["wiring"][0]["connections"][1] = "U1.1A"
        runner = CircuitRunner(parse_circuit_package(data, source_path=ROOT / "fixture.json"))
        runner.set_input("IN", 1)
        self.assertEqual(0, runner.read("OUT"))

    def test_public_boundary_owns_shared_virtual_driver_until_release(self) -> None:
        data = package_data()
        data["chips"].append({"ref": "SW", "part": "Switch", "role": "input stimulus"})
        data["wiring"][0]["connections"].append("SW.1")
        runner = CircuitRunner(parse_circuit_package(data, source_path=ROOT / "fixture.json"))
        virtual = runner.board.sources["virtual:SW"]
        self.assertFalse(virtual.enabled)
        runner.set_input("IN", 1)
        self.assertFalse(virtual.enabled)
        runner.release_input("IN")
        self.assertTrue(virtual.enabled)
        self.assertEqual(1, runner.read("OUT"))

    def test_loads_rom_image_through_public_runner_contract(self) -> None:
        runner = load_circuit_runner(PACKAGE_ROOT / "RV8GR_RomDbusRead" / "circuit.json")
        with tempfile.NamedTemporaryFile(suffix=".bin") as image:
            image.write(b"\xA5\x5A")
            image.flush()
            self.assertEqual(2, runner.load_memory_image("ROM1", image.name))
        self.assertEqual(b"\xA5\x5A", bytes(runner.board.chips["ROM1"].data[:2]))
        with self.assertRaises(CircuitRunnerError) as caught:
            runner.load_memory_image("U7", "unused.bin")
        self.assertEqual("memory_image_not_loadable", caught.exception.issues[0].code)

    def test_rejects_virtual_parts_composites_and_duplicate_refs(self) -> None:
        virtual_package = parse_circuit_package(package_data(), source_path=ROOT / "fixture.json")
        virtual_package = replace(
            virtual_package,
            chips=(replace(virtual_package.chips[0], part="Virtual"),),
        )
        with self.assertRaises(CircuitRunnerError) as caught:
            CircuitRunner(virtual_package)
        self.assertIn("virtual_part_not_executable", {issue.code for issue in caught.exception.issues})

        named = package_data()
        named["chips"].append({"ref": "P1", "part": "Probe", "role": "output observer"})
        named["wiring"][1]["connections"].append("P1.1")
        runner = CircuitRunner(parse_circuit_package(named, source_path=ROOT / "fixture.json"))
        self.assertEqual("Probe", runner.virtual_adapters["P1"].part)
        virtual = runner.snapshot()["virtual_adapters"]["P1"]
        self.assertTrue(virtual["modeled_only"])
        self.assertEqual(("OUT",), virtual["nets"])

        composite = package_data()
        composite["chips"][0]["part"] = "RV8GR_RingCounter"
        composite["chips"][0]["symbolic_endpoints"] = ["CLK"]
        composite["wiring"][0]["connections"][1] = "U1.CLK"
        composite["wiring"][1]["connections"][0] = "U1.CLK"
        with self.assertRaises(CircuitRunnerError) as caught:
            CircuitRunner(parse_circuit_package(composite, source_path=ROOT / "examples" / "circuits" / "fixture.json", check_files=False))
        self.assertIn("composite_not_executable", {issue.code for issue in caught.exception.issues})

        duplicate = package_data()
        duplicate["chips"].append(deepcopy(duplicate["chips"][0]))
        with self.assertRaisesRegex(Exception, "duplicate_ref"):
            parse_circuit_package(duplicate, source_path=ROOT / "fixture.json")


if __name__ == "__main__":
    unittest.main()
