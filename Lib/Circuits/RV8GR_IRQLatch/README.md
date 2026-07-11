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

## Build and test guide

- **Build/probe:** Use Lab 14 for U31 and U33. Probe `/RST`, `EI_decode`, `/IRQ`, `IE`, and `IRQ_FF`; do not add a PC-force or acknowledge wire.
- **Isolated manual-clock test:** Reset and release without a CPU clock. Pulse `EI_decode` LOW-to-HIGH once. Then pull `/IRQ` LOW, hold it, and release it HIGH.
- **Integration test:** Execute EI and DI through T2, apply and release `/IRQ`, then continue 100 CPU ticks while watching both flags and PC.
- **Pass:** Reset gives `IE=0, IRQ_FF=0`; EI sets IE; DI is inert; only the `/IRQ` release edge sets `IRQ_FF`; it stays set until reset; PC is unchanged by IRQ hardware.
- **Stop:** Stop on a flag change at the wrong edge, loss of the sticky flag, unknown output, or any automatic PC jump.
- **Temporary wiring:** Replace the Lab 12 temporary U33 tie-high wiring with the Lab 14 `EI_decode` connections before integration.
- **Boundary:** This proves the v1.0 polling latch behavior. It does not prove IRQ switch quality, physical edge timing, or a vectored interrupt system.
