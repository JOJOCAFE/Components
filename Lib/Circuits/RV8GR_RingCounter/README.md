# RV8GR Ring Counter

This circuit is the RV8GR three-phase timing generator. It uses one `74HC164`
shift register and two gates from one `74HC04` inverter package.

The electrical reset on `74HC164` clears all outputs to `0`. On the first rising
clock after reset, feedback `NOT(T0) AND NOT(T1)` shifts a `1` into `Q0`, which
starts the usable `T0 -> T1 -> T2` loop.

The RV8GR labs and build plan are used as extraction guides. Where they say
`Reset: T0=1`, read that as the first usable phase after the clear/start clock.
The circuit proof keeps the raw `/CLR` state separate because timing and edge
proofs need that distinction.

## Outputs

| Signal | Source | Meaning |
|---|---|---|
| `T0` | U8 `Q0` | Fetch control byte |
| `T1` | U8 `Q1` | Fetch operand byte |
| `T2` | U8 `Q2` | Execute phase |

`Q3..Q7` are not part of the phase contract. They may contain shifted history
bits and must not be used as "ring is healthy" indicators. The proven contract
is only that the lower three phase outputs repeat one-hot as `T0 -> T1 -> T2`.

## Proof

The circuit proof checks:

- `/CLR=0` forces `T0=T1=T2=0`.
- The first clock after reset enters `T0`.
- Later clocks repeat `T0 -> T1 -> T2`.
- No normal phase has more than one phase output high.
- Lower three-bit illegal states recover to the normal loop within three clocks.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```
