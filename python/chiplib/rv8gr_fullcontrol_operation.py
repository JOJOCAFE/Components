"""Source-owned live operations for the RV8GR FullControl package.

This is intentionally a narrow operation adapter, not a CPU interpreter.  It
can exercise controls whose sources are real public inputs of the flattened
package.  In particular it must never turn an observed/shared bus or register
output into a convenient test driver.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .circuit_hierarchy import discover_circuit_packages
from .circuit_runner import CircuitRunner
from .core import BusConflictError


class FullControlOperationError(ValueError):
    """The declared FullControl operation boundary is unsafe or incomplete."""


# Kept as an import-compatible name for callers that recorded the former
# blocker.  New executions must never return it: the package now declares the
# source-backed U33-8 -> U31-3 clock contract explicitly.
IE_DERIVED_CLOCK_BLOCKER = (
    "retired: U33.EI_decode -> U31.1CLK is delivered only through the declared "
    "source-backed clock-sink contract"
)


@dataclass(frozen=True)
class FullControlControlResult:
    """Observed result of one source-owned T2 control phase."""

    opcode: int
    pc_load: int | str
    ie: int | str
    live_scope: str = "control_and_ie_only"
    ie_blocker: str | None = None


def _harness(package: Any) -> Mapping[str, Any]:
    runtime = package.raw.get("runtime")
    if not isinstance(runtime, Mapping):
        raise FullControlOperationError("FullControl has no runtime operation harness")
    harness = runtime.get("operation_harness")
    if not isinstance(harness, Mapping) or harness.get("kind") != "source_owned_t2":
        raise FullControlOperationError("FullControl has no source_owned_t2 operation harness")
    return harness


def _validate_harness(package: Any, harness: Mapping[str, Any]) -> tuple[str, ...]:
    allowed = harness.get("source_inputs")
    if not isinstance(allowed, list) or not allowed or any(not isinstance(name, str) for name in allowed):
        raise FullControlOperationError("operation_harness.source_inputs must be a non-empty string list")
    if len(set(allowed)) != len(allowed):
        raise FullControlOperationError("operation_harness.source_inputs must not repeat an input")
    directions = {port.name: port.direction for port in package.ports}
    unknown = [name for name in allowed if name not in directions]
    if unknown:
        raise FullControlOperationError(f"operation harness names unknown input {unknown[0]!r}")
    unsafe = [name for name in allowed if directions[name] != "input"]
    if unsafe:
        raise FullControlOperationError(
            f"operation harness may drive only direction=input ports, not {unsafe[0]!r} ({directions[unsafe[0]]})"
        )
    required = {"/RST", "IRH0..IRH7", "IRL0..IRL7", "T2"}
    if not required <= set(allowed):
        raise FullControlOperationError(
            "operation harness must own /RST, IRH0..IRH7, IRL0..IRL7, and T2"
        )
    return tuple(allowed)


def run_full_control_t2_control(opcode: int, *, operand: int = 0) -> FullControlControlResult:
    """Run one real-control T2 phase without driving shared CPU state/buses.

    The result deliberately exposes only `/PC_LD` and IE.  AC, Z, PG, DP, PC,
    IBUS, and DBUS are not initialized or injected here: those are output or
    bidirectional physical boundaries and require their own source-backed
    state/driver contracts before a whole-opcode live promotion is valid.
    """

    if not isinstance(opcode, int) or isinstance(opcode, bool) or not 0 <= opcode <= 0xFF:
        raise FullControlOperationError("opcode must be an 8-bit integer")
    if not isinstance(operand, int) or isinstance(operand, bool) or not 0 <= operand <= 0xFF:
        raise FullControlOperationError("operand must be an 8-bit integer")

    catalog = discover_circuit_packages()
    package = catalog["RV8GR_FullControlOpcodeSweep"]
    allowed = _validate_harness(package, _harness(package))
    runner = CircuitRunner.from_hierarchy(package, catalog)

    # Reset is a real public input wired to the concrete PC16 and IEFF sinks.
    runner.set_input("/RST", 0)
    runner.set_input("/RST", 1)
    runner.set_input("T2", 0)
    if "PC_INC" in allowed:
        runner.set_input("PC_INC", 0)
    runner.set_input("IRL0..IRL7", operand)
    runner.set_input("IRH0..IRH7", opcode)
    try:
        # The chip-level RTL treats U7 release and U34 enable as one delayed
        # handoff.  Components must inspect the settled result, not raise on
        # an intermediate event ordering; a persistent fight still raises when
        # this transaction drains.
        with runner.board.atomic_settlement():
            runner.set_input_with_declared_clock_edges("T2", 1)
    except BusConflictError as exc:
        # This is a proof result, not an exception to bypass.  It says the
        # operation used real drivers and therefore cannot be promoted until
        # the concrete ownership error is repaired.
        raise FullControlOperationError(
            f"live_t2_blocked_bus_conflict: opcode 0x{opcode:02X}: {exc}"
        ) from exc
    ie_decode_expected = bool((opcode & 0x08) and not (opcode & 0x40) and not (opcode & 0x10))
    ie_value: int | str = runner.read("IE")
    ie_blocker = None
    if ie_value != int(ie_decode_expected):
        raise FullControlOperationError(
            f"live_ie_mismatch: opcode 0x{opcode:02X}: observed {ie_value!r}, "
            f"expected {int(ie_decode_expected)} through declared U33->U31 edge"
        )
    result = FullControlControlResult(opcode, runner.read("/PC_LD"), ie_value, ie_blocker=ie_blocker)
    runner.set_input("T2", 0)
    return result
