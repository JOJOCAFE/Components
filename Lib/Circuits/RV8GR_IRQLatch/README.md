# RV8GR IRQLatch

This circuit is the RV8GR v1.0 polling interrupt latch.

U31 is a dual `74HC74`:

| Flip-flop | Clock | D | Output | Meaning |
|---|---|---|---|---|
| FF-A | `EI_decode` rising edge | 1 | `IE` | interrupt enable flag |
| FF-B | `/IRQ` release rising edge | 1 | `IRQ_FF` | pending interrupt flag |

Both clears are tied to `/RST`.

## v1.0 Boundary

This circuit does not force the PC, does not jump to `$FF00`, does not clear
itself when software sees the interrupt, and does not include IRQ acknowledge
logic. Software polls `IE` and `IRQ_FF`.

## Proof

The circuit proof checks:

- `/RST` clears IE and IRQ_FF.
- EI sets IE on a rising `EI_decode` edge.
- Holding `/IRQ` low does not latch; release back high latches IRQ_FF.
- IRQ_FF is sticky across 100 CPU ticks.
- DI is inert in v1.0.
- No PC force, vector, acknowledge, or auto-clear path is part of this package.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```
