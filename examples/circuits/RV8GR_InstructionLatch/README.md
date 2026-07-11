# RV8GR InstructionLatch

This circuit stores the two bytes of an RV8GR instruction.

| Chip | Clock | Captures | Meaning |
|---|---|---|---|
| U5 `74HC574` | T0 rising edge | `IR_HIGH` | direct control byte |
| U6 `74HC574` | T1 rising edge | `IRL` | operand byte |

U5 maps the control byte directly to control signals:

`SUB XOR_MODE MUX_SEL AC_WR SRC STR BR JMP`

There is no opcode decoder in this path. The instruction bit is the control
wire.

## Proof

The circuit proof checks:

- U5 captures only on T0.
- U6 captures only on T1.
- Both latches hold through T2.
- The direct-control bit labels match the RV8GR wiring guide.
- The same vectors execute through live `74HC574` component models.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```

## Build and test guide

- **Build/probe:** Build U5 and U6 from Lab 06. Probe IBUS, T0, T1, all `IR_HIGH` control outputs, and `IRL`; use the lab pinout table for physical pins.
- **Isolated manual-clock test:** Put one known byte on IBUS, pulse T0, and confirm only U5 captures. Put a different byte on IBUS, pulse T1, and confirm only U6 captures. Pulse T2 and confirm both hold.
- **Integration test:** Fetch `30 42` from ROM and verify U5 captures `$30` at T0 and U6 captures `$42` at T1 while bus ownership remains single-driver.
- **Pass:** IRH bit labels map directly to `SUB XOR_MODE MUX_SEL AC_WR SRC STR BR JMP`; IRL holds the operand; neither register changes in the wrong phase.
- **Stop:** Stop on a wrong-phase capture, unknown output, phase overlap, or more than one IBUS driver.
- **Temporary wiring:** Remove manual latch clocks and direct IBUS switches before connecting T0/T1 and U7/U34/U14. Restore any swapped clocks used by the optional challenge.
- **Boundary:** Simulation proves edge semantics. Physical proof still needs clean phase edges and setup/hold at both `74HC574` inputs.
