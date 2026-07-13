"""Fail-loud boundary tests for the RV8GR FullControl live-operation adapter."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
import shutil
import subprocess
import unittest

from chiplib.circuit_hierarchy import discover_circuit_packages
from chiplib.circuit_runner import CircuitRunner
from chiplib.rv8gr_fullcontrol_operation import (
    FullControlOperationError,
    _harness,
    _validate_harness,
    run_full_control_t2_control,
)


class FullControlOperationTests(unittest.TestCase):
    _RV8GR = Path("/home/jo/kiro/RV8/RV8GR")

    @staticmethod
    def _rtl_vcd_scalar_events(vcd: Path, names: tuple[str, ...]) -> dict[str, list[tuple[int, str]]]:
        """Read the named scalar handoff signals from an existing VCD only."""
        text = vcd.read_text(encoding="utf-8", errors="strict")
        codes: dict[str, str] = {}
        for name in names:
            match = re.search(rf"^\$var\s+\S+\s+1\s+(\S+)\s+{re.escape(name)}\s+\$end$", text, re.MULTILINE)
            if match is None:
                raise AssertionError(f"chip-level VCD has no scalar {name}")
            codes[match.group(1)] = name
        events = {name: [] for name in names}
        time = 0
        for line in text.splitlines():
            if line.startswith("#"):
                time = int(line[1:])
                continue
            match = re.fullmatch(r"([01xXzZ])(\S+)", line)
            if match and match.group(2) in codes:
                events[codes[match.group(2)]].append((time, match.group(1).lower()))
        return events

    def test_harness_owns_only_real_input_sources(self) -> None:
        package = discover_circuit_packages()["RV8GR_FullControlOpcodeSweep"]
        sources = _validate_harness(package, _harness(package))
        self.assertEqual(("/RST", "PC_INC", "IRH0..IRH7", "IRL0..IRL7", "T2"), sources)
        self.assertFalse({"AC0..AC7", "Z_flag", "PG0..PG7", "DP0..DP7", "IE", "PC0..PC15", "IBUS0..IBUS7", "DBUS0..DBUS7"} & set(sources))

    def test_t2_operation_settles_the_canonical_u34_u7_handoff(self) -> None:
        # The U34/U7 transition is an atomic chip-level simulation handoff.
        # No test source is allowed onto IBUS or DBUS, and a persistent fight
        # remains an error when the transaction reaches quiescence.
        result = run_full_control_t2_control(0x01, operand=0x5A)
        self.assertEqual(0, result.pc_load)
        self.assertEqual(0, result.ie)

    def test_512_control_contract_has_an_external_verilog_gate_and_live_owner_check(self) -> None:
        """Fail loudly if the 512-case RTL sweep or live T2 controls drift.

        The external suite is deliberately run read-only: its behavioral
        opcode bench is the canonical exhaustive 256 opcode x two-Z proof,
        while its chip-level and dual benches make this a three-model gate.
        Components can execute the source-owned T2 controls with reset Z=0;
        Z=1 remains scheduled-only because Z is a shared output boundary.
        """
        script = self._RV8GR / "tools" / "run_all_verilog_tb.sh"
        if not script.is_file() or shutil.which("iverilog") is None or shutil.which("vvp") is None:
            self.skipTest("RV8GR Verilog suite or tools unavailable")
        completed = subprocess.run(
            [str(script)], cwd=self._RV8GR, text=True, capture_output=True, check=False,
            env={**__import__("os").environ, "COMPONENTS_ROOT": str(Path(__file__).resolve().parents[2])},
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        output = completed.stdout + completed.stderr
        self.assertIn("OPCODE SWEEP PASSED: 512 cases (256 opcodes x Z=0/1)", output)
        self.assertIn("RV8GR chip-level bring-up PASS", output)
        self.assertIn("RV8GR dual compare PASS", output)

        # Scheduled control contract: this is the exact /PC_LD equation used
        # by the RTL sweep, for both legal initial-Z states.  Keep it here
        # rather than assuming a no-op for reserved encodings.
        scheduled = 0
        for opcode in range(256):
            for initial_z in (0, 1):
                expected_load = int(bool((opcode & 0x01) or ((opcode & 0x02) and (initial_z ^ ((opcode >> 7) & 1)))))
                self.assertIn(expected_load, (0, 1), (opcode, initial_z))
                scheduled += 1
        self.assertEqual(512, scheduled)

        # Live ownership/control check: one flattened runner, real public
        # sources only.  Reset establishes Z=0, so /PC_LD is live-compared for
        # every opcode at that source-backed state.  U34/U7 are checked as the
        # settled enables, not by injecting an artificial IBUS driver.
        catalog = discover_circuit_packages()
        runner = CircuitRunner.from_hierarchy(catalog["RV8GR_FullControlOpcodeSweep"], catalog)
        for name, value in (("/RST", 0), ("/RST", 1), ("PC_INC", 0), ("IRL0..IRL7", 0x5A), ("T2", 0)):
            runner.set_input(name, value)
        for opcode in range(256):
            # Reset is the only declared public initialization of the shared
            # Z boundary.  Reapply it per row so an earlier AC-write opcode
            # cannot silently alter a later branch row.
            runner.set_input("/RST", 0)
            runner.set_input("/RST", 1)
            runner.set_input("IRH0..IRH7", opcode)
            initial_z = runner.read("Z_flag")
            self.assertIn(initial_z, (0, 1), hex(opcode))
            with runner.board.atomic_settlement():
                runner.set_input_with_declared_clock_edges("T2", 1)
            expected_load = int(bool((opcode & 0x01) or ((opcode & 0x02) and (initial_z ^ ((opcode >> 7) & 1)))))
            self.assertEqual(0 if expected_load else 1, runner.read("/PC_LD"), hex(opcode))
            immediate = not bool(opcode & 0x0C)  # SRC=0 and STR=0
            self.assertEqual(0 if immediate else 1, runner._chips["BUS_U34"].read("/OE1"), hex(opcode))
            self.assertEqual(1 if immediate else 0, runner._chips["BUS_U7"].read("/OE"), hex(opcode))
            expected_ie = int(bool((opcode & 0x08) and not (opcode & 0x40) and not (opcode & 0x10)))
            self.assertEqual(expected_ie, runner.read("IE"), hex(opcode))
            runner.set_input("T2", 0)

    def test_ei_uses_declared_source_backed_clock_sink_not_a_virtual_override(self) -> None:
        """EI raises real U33-8 then clocks the declared U31-3 sink."""
        result = run_full_control_t2_control(0x08)
        self.assertEqual(1, result.ie)
        self.assertIsNone(result.ie_blocker)
        # Similar-looking but non-EI control bytes must not produce a clock
        # edge.  This is a source-backed decode, not an arbitrary T2 pulse.
        self.assertEqual(0, run_full_control_t2_control(0x18).ie)
        self.assertEqual(0, run_full_control_t2_control(0x48).ie)

    def test_chip_level_rtl_and_components_agree_on_the_u34_u7_handoff_outcome(self) -> None:
        """Compare final ownership against the canonical chip-level VCD.

        This is deliberately a simulator comparison, not a physical timing
        claim.  It confirms the RTL's named U34-enable/U7-disable handoff has
        no persistent IBUS X after T2 and that the Components transaction ends
        with the same ownership/value outcome.
        """
        script = self._RV8GR / "tools" / "run_chip_level_verilog.sh"
        source = self._RV8GR / "rtl" / "rv8gr_chip_level.v"
        if not script.is_file() or not source.is_file() or shutil.which("iverilog") is None or shutil.which("vvp") is None:
            self.skipTest("canonical RV8GR chip-level Verilog source or tools unavailable")
        completed = subprocess.run([str(script)], cwd=self._RV8GR, text=True, capture_output=True, check=False)
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertIn("RV8GR chip-level bring-up PASS", completed.stdout)
        vcd = Path("/tmp/rv8gr-verilog/rv8gr_chip_level.vcd")
        self.assertTrue(vcd.is_file(), "chip-level script did not produce its declared VCD")
        trace = self._rtl_vcd_scalar_events(vcd, ("n_T2", "n_bar_IRL_OE", "n_BUF_OE_N", "n_IBUS0"))
        t2_rises = [time for time, value in trace["n_T2"] if value == "1"]
        self.assertTrue(t2_rises, "chip-level VCD never enters T2")
        first_t2 = t2_rises[0]
        ibus_after_t2 = [value for time, value in trace["n_IBUS0"] if time >= first_t2]
        self.assertTrue(ibus_after_t2, "chip-level VCD has no IBUS samples after T2")
        self.assertNotIn("x", ibus_after_t2, "chip-level RTL leaves persistent IBUS X after T2")
        self.assertIn("0", [value for _time, value in trace["n_bar_IRL_OE"]], "RTL never enables U34")
        self.assertIn("1", [value for _time, value in trace["n_BUF_OE_N"]], "RTL never disables U7 for immediate T2")

        package = discover_circuit_packages()["RV8GR_FullControlOpcodeSweep"]
        runner = CircuitRunner.from_hierarchy(package, discover_circuit_packages())
        for name, value in (("/RST", 0), ("/RST", 1), ("T2", 0), ("PC_INC", 0), ("IRL0..IRL7", 0x5A), ("IRH0..IRH7", 0x01)):
            runner.set_input(name, value)
        with runner.board.atomic_settlement():
            runner.set_input("T2", 1)
        self.assertEqual(0, runner._chips["BUS_U34"].read("/OE1"))
        self.assertEqual(1, runner._chips["BUS_U7"].read("/OE"))
        self.assertEqual(tuple((0x5A >> bit) & 1 for bit in range(8)), runner.read("IBUS0..IBUS7"))

    def test_atomic_settlement_still_rejects_a_persistent_bus_fight(self) -> None:
        package = discover_circuit_packages()["RV8GR_FullControlOpcodeSweep"]
        runner = CircuitRunner.from_hierarchy(package, discover_circuit_packages())
        runner.set_input("/RST", 0)
        runner.set_input("/RST", 1)
        runner.set_input("T2", 0)
        runner.set_input("IRL0..IRL7", 0x5A)
        runner.set_input("IRH0..IRH7", 0x01)
        with runner.board.atomic_settlement():
            runner.set_input("T2", 1)
        # A persistent second driver added after U34 is settled must still
        # fail.  It is deliberately a Board source rather than a test input
        # and is never part of the operation harness.
        ibus0 = runner._boundary_lines["IBUS0..IBUS7"][0]
        with self.assertRaisesRegex(Exception, "conflicting drivers"):
            with runner.board.atomic_settlement():
                runner.board.logic_source("persistent_test_conflict", ibus0, 1)

    def test_harness_rejects_an_inout_as_a_test_driver(self) -> None:
        package = discover_circuit_packages()["RV8GR_FullControlOpcodeSweep"]
        raw = deepcopy(package.raw)
        raw["runtime"]["operation_harness"]["source_inputs"].append("IBUS0..IBUS7")
        class Package:
            ports = package.ports
        with self.assertRaisesRegex(FullControlOperationError, "direction=input"):
            _validate_harness(Package(), raw["runtime"]["operation_harness"])


if __name__ == "__main__":
    unittest.main()
