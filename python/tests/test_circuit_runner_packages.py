"""Promotion gates for all circuit packages and batches A-G."""

from __future__ import annotations

from pathlib import Path
import unittest

from chiplib.circuit_proofs import (
    PROMOTION_BATCHES,
    audit_all_packages,
    audit_promotion_batches,
    circuit_package_names,
)


ROOT = Path(__file__).resolve().parents[2]

EXPECTED_BATCH_BLOCK_CODES = {
    "A": {"symbolic_aggregate_not_executable", "unresolved_output", "unsupported_port_direction"},
    "B": {"proof_vector_mismatch", "proof_internal_control_undriven"},
    "C": {"proof_adapter_not_implemented", "symbolic_aggregate_not_executable", "composite_not_executable"},
    "D": {"symbolic_aggregate_not_executable", "unresolved_output"},
    "E": {"ambiguous_range_width", "symbolic_aggregate_not_executable", "unresolved_output", "unsupported_port_direction"},
    "F": {"ambiguous_range_width", "symbolic_aggregate_not_executable", "unresolved_output"},
    "G": {"composite_not_executable", "symbolic_aggregate_not_executable", "unresolved_output"},
}

EXPECTED_BATCH_PACKAGES = {
    package
    for packages in PROMOTION_BATCHES.values()
    for package in packages
}


class CircuitRunnerPackagePromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.results = audit_all_packages()
        cls.by_name = {result.package: result for result in cls.results}

    def test_inventory_audits_all_22_packages_and_declared_proofs(self) -> None:
        self.assertEqual(22, len(circuit_package_names()))
        self.assertEqual(circuit_package_names(), tuple(result.package for result in self.results))
        for result in self.results:
            with self.subTest(package=result.package):
                self.assertTrue(result.circuit_path.is_file())
                self.assertTrue(result.proof_paths)
                self.assertTrue(all(path.is_file() for path in result.proof_paths))
                self.assertTrue(all(ROOT in path.parents for path in result.proof_paths))

    def test_ring_counter_is_promoted_only_by_declared_live_execution(self) -> None:
        promoted = [result for result in self.results if result.promoted]
        self.assertEqual(["RV8GR_RingCounter"], [result.package for result in promoted])
        proof = self.by_name["RV8GR_RingCounter"].observations
        self.assertEqual({"T0": 0, "T1": 0, "T2": 0}, proof["reset"])
        self.assertEqual(
            ({"T0": 1, "T1": 0, "T2": 0}, {"T0": 0, "T1": 1, "T2": 0}, {"T0": 0, "T1": 0, "T2": 1}),
            proof["sequence"],
        )
        self.assertTrue(all(
            item["source"] == "live_db_package"
            for item in proof["snapshot"]["provenance"].values()
        ))
    def test_loadable_but_unproved_packages_remain_explicitly_blocked(self) -> None:
        expected = {
            "RV8GR_AluAccumulator": "proof_state_not_executable",
            "RV8GR_BranchJumpControl": "proof_vector_mismatch",
            "RV8GR_IRQLatch": "proof_clock_driver_conflict",
            "RV8GR_RomDbusRead": "proof_rom_image_not_loadable",
            "RV8GR_StorePath": "proof_internal_control_undriven",
        }
        for package, code in expected.items():
            with self.subTest(package=package):
                result = self.by_name[package]
                self.assertFalse(result.promoted)
                self.assertEqual([code], [block.code for block in result.blocks])
                self.assertIn("tests/", result.blocks[0].path)

    def test_every_nonexecuted_package_has_structured_runner_blocks(self) -> None:
        for result in self.results:
            if result.promoted:
                continue
            with self.subTest(package=result.package):
                self.assertEqual("blocked", result.status)
                self.assertFalse(result.observations)
                self.assertTrue(result.blocks)
                self.assertTrue(all(block.code and block.path and block.message for block in result.blocks))

    def test_batches_a_through_g_are_complete_and_explicitly_blocked(self) -> None:
        self.assertEqual(tuple("ABCDEFG"), tuple(PROMOTION_BATCHES))
        self.assertEqual(13, sum(len(packages) for packages in PROMOTION_BATCHES.values()))
        batches = audit_promotion_batches()
        observed_packages = {item.package for results in batches.values() for item in results}
        self.assertEqual(EXPECTED_BATCH_PACKAGES, observed_packages)
        for batch, results in batches.items():
            with self.subTest(batch=batch):
                self.assertEqual(PROMOTION_BATCHES[batch], tuple(item.package for item in results))
                self.assertTrue(all(item.status == "blocked" for item in results))
                codes = {block.code for item in results for block in item.blocks}
                self.assertEqual(EXPECTED_BATCH_BLOCK_CODES[batch], codes)

    def test_blocks_name_exact_package_json_paths(self) -> None:
        for batch_results in audit_promotion_batches().values():
            for result in batch_results:
                with self.subTest(package=result.package):
                    self.assertEqual(
                        ROOT / "Lib" / "Circuits" / result.package / "circuit.json",
                        result.circuit_path,
                    )
                    self.assertEqual(
                        (ROOT / "Lib" / "Circuits" / result.package / "tests" / f"{result.circuit_id.removeprefix('rv8gr_')}.json",),
                        result.proof_paths,
                    )
                    self.assertTrue(all(
                        block.path.startswith("$.") or "tests/" in block.path
                        for block in result.blocks
                    ))


if __name__ == "__main__":
    unittest.main()
