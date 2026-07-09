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
