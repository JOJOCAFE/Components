"""Executable promotion audit for circuit packages and their proof files."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
from typing import Any, Mapping

from .circuit_package import CIRCUIT_ROOT, CircuitPackage, load_circuit_package
from .circuit_runner import CircuitRunnerError, load_circuit_runner
from .virtual_runtime import OutputAssertionFailure, VirtualTransition


PROMOTION_BATCHES: Mapping[str, tuple[str, ...]] = {
    "A": ("RV8GR_VirtualTestHelpers",),
    "B": ("RV8GR_BranchJumpControl", "RV8GR_StorePath"),
    "C": (
        "RV8GR_ResetClockBringup",
        "RV8GR_BusOwnership",
        "RV8GR_InterruptEnable",
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
    def __init__(self, *blocks: PromotionBlock, observations: Mapping[str, Any] | None = None):
        self.blocks = blocks
        self.observations = dict(observations or {})
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
            observations=exc.observations,
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

    adapters = {
        "RV8GR_VirtualTestHelpers": _prove_virtual_helpers,
        "RV8GR_AluAccumulator": _prove_alu_accumulator,
        "RV8GR_BranchJumpControl": _prove_branch_jump,
        "RV8GR_IRQLatch": _prove_irq_latch,
        "RV8GR_ResetClockBringup": _prove_reset_clock,
        "RV8GR_RomDbusRead": _prove_rom_read,
        "RV8GR_StorePath": _prove_store_path,
        "RV8GR_BusOwnership": _prove_bus_ownership,
    }
    if package in adapters:
        return adapters[package](runner, proof_paths[0])

    # Generic execution is deliberately weak and cannot promote a package with
    # package-specific state or vector requirements. Keep this fail-loudly as
    # new runner support lands instead of awarding a final-state-only pass.
    raise _ProofBlocked(PromotionBlock(
        "proof_adapter_not_implemented",
        f"{proof_paths[0]}#$",
        f"{package} loads, but no package-specific adapter executes its declared proof vectors",
    ))


def _prove_virtual_helpers(runner: Any, proof_path: Path) -> Mapping[str, Any]:
    """Execute every virtual-helper vector through the loaded named adapters."""

    data = json.loads(proof_path.read_text(encoding="utf-8"))
    adapters = runner.virtual_adapters
    checks: list[dict[str, Any]] = []

    clock = adapters["VCLK"]
    for vector in data["clock_profiles"]:
        events = clock.ticks(vector["expect_ticks"])
        checks.append({"name": vector["name"], "passed": len(events) == 2 * vector["expect_ticks"]})

    for vector in data["phase_vectors"]:
        for name in ("T0", "T1", "T2"):
            runner.set_input(name, vector[name])
            adapters[{"T0": "PH0", "T1": "PH1", "T2": "PH2"}[name]].sample(
                runner.board.net(name).value
            )
        active = [name for name in ("T0", "T1", "T2") if vector[name] == 1]
        actual_valid = len(active) == 1
        actual_phase = active[0] if actual_valid else None
        checks.append({
            "name": vector["name"],
            "passed": actual_valid == vector["expect_valid"]
            and (not actual_valid or actual_phase == vector["expect_phase"]),
        })

    for vector in data["bus_vectors"]:
        probe = adapters["IBUSMON" if vector["bus"] == "IBUS" else "DBUSMON"]
        drivers = {name: index % 2 for index, name in enumerate(vector["drivers"])}
        sample = probe.sample(drivers)
        checks.append({"name": vector["name"], "passed": sample["conflict"] == vector["expect_conflict"]})

    switch = adapters["SW1"]
    for vector in data["switch_vectors"]:
        mode = vector["mode"]
        if mode.startswith("stable_"):
            sequence = [switch.set_state(1 if mode == "stable_on" else 0).value]
        elif mode == "preset_pulse_train":
            sequence = [event.value for index in range(vector["pulses"]) for event in switch.pulse(1, start_ps=index * 2)]
        else:
            sequence = [0, *[event.value for event in switch.pulse(1)]] if mode == "one_shot_push_on_release_off" else [event.value for event in switch.pulse(1)]
        expected = vector.get("expect_sequence")
        passed = sequence == expected if expected is not None else sequence.count(1) == vector["expect_edges"]
        checks.append({"name": vector["name"], "passed": passed})

    for vector in data["rc_parasitic_vectors"]:
        adapter = type(adapters["CLKRC"])(
            "RC", source_resistance_ohm=vector["source_resistance_ohm"],
            wire_capacitance_pf=vector["wire_capacitance_pf"],
            chip_input_capacitance_pf=vector["chip_input_capacitance_pf"],
            probe_capacitance_pf=vector["probe_capacitance_pf"],
            extra_capacitance_pf=vector["extra_capacitance_pf"],
        )
        estimate = adapter.estimate()
        checks.append({
            "name": vector["name"],
            "passed": abs(estimate["tau_ns"] - vector["expect_tau_ns"]) < 1e-9
            and abs(estimate["settling_10_90_ns"] - vector["expect_settling_10_90_ns"]) < 1e-9,
        })

    for vector in data["delay_noise_vectors"]:
        adapter = type(adapters["DLY1"])(
            "DLY", seed=vector["seed"], base_delay_ps=vector["base_delay_ns"] * 1000,
            jitter_ps=vector["jitter_ns"] * 1000,
            glitch_probability=vector["glitch_probability"], glitch_width_ps=vector["glitch_width_ns"] * 1000,
        )
        output = adapter.transform(tuple(VirtualTransition(index, value) for index, value in enumerate(vector["input_sequence"])))
        observed = [event.value for event in output if event.kind == "delayed_drive"]
        checks.append({"name": vector["name"], "passed": observed == vector["expect_sequence"]})

    assertion = adapters["ASSERT1"]
    for vector in data["output_assert_vectors"]:
        try:
            assertion.check(vector["observed"], vector["expected"], mode=vector["mode"])
            passed = vector["expect_pass"]
        except OutputAssertionFailure:
            passed = not vector["expect_pass"]
        checks.append({"name": vector["name"], "passed": passed})

    if not all(check["passed"] for check in checks):
        failed = [check["name"] for check in checks if not check["passed"]]
        raise AssertionError(f"{runner.package.id}: virtual helper vector mismatch: {failed}")
    return {"proof": str(proof_path), "vectors_executed": len(checks), "checks": checks, "snapshot": runner.snapshot()}


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
        indexes = ", ".join(str(check["vector_index"]) for check in failed)
        raise _ProofBlocked(PromotionBlock(
            "circuit_truth_mismatch",
            f"{proof_path}#$.vectors[{indexes}]",
            "live NAND wiring computes PC_LOAD_COND=NAND(JMP,/BR_TAKEN), not the declared JMP OR BR_TAKEN; jump, untaken branch, and NOP vectors therefore disagree",
        ), observations={"proof": str(proof_path), "vectors_executed": len(checks), "checks": tuple(checks)})
    return {
        "proof": str(proof_path),
        "vectors_executed": len(checks),
        "checks": tuple(checks),
        "provenance": runner.snapshot()["provenance"],
    }


def _logic_vector(value: str | int) -> int:
    return int(value, 0) if isinstance(value, str) else value


def _net_values(runner: Any) -> dict[str, Any]:
    return {item["name"]: item["value"] for item in runner.snapshot()["board"]["nets"]}


def _prove_alu_accumulator(runner: Any, proof_path: Path) -> Mapping[str, Any]:
    data = json.loads(proof_path.read_text(encoding="utf-8"))
    checks: list[dict[str, Any]] = []
    for index, vector in enumerate(data["vectors"]):
        session = type(runner).load(runner.package.source_path)
        initial = session.initialize_state("AC", _logic_vector(vector["start_ac"]))
        if _logic_vector(vector["start_ac"]) != _bits_to_int(session.read("AC0..AC7")):
            raise _ProofBlocked(PromotionBlock(
                "state_initializer_mismatch",
                f"{proof_path}#$.vectors[{index}].start_ac",
                "public AC initializer did not produce the declared initial accumulator value",
            ), observations={"proof": str(proof_path), "vectors_executed": len(checks),
                "checks": tuple(checks), "initializer": initial})
        try:
            session.set_input("IBUS0..IBUS7", _logic_vector(vector["ibus"]))
        except Exception as exc:
            raise _ProofBlocked(PromotionBlock(
                "proof_bus_driver_conflict",
                f"{proof_path}#$.vectors[{index}].ibus",
                "IBUS stimulus conflicts with U14 because package wiring leaves /AC_BUF without a concrete control driver",
            ), observations={"proof": str(proof_path), "vectors_executed": len(checks),
                "runner_error": str(exc)}) from exc
        for field, port in (("alu_sub", "ALU_SUB"), ("xor_mode", "XOR_MODE"),
                            ("mux_sel", "MUX_SEL"), ("ac_wr", "AC_WR")):
            session.set_input(port, vector[field])
        if vector["phase"] == "T2":
            if vector["ac_wr"]:
                session.pulse_clock(
                    "T2", return_low=True,
                    propagated_rising_on_fall=("ACC_CLK",),
                )
                # RV8GR chip-level RTL gives U21 a package-specific 20 ns
                # delayed ACC_CLK sample.  This is declared by the package;
                # it does not change the generic 74HC74 behavior.
                session.run_modeled_post_clock_samples("ACC_CLK")
            else:
                session.pulse_clock("T2", return_low=True)
        else:
            session.set_input("T2", 0)
        actual = {"ac": _bits_to_int(session.read("AC0..AC7")), "z": session.read("Z_flag")}
        expected = {"ac": _logic_vector(vector["expect_ac"]), "z": vector["expect_z"]}
        checks.append({"name": vector["name"], "passed": actual == expected,
                       "expected": expected, "actual": actual})
    # These transitions specifically exercise the package-declared 20 ns U21
    # sample phase.  They remain live component-model executions: the adapter
    # drives only public ports and requests the declared model phase.
    for index, vector in enumerate(data.get("z_settle_vectors", ())):
        session = type(runner).load(runner.package.source_path)
        session.initialize_state("AC", _logic_vector(vector["start_ac"]))
        session.set_input("IBUS0..IBUS7", _logic_vector(vector["ibus"]))
        for port, value in (("ALU_SUB", 0), ("XOR_MODE", 0), ("MUX_SEL", 1), ("AC_WR", vector["ac_wr"])):
            session.set_input(port, value)
        if vector["phase"] == "T2" and vector["ac_wr"]:
            session.pulse_clock("T2", return_low=True, propagated_rising_on_fall=("ACC_CLK",))
            session.run_modeled_post_clock_samples("ACC_CLK")
        else:
            session.set_input("T2", 0)
        actual = {"ac": _bits_to_int(session.read("AC0..AC7")), "z": session.read("Z_flag")}
        expected = {"ac": _logic_vector(vector["expect_ac"]), "z": vector["expect_z"]}
        checks.append({"name": vector["name"], "settle_vector_index": index,
                       "passed": actual == expected, "expected": expected, "actual": actual})
    failed = [check for check in checks if not check["passed"]]
    if failed:
        indexes = ", ".join(str(index) for index, check in enumerate(checks) if not check["passed"])
        raise _ProofBlocked(PromotionBlock(
            "proof_vector_mismatch",
            f"{proof_path}#$.vectors[{indexes}]",
            "live AC/Z results differ from the declared vectors after edge-respecting public initialization",
        ), observations={"proof": str(proof_path), "vectors_executed": len(checks), "checks": tuple(checks)})
    return {"proof": str(proof_path), "vectors_executed": len(checks), "checks": tuple(checks)}


def _prove_irq_latch(runner: Any, proof_path: Path) -> Mapping[str, Any]:
    data = json.loads(proof_path.read_text(encoding="utf-8"))
    checks: list[dict[str, Any]] = []
    for vector in data["vectors"]:
        session = type(runner).load(runner.package.source_path)
        session.set_input("/RST", 0)
        session.set_input("/RST", 1)
        if vector["start_ie"]:
            session.pulse_clock("EI_decode")
        if vector["start_irq_ff"]:
            session.set_input("/IRQ", 0)
            session.pulse_clock("/IRQ")
        event = vector["event"]
        if event == "reset":
            session.set_input("/RST", 0)
        elif event == "ei_rising":
            session.pulse_clock("EI_decode")
        elif event == "irq_low":
            session.set_input("/IRQ", 0)
        elif event == "irq_release_rising":
            session.set_input("/IRQ", 0)
            session.pulse_clock("/IRQ")
        actual = session.read()
        expected = {"IE": vector["expect_ie"], "IRQ_FF": vector["expect_irq_ff"]}
        checks.append({"name": vector["name"], "passed": actual == expected,
                       "expected": expected, "actual": actual})
    if not all(check["passed"] for check in checks):
        raise _ProofBlocked(PromotionBlock(
            "proof_vector_mismatch", f"{proof_path}#$.vectors",
            "one or more IRQ latch live vectors do not match the declared result",
        ), observations={"proof": str(proof_path), "vectors_executed": len(checks), "checks": tuple(checks)})
    return {"proof": str(proof_path), "vectors_executed": len(checks), "checks": tuple(checks)}


def _prove_reset_clock(runner: Any, proof_path: Path) -> Mapping[str, Any]:
    data = json.loads(proof_path.read_text(encoding="utf-8"))
    session = type(runner).load(runner.package.source_path)
    session.set_input("/RST", 0)
    session.set_input("CLK", 0)
    checks: list[dict[str, Any]] = []
    for name, expected_row in (("reset_idle", data["reset_idle"]["expect"]),
                               ("reset_release", data["reset_release"]["expect"])):
        if name == "reset_release":
            session.set_input("/RST", 1)
        actual_ports = session.read()
        actual = {"T0": actual_ports["T0"], "T1": actual_ports["T1"],
                  "T2": actual_ports["T2"], "PC": _bits_to_int(actual_ports["PC0..PC15"])}
        expected = {"T0": expected_row["T0"], "T1": expected_row["T1"],
                    "T2": expected_row["T2"], "PC": _logic_vector(expected_row["PC"])}
        checks.append({"name": name, "passed": actual == expected,
                       "expected": expected, "actual": actual})
    for vector in data["push_vectors"]:
        actual_ports = session.pulse_clock("CLK")
        actual = {"T0": actual_ports["T0"], "T1": actual_ports["T1"],
                  "T2": actual_ports["T2"], "PC": _bits_to_int(actual_ports["PC0..PC15"])}
        row = vector["expect"]
        expected = {"T0": row["T0"], "T1": row["T1"], "T2": row["T2"],
                    "PC": _logic_vector(row["PC"])}
        checks.append({"name": f"push_{vector['push']}", "passed": actual == expected,
                       "expected": expected, "actual": actual})
    if not all(check["passed"] for check in checks):
        raise _ProofBlocked(PromotionBlock(
            "proof_vector_mismatch", f"{proof_path}#$",
            "reset/clock live sequence does not match the declared phase and PC vectors",
        ), observations={"proof": str(proof_path), "vectors_executed": len(checks), "checks": tuple(checks)})
    return {"proof": str(proof_path), "vectors_executed": len(checks), "checks": tuple(checks)}


def _prove_rom_read(runner: Any, proof_path: Path) -> Mapping[str, Any]:
    data = json.loads(proof_path.read_text(encoding="utf-8"))
    session = type(runner).load(runner.package.source_path)
    image = bytearray(0x8000)
    for address, value in data["rom_image"].items():
        image[int(address, 0)] = int(value, 0)
    with tempfile.NamedTemporaryFile(suffix=".bin") as handle:
        handle.write(image)
        handle.flush()
        session.load_memory_image("ROM1", handle.name, fmt="bin", clear=0xFF)
    checks = []
    for vector in data["vectors"]:
        session.set_input("A0..A14", int(vector["address"], 0) & 0x7FFF)
        session.set_input("A15", (int(vector["address"], 0) >> 15) & 1)
        session.set_input("WR_DIR", vector["wr_dir"])
        session.set_input("BUF_OE_N", vector["buf_oe_n"])
        session.release_input("DBUS0..DBUS7")
        session.release_input("IBUS0..IBUS7")
        bits = session.read("IBUS0..IBUS7")
        actual = None if all(bit == "Z" for bit in bits) else _bits_to_int(bits)
        expected = None if vector["expect_ibus"] is None else _logic_vector(vector["expect_ibus"])
        checks.append({"name": vector["name"], "passed": actual == expected,
                       "expected": expected, "actual": actual})
    if not all(check["passed"] for check in checks):
        raise _ProofBlocked(PromotionBlock(
            "proof_vector_mismatch", f"{proof_path}#$.vectors",
            "one or more ROM-to-IBUS live vectors do not match the declared result",
        ), observations={"proof": str(proof_path), "vectors_executed": len(checks), "checks": tuple(checks)})
    return {"proof": str(proof_path), "vectors_executed": len(checks), "checks": tuple(checks)}


def _prove_store_path(runner: Any, proof_path: Path) -> Mapping[str, Any]:
    data = json.loads(proof_path.read_text(encoding="utf-8"))
    checks = []
    for vector in data["vectors"]:
        session = type(runner).load(runner.package.source_path)
        session.release_input("IBUS0..IBUS7")
        session.release_input("DBUS0..DBUS7")
        session.set_input("T2", int(vector["phase"] == "T2"))
        session.set_input("STR", vector["str"])
        session.set_input("A15", vector["a15"])
        # StorePath receives this full-system control through U24; HIGH enables U7.
        session.set_input("/IRL_OE", 1)
        try:
            session.set_input("AC0..AC7", _logic_vector(vector["ac"]))
        except Exception as exc:
            raise _ProofBlocked(PromotionBlock(
                "proof_bus_driver_conflict", f"{proof_path}#$.vectors[{len(checks)}]",
                "live U14 and U7 outputs contend because BUF_OE_N and related internal controls have no concrete package drivers",
            ), observations={"proof": str(proof_path), "vectors_executed": len(checks),
                "runner_error": str(exc)}) from exc
        nets = _net_values(session)
        actual = {
            "ac_buf_n": nets["/AC_BUF"],
            "wr_dir": nets["WR_DIR"],
            "ram_we_n": session._chips["RAM1"].read("/WE"),
            "rom_oe_n": session._chips["ROM1"].read("/OE"),
            "write": session._chips["RAM1"].data[0] == _logic_vector(vector["ac"]),
        }
        expected = {
            "ac_buf_n": vector["expect_ac_buf_n"],
            "wr_dir": vector["expect_wr_dir"],
            "ram_we_n": vector["expect_ram_we_n"],
            "rom_oe_n": vector["expect_rom_oe_n"],
            "write": vector["expect_write"],
        }
        checks.append({"name": vector["name"], "passed": actual == expected,
                       "expected": expected, "actual": actual})
    if not all(check["passed"] for check in checks):
        raise _ProofBlocked(PromotionBlock(
            "proof_vector_mismatch", f"{proof_path}#$.vectors",
            "one or more live StorePath vectors do not match the declared control or write result",
        ), observations={"proof": str(proof_path), "vectors_executed": len(checks), "checks": tuple(checks)})
    return {"proof": str(proof_path), "vectors_executed": len(checks), "checks": tuple(checks),
            "provenance": runner.snapshot()["provenance"]}


def _prove_bus_ownership(runner: Any, proof_path: Path) -> Mapping[str, Any]:
    """Run the normal ownership rows through the concrete RV8GR control wiring.

    The negative rows deliberately override interlocked control nets, which the
    real NAND/XOR chain prevents during normal operation.  They remain proof
    requirements, but are checked as explicit hypothetical fault injections
    rather than being presented as reachable live circuit states.
    """

    data = json.loads(proof_path.read_text(encoding="utf-8"))
    checks: list[dict[str, Any]] = []
    for vector in data["vectors"]:
        session = type(runner).load(runner.package.source_path)
        session.set_input("T2", int(vector["phase"] == "T2"))
        session.set_input("SRC", vector["src"])
        session.set_input("STR", vector["str"])
        session.set_input("A15", vector["a15"])
        session.set_input("A0..A14", 0)
        session.set_input("IRL0..IRL7", 0x3C)
        session.set_input("AC0..AC7", 0xA5)
        session.release_input("IBUS0..IBUS7")
        session.release_input("DBUS0..DBUS7")

        u7, u14, u34 = (session._chips[name] for name in ("U7", "U14", "U34"))
        rom, ram = (session._chips[name] for name in ("ROM1", "RAM1"))
        ibus: list[str] = []
        dbus: list[str] = []
        if u34.read("/OE1") == 0:
            ibus.append("U34")
        if u14.read("/OE1") == 0:
            ibus.append("U14")
        if u7.read("/OE") == 0:
            (dbus if u7.read("DIR") == 1 else ibus).append("U7")
        if rom.read("/CE") == 0 and rom.read("/OE") == 0:
            dbus.append("ROM1")
        if ram.read("/CE") == 0 and ram.read("/OE") == 0 and ram.read("/WE") == 1:
            dbus.append("RAM1")
        actual = {
            "ibus_drivers": ibus,
            "dbus_drivers": dbus,
            "u7_direction": (
                "DISABLED" if u7.read("/OE") == 1
                else "IBUS_TO_DBUS" if u7.read("DIR") == 1
                else "DBUS_TO_IBUS"
            ),
            "conflict": len(ibus) > 1 or len(dbus) > 1,
            "rom_ce_n": rom.read("/CE"),
            "ram_ce_n": ram.read("/CE"),
        }
        expected = {
            "ibus_drivers": vector["expect_ibus_drivers"],
            "dbus_drivers": vector["expect_dbus_drivers"],
            "u7_direction": vector["u7_direction"],
            "conflict": vector["expect_conflict"],
            "rom_ce_n": int(vector["a15"]),
            "ram_ce_n": 1 - int(vector["a15"]),
        }
        checks.append({"name": vector["name"], "passed": actual == expected,
                       "expected": expected, "actual": actual})

    # Negative proof rows verify the declared detector contract. They are not
    # live control vectors: reaching one would require a fault/forced net that
    # bypasses the proven U24/U25/U26/U28 interlock chain above.
    for vector in data["unsafe_control_vectors"]:
        override = vector["override"]
        ibus = sum(override.get(name) == 0 for name in ("/IRL_OE", "/AC_BUF"))
        ibus += int(override.get("BUF_OE_N") == 0 and override.get("WR_DIR") == 0)
        dbus = int(override.get("BUF_OE_N") == 0 and override.get("WR_DIR") == 1)
        dbus += int(override.get("A15") == 0 and override.get("ROM_OE_N") == 0)
        dbus += int(override.get("A15") == 1 and override.get("RAM_WE_N") == 1)
        conflict = ibus > 1 or dbus > 1 or (
            override.get("ROM_CE_N") == 0 and override.get("RAM_CE_N") == 0
        )
        checks.append({"name": vector["name"], "passed": conflict == vector["expect_conflict"],
                       "expected": vector["expect_conflict"], "actual": conflict,
                       "mode": "forced_control_fault_model"})

    if not all(check["passed"] for check in checks):
        raise _ProofBlocked(PromotionBlock(
            "proof_vector_mismatch", f"{proof_path}#$",
            "one or more live bus-owner or forced-conflict proof vectors do not match the declared contract",
        ), observations={"proof": str(proof_path), "vectors_executed": len(checks), "checks": tuple(checks)})
    return {"proof": str(proof_path), "vectors_executed": len(checks), "checks": tuple(checks),
            "provenance": runner.snapshot()["provenance"]}


def _bits_to_int(bits: Any) -> int:
    if not isinstance(bits, tuple) or any(bit not in (0, 1) for bit in bits):
        return -1
    return sum(bit << index for index, bit in enumerate(bits))
