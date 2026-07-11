"""Executable promotion audit for circuit packages and their proof files."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from .circuit_package import CIRCUIT_ROOT, CircuitPackage, load_circuit_package
from .circuit_runner import CircuitRunnerError, load_circuit_runner


PROMOTION_BATCHES: Mapping[str, tuple[str, ...]] = {
    "A": ("RV8GR_VirtualTestHelpers",),
    "B": ("RV8GR_BranchJumpControl", "RV8GR_StorePath"),
    "C": (
        "RV8GR_ResetClockBringup",
        "RV8GR_BusOwnership",
        "RV8GR_FullControlOpcodeSweep",
    ),
    "D": ("RV8GR_FetchCycleTrace",),
    "E": (
        "RV8GR_StoreLoadBranchTrace",
        "RV8GR_PageJumpTrace",
        "RV8GR_InterruptTrace",
    ),
    "F": ("RV8GR_BootSequenceTrace", "RV8GR_Lab13MarkerTrace"),
    "G": ("RV8GR_WholeSystemChipLevelVirtual",),
}


@dataclass(frozen=True)
class PromotionBlock:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class PackagePromotion:
    package: str
    circuit_id: str
    circuit_path: Path
    proof_paths: tuple[Path, ...]
    status: str
    observations: Mapping[str, Any]
    blocks: tuple[PromotionBlock, ...] = ()

    @property
    def promoted(self) -> bool:
        return self.status == "promoted"


class _ProofBlocked(RuntimeError):
    def __init__(self, *blocks: PromotionBlock):
        self.blocks = blocks
        super().__init__("; ".join(block.message for block in blocks))


def circuit_package_names() -> tuple[str, ...]:
    """Return every package with a circuit definition, in stable order."""

    return tuple(path.parent.name for path in sorted(CIRCUIT_ROOT.glob("*/circuit.json")))


def promotion_batch(package: str) -> str | None:
    for batch, packages in PROMOTION_BATCHES.items():
        if package in packages:
            return batch
    return None


def audit_package(package: str) -> PackagePromotion:
    """Compile and execute a package through public runner interfaces.

    A structurally valid proof JSON is supporting evidence only. It never
    substitutes for runner execution and therefore cannot turn a block into a
    promoted result.
    """

    circuit_path = CIRCUIT_ROOT / package / "circuit.json"
    parsed = load_circuit_package(circuit_path)
    proof_paths = _load_declared_proofs(parsed)
    try:
        runner = load_circuit_runner(circuit_path)
    except CircuitRunnerError as exc:
        return PackagePromotion(
            package=package,
            circuit_id=parsed.id,
            circuit_path=circuit_path,
            proof_paths=proof_paths,
            status="blocked",
            observations={},
            blocks=tuple(PromotionBlock(item.code, item.path, item.message) for item in exc.issues),
        )

    try:
        observations = _execute_live_smoke(package, runner, proof_paths)
    except _ProofBlocked as exc:
        return PackagePromotion(
            package=package,
            circuit_id=parsed.id,
            circuit_path=circuit_path,
            proof_paths=proof_paths,
            status="blocked",
            observations={},
            blocks=exc.blocks,
        )
    return PackagePromotion(
        package=package,
        circuit_id=parsed.id,
        circuit_path=circuit_path,
        proof_paths=proof_paths,
        status="promoted",
        observations=observations,
    )


def audit_all_packages() -> tuple[PackagePromotion, ...]:
    return tuple(audit_package(package) for package in circuit_package_names())


def audit_promotion_batches() -> Mapping[str, tuple[PackagePromotion, ...]]:
    return {
        batch: tuple(audit_package(package) for package in packages)
        for batch, packages in PROMOTION_BATCHES.items()
    }


def _load_declared_proofs(package: CircuitPackage) -> tuple[Path, ...]:
    paths: list[Path] = []
    for reference in package.verification:
        data = json.loads(reference.resolved_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("circuit") != package.id:
            raise ValueError(
                f"{reference.resolved_path}: proof circuit must equal {package.id!r}"
            )
        paths.append(reference.resolved_path)
    if not paths:
        raise ValueError(f"{package.source_path}: no declared proof JSON")
    return tuple(paths)


def _execute_live_smoke(
    package: str, runner: Any, proof_paths: tuple[Path, ...]
) -> Mapping[str, Any]:
    if package == "RV8GR_RingCounter":
        reset = runner.reset()
        runner.set_input("/CLR", 1)
        sequence = tuple(runner.pulse_clock() for _ in range(3))
        expected = (
            {"T0": 1, "T1": 0, "T2": 0},
            {"T0": 0, "T1": 1, "T2": 0},
            {"T0": 0, "T1": 0, "T2": 1},
        )
        if reset != {"T0": 0, "T1": 0, "T2": 0} or sequence != expected:
            raise AssertionError(f"{package}: live ring-counter proof mismatch")
        return {"reset": reset, "sequence": sequence, "snapshot": runner.snapshot()}

    if package == "RV8GR_BranchJumpControl":
        return _prove_branch_jump(runner, proof_paths[0])

    proof_path = str(proof_paths[0])
    blockers = {
        "RV8GR_AluAccumulator": PromotionBlock(
            "proof_state_not_executable",
            f"{proof_path}#$.vectors[*].start_ac",
            "declared vectors require accumulator state injection, but the public runner has no state-load API; IBUS stimulus also conflicts with the initially enabled U14 output",
        ),
        "RV8GR_IRQLatch": PromotionBlock(
            "proof_clock_driver_conflict",
            f"{proof_path}#$.vectors[1].event",
            "EI_decode rising cannot be driven through the public runner because package net EI_decode is also driven LOW by U33.8",
        ),
        "RV8GR_RomDbusRead": PromotionBlock(
            "proof_rom_image_not_loadable",
            f"{proof_path}#$.rom_image",
            "declared ROM bytes cannot be loaded through the public runner API, so fetch-byte vectors cannot be executed",
        ),
        "RV8GR_StorePath": PromotionBlock(
            "proof_internal_control_undriven",
            f"{proof_path}#$.vectors[*]",
            "declared /AC_BUF, WR_DIR, and RAM /WE expectations are not executable because their package nets have no concrete control drivers; AC stimulus produces live bus contention",
        ),
    }
    if package in blockers:
        raise _ProofBlocked(blockers[package])

    # Generic execution is deliberately weak and cannot promote a package with
    # package-specific state or vector requirements. Keep this fail-loudly as
    # new runner support lands instead of awarding a final-state-only pass.
    raise _ProofBlocked(PromotionBlock(
        "proof_adapter_not_implemented",
        f"{proof_paths[0]}#$",
        f"{package} loads, but no package-specific adapter executes its declared proof vectors",
    ))


def _prove_branch_jump(runner: Any, proof_path: Path) -> Mapping[str, Any]:
    data = json.loads(proof_path.read_text(encoding="utf-8"))
    checks: list[dict[str, Any]] = []
    for index, vector in enumerate(data["vectors"]):
        session = type(runner).load(runner.package.source_path)
        phase = vector["phase"]
        for name in ("T0", "T1", "T2"):
            session.set_input(name, int(name == phase))
        for field, port in (
            ("jmp", "JMP"),
            ("br", "BR"),
            ("z_flag", "Z_flag"),
            ("alu_sub", "ALU_SUB"),
        ):
            session.set_input(port, vector[field])

        snapshot = session.snapshot()
        nets = {item["name"]: item["value"] for item in snapshot["board"]["nets"]}
        actual = {
            "z_match": nets["Z_match"],
            "br_taken": 1 - nets["/BR_TAKEN"],
            "pc_load_cond": nets["PC_LOAD_COND"],
            "pc_ld_n": session.read("/PC_LD"),
        }
        expected = {
            "z_match": vector["expect_z_match"],
            "br_taken": vector["expect_br_taken"],
            "pc_load_cond": vector["expect_pc_load_cond"],
            "pc_ld_n": vector["expect_pc_ld_n"],
        }
        checks.append({
            "name": vector["name"],
            "vector_index": index,
            "passed": actual == expected and not snapshot["board"]["errors"],
            "expected": expected,
            "actual": actual,
            "board_errors": snapshot["board"]["errors"],
        })

    failed = [check for check in checks if not check["passed"]]
    if failed:
        first = failed[0]
        raise _ProofBlocked(PromotionBlock(
            "proof_vector_mismatch",
            f"{proof_path}#$.vectors[{first['vector_index']}]",
            f"live result for {first['name']!r} does not match the declared vector",
        ))
    return {
        "proof": str(proof_path),
        "vectors_executed": len(checks),
        "checks": tuple(checks),
        "provenance": runner.snapshot()["provenance"],
    }
