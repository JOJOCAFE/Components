# RV8GR Interrupt Trace

This package checks the RV8GR v1.0 polling interrupt behavior:

- `EI` sets `IE`.
- `DI` does not clear `IE` in this hardware version.
- Pulling `/IRQ` LOW does not set `IRQ_FF`.
- Releasing `/IRQ` back HIGH sets `IRQ_FF`.
- `IRQ_FF` stays set until reset.
- The PC does not jump by itself.

`/IRQ` is active-low, so LOW means the interrupt line is being held active.
The `74HC74` latch uses the release edge, so the visible state changes when
the line returns HIGH.

## Student Checks

1. Reset first and confirm `IE=0`, `IRQ_FF=0`.
2. Run `EI` and confirm `IE=1`.
3. Run `DI` and confirm both flags hold their old values.
4. Hold `/IRQ` LOW and confirm `IRQ_FF` is still 0.
5. Release `/IRQ` HIGH and confirm `IRQ_FF=1`.
6. Check that `PC` did not change in any row.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```
