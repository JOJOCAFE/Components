"""Tests for deterministic hierarchical circuit package planning."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from chiplib.circuit_hierarchy import (
    CircuitHierarchyError,
    discover_circuit_packages,
    flatten_circuit_hierarchy,
)
from chiplib.circuit_package import parse_circuit_package
from chiplib.circuit_runner import CircuitRunner


ROOT = Path(__file__).resolve().parents[2]


def package_data(package_id: str, chips: list[dict], ports: list[dict], wiring: list[dict]) -> dict:
    return {
        "schema": "components.lib.circuit",
        "version": 1,
        "id": package_id,
        "title": package_id,
        "source_project": {"name": "test", "paths": ["python/chiplib/core.py"]},
        "chips": chips,
        "ports": ports,
        "wiring": wiring,
        "verification": {"tests": ["python/tests/test_circuit_hierarchy.py"]},
    }


def fixtures():
    leaf_data = package_data(
        "leaf",
        [{"ref": "U1", "part": "74HC04", "role": "invert"}],
        [{"name": "IN", "direction": "input"}, {"name": "OUT", "direction": "output"}],
        [
            {"net": "IN", "connections": ["IN", "U1.1"]},
            {"net": "OUT", "connections": ["U1.2", "OUT"]},
        ],
    )
    leaf = parse_circuit_package(leaf_data, source_path=ROOT / "leaf.json")
    parent_data = package_data(
        "parent",
        [{
            "ref": "BLOCK",
            "part": "LeafPackage",
            "role": "child",
            "symbolic_endpoints": ["IN", "OUT"],
        }],
        [{"name": "A", "direction": "input"}, {"name": "Y", "direction": "output"}],
        [
            {"net": "A", "connections": ["A", "BLOCK.IN"]},
            {"net": "Y", "connections": ["BLOCK.OUT", "Y"]},
        ],
    )
    parent = parse_circuit_package(parent_data, source_path=ROOT / "parent.json")
    return leaf, parent, parent_data


class CircuitHierarchyTests(unittest.TestCase):
    def test_discovers_all_library_packages_by_directory_and_id(self) -> None:
        catalog = discover_circuit_packages()
        sources = {package.source_path for package in catalog.values()}
        self.assertEqual(23, len(sources))
        self.assertIn("RV8GR_BusOwnership", catalog)
        self.assertIn("rv8gr_bus_ownership", catalog)

    def test_flattens_explicit_mapping_with_stable_qualified_names(self) -> None:
        leaf, parent, _ = fixtures()
        plan = flatten_circuit_hierarchy(parent, {"LeafPackage": leaf})
        self.assertEqual((('IN', 'A'), ('OUT', 'Y')), plan.composites[0].port_nets)
        self.assertEqual("BLOCK.U1", plan.leaves[0].instance_path)
        self.assertEqual(("A", "BLOCK.IN", "BLOCK.OUT", "Y"), plan.nets)

    def test_flattens_explicit_bit_select_without_name_inference(self) -> None:
        leaf, _, _ = fixtures()
        parent_data = package_data(
            "bit_select_parent",
            [{"ref": "BLOCK", "part": "LeafPackage", "role": "child", "symbolic_endpoints": ["IN", "OUT"]}],
            [{"name": "IRH0..IRH7", "direction": "input"}, {"name": "Y", "direction": "output"}],
            [
                {"net": "ALU_SUB", "connections": ["IRH0..IRH7[3]", "BLOCK.IN"]},
                {"net": "Y", "connections": ["BLOCK.OUT", "Y"]},
            ],
        )
        parent = parse_circuit_package(parent_data, source_path=ROOT / "bit_select_parent.json")
        plan = flatten_circuit_hierarchy(parent, {"LeafPackage": leaf})
        self.assertEqual((("IN", "ALU_SUB"), ("OUT", "Y")), plan.composites[0].port_nets)

    def test_executes_explicit_child_mapping_on_one_shared_board(self) -> None:
        leaf, parent, _ = fixtures()
        runner = CircuitRunner.from_hierarchy(parent, {"LeafPackage": leaf})
        runner.set_input("A", 0)
        self.assertEqual(1, runner.read("Y"))
        runner.set_input("A", 1)
        self.assertEqual(0, runner.read("Y"))
        self.assertEqual({"BLOCK_U1"}, set(runner.board.chips))

    def test_executes_nested_explicit_mapping_on_the_same_board(self) -> None:
        leaf, parent, _ = fixtures()
        middle_data = package_data(
            "middle",
            [{"ref": "INNER", "part": "LeafPackage", "role": "child", "symbolic_endpoints": ["IN", "OUT"]}],
            [{"name": "IN", "direction": "input"}, {"name": "OUT", "direction": "output"}],
            [
                {"net": "IN", "connections": ["IN", "INNER.IN"]},
                {"net": "OUT", "connections": ["INNER.OUT", "OUT"]},
            ],
        )
        middle = parse_circuit_package(middle_data, source_path=ROOT / "middle.json")
        parent_data = deepcopy(parent.raw)
        parent_data["chips"][0]["part"] = "MiddlePackage"
        parent = parse_circuit_package(parent_data, source_path=ROOT / "nested_parent.json")
        runner = CircuitRunner.from_hierarchy(parent, {"LeafPackage": leaf, "MiddlePackage": middle})
        runner.set_input("A", 1)
        self.assertEqual(0, runner.read("Y"))
        self.assertEqual({"BLOCK_INNER_U1"}, set(runner.board.chips))

    def test_executes_explicit_bit_select_without_same_name_join(self) -> None:
        leaf, _, _ = fixtures()
        parent_data = package_data(
            "bit_select_execution",
            [{"ref": "BLOCK", "part": "LeafPackage", "role": "child", "symbolic_endpoints": ["IN", "OUT"]}],
            [{"name": "IRH0..IRH7", "direction": "input"}, {"name": "Y", "direction": "output"}],
            [
                {"net": "ALU_SUB", "connections": ["IRH0..IRH7[3]", "BLOCK.IN"]},
                {"net": "Y", "connections": ["BLOCK.OUT", "Y"]},
            ],
        )
        parent = parse_circuit_package(parent_data, source_path=ROOT / "bit_select_execution.json")
        runner = CircuitRunner.from_hierarchy(parent, {"LeafPackage": leaf})
        runner.set_input("IRH0..IRH7", 0)
        self.assertEqual(1, runner.read("Y"))
        runner.set_input("IRH0..IRH7", 0b00001000)
        self.assertEqual(0, runner.read("Y"))

    def test_rejects_missing_mapping_with_structured_diagnostic(self) -> None:
        leaf, _, parent_data = fixtures()
        parent_data["wiring"] = parent_data["wiring"][:1]
        parent = parse_circuit_package(parent_data, source_path=ROOT / "parent.json")
        with self.assertRaises(CircuitHierarchyError) as caught:
            flatten_circuit_hierarchy(parent, {"LeafPackage": leaf})
        payload = caught.exception.to_dict()
        self.assertEqual("invalid_circuit_hierarchy", payload["error"])
        self.assertIn("missing_child_port_mapping", {row["code"] for row in payload["issues"]})
        self.assertIn("BLOCK.OUT", {row["path"] for row in payload["issues"]})

    def test_rejects_duplicate_mapping_deterministically(self) -> None:
        leaf, _, parent_data = fixtures()
        parent_data["wiring"].append({"net": "A_COPY", "connections": ["BLOCK.IN"]})
        parent = parse_circuit_package(parent_data, source_path=ROOT / "parent.json")
        with self.assertRaises(CircuitHierarchyError) as caught:
            flatten_circuit_hierarchy(parent, {"LeafPackage": leaf})
        issue = next(row for row in caught.exception.issues if row.code == "duplicate_child_port_mapping")
        self.assertEqual("BLOCK.IN", issue.path)
        self.assertIn("A, A_COPY", issue.message)

    def test_detects_recursive_package_cycle(self) -> None:
        leaf, parent, _ = fixtures()
        loop_data = deepcopy(leaf.raw)
        loop_data["id"] = "loop"
        loop_data["chips"] = [{
            "ref": "SELF", "part": "LoopPackage", "role": "cycle",
            "symbolic_endpoints": ["IN", "OUT"],
        }]
        loop_data["wiring"] = [
            {"net": "IN", "connections": ["IN", "SELF.IN"]},
            {"net": "OUT", "connections": ["SELF.OUT", "OUT"]},
        ]
        loop = parse_circuit_package(loop_data, source_path=ROOT / "loop.json")
        with self.assertRaises(CircuitHierarchyError) as caught:
            flatten_circuit_hierarchy(loop, {"LoopPackage": loop, "LeafPackage": leaf, "Parent": parent})
        self.assertIn("hierarchy_cycle", {row.code for row in caught.exception.issues})

    def test_rejects_independent_proof_gate_instead_of_paralleling_children(self) -> None:
        leaf, _, _ = fixtures()
        gate_data = package_data(
            "proof_gate",
            [
                {"ref": "TRACE_A", "part": "LeafPackage", "role": "scenario A"},
                {"ref": "TRACE_B", "part": "LeafPackage", "role": "scenario B"},
            ],
            [{"name": "VCC", "direction": "power"}],
            [],
        )
        gate_data["behavior"] = {
            "coverage_rule": "This package references existing executable circuit proofs."
        }
        gate = parse_circuit_package(gate_data, source_path=ROOT / "proof_gate.json")
        with self.assertRaises(CircuitHierarchyError) as caught:
            flatten_circuit_hierarchy(gate, {"LeafPackage": leaf})
        self.assertEqual(
            {"independent_proof_scenarios_not_composable"},
            {row.code for row in caught.exception.issues},
        )
        self.assertIn("TRACE_A, TRACE_B", caught.exception.issues[0].message)

    def test_full_control_has_authoritative_child_port_mappings_and_constructs(self) -> None:
        catalog = discover_circuit_packages()
        package = catalog["RV8GR_FullControlOpcodeSweep"]
        plan = flatten_circuit_hierarchy(package, catalog)
        composites = {item.ref: dict(item.port_nets) for item in plan.composites}
        self.assertEqual({"BUS", "ALU", "PGDP", "PC", "PC16", "IEFF", "VT"}, set(composites))
        self.assertEqual("ALU_SUB", composites["ALU"]["ALU_SUB"])
        self.assertEqual("XOR_MODE", composites["PGDP"]["XOR_MODE"])
        self.assertEqual("Z_flag", composites["PC"]["Z_flag"])
        self.assertEqual("/PC_LD", composites["PC16"]["/PC_LD"])
        self.assertEqual("IE", composites["IEFF"]["IE"])
        self.assertEqual("VT_IBUS_OBSERVE", composites["VT"]["IBUS"])
        self.assertEqual("VT_DBUS_OBSERVE", composites["VT"]["DBUS"])
        # Construction validates every declared child port on one Board.  It is
        # deliberately not a 512-case promotion proof: the package documents
        # the remaining PC/address/memory state-boundary work separately.
        self.assertIsInstance(CircuitRunner.from_hierarchy(package, catalog), CircuitRunner)

    def test_full_control_exposes_real_pc_load_and_declared_ie_clock_sink(self) -> None:
        """Exercise the real strobe plus explicit U33-to-U31 edge contract."""
        catalog = discover_circuit_packages()
        runner = CircuitRunner.from_hierarchy(catalog["RV8GR_FullControlOpcodeSweep"], catalog)
        runner.set_input("/RST", 0)
        self.assertEqual(0, runner.read("IE"))
        runner.set_input("/RST", 1)

        # IRH bit 0 is JMP.  The concrete U26 path must lower /PC_LD in T2.
        runner.set_input("IRH0..IRH7", 0x01)
        runner.set_input("T2", 1)
        self.assertEqual(0, runner.read("/PC_LD"))

        # EI is $08: SRC=1, XOR_MODE=0, AC_WR=0.  The runner must not infer
        # arbitrary output clocks, so this only invokes the package-declared
        # U33-8 -> U31-3 source/sink edge after validating that concrete net.
        runner.set_input("T2", 0)
        runner.set_input("IRH0..IRH7", 0x08)
        runner.set_input("T2", 1)
        self.assertEqual(0, runner.read("IE"))
        runner.set_input("T2", 0)
        runner.set_input_with_declared_clock_edges("T2", 1)
        self.assertEqual(1, runner.read("IE"))

    def test_flat_pc16_has_powered_reset_load_and_increment_edges(self) -> None:
        """PC16 must receive real power/control pins after hierarchy flattening.

        This is intentionally a narrow state-boundary proof, not an opcode
        sweep promotion.  It proves the concrete U1-U4 chain can reset, load
        the documented {PG, IRL} target on a real /PC_LD edge, then increment
        on its next public CLK edge.
        """
        catalog = discover_circuit_packages()
        # This deliberately executes the PC16 hierarchy by itself.  FullControl
        # has live RAM/ROM/IBUS drivers and needs its own operation harness;
        # this proof must not inject values onto those root buses.
        runner = CircuitRunner.from_hierarchy(catalog["RV8GR_PC16"], catalog)

        # The physical supplies are explicit PC16 wiring, not implicit model
        # defaults.  Check the flattened live pins as well as public outputs.
        for ref in ("U1", "U2", "U3", "U4"):
            self.assertEqual(1, runner._chips[ref].read(16), ref)
            self.assertEqual(0, runner._chips[ref].read(8), ref)

        runner.set_input("/RST", 0)
        self.assertEqual((0,) * 16, runner.read("PC0..PC15"))
        runner.set_input("/RST", 1)
        runner.set_input("CLK", 0)
        runner.set_input("PC_INC", 0)
        runner.set_input("PG0..PG7", 0x12)
        runner.set_input("IRL0..IRL7", 0x34)

        # The documented active-low PC load input samples {PG, IRL}.
        runner.set_input("/PC_LD", 0)
        runner.pulse_clock("CLK", return_low=True)
        self.assertEqual(tuple((0x1234 >> bit) & 1 for bit in range(16)), runner.read("PC0..PC15"))

        # Return the load input inactive, then count through the same U1-U4 path.
        runner.set_input("/PC_LD", 1)
        runner.set_input("PC_INC", 1)
        runner.pulse_clock("CLK", return_low=True)
        self.assertEqual(tuple((0x1235 >> bit) & 1 for bit in range(16)), runner.read("PC0..PC15"))

    def test_whole_system_rejects_independent_trace_scenarios(self) -> None:
        catalog = discover_circuit_packages()
        with self.assertRaises(CircuitHierarchyError) as caught:
            flatten_circuit_hierarchy(catalog["RV8GR_WholeSystemChipLevelVirtual"], catalog)
        self.assertEqual(
            {"independent_proof_scenarios_not_composable"},
            {row.code for row in caught.exception.issues},
        )
        self.assertIn("BOOT", caught.exception.issues[0].message)
        self.assertIn("PAGE_JUMP", caught.exception.issues[0].message)


if __name__ == "__main__":
    unittest.main()
