# RV8GR narrow composition contract

This contract makes selected FullControl child boundaries executable without
adding a general circuit expression language.

| Need | Explicit contract | Source |
| --- | --- | --- |
| Data address | `A0..A14={IRL0..IRL7,DP0..DP6}` in destination bit order; this is the physical form of logical `{DP,IRL}`. | RV8GR wiring guide Address Mux and chip-level RTL U15/U16/U29/U30 |
| Memory select | `A15=DP0..DP7[7]`. | chip-level RTL U30 A input and address-mux guide |
| Address mode | BUS exports concrete U26-6 `/ADDR_MODE` to PGDP. | wiring guide U26 gate B |
| PC load | BranchJump `/PC_LD` feeds the existing PC16 U1-U4 child. | wiring guide U26 gate D and PC wiring |
| IE state | `T2,SRC,/XOR_MODE,/AC_WR` feed U33-8, which clocks U31-3 through one declared rising-edge source/sink contract. | wiring guide EI Decode section |

The only new hierarchy syntax is ordered boundary concatenation, for example
`{IRL0..IRL7,DP0..DP6}`. It accepts declared boundaries only; it has no
operators, constants, inversions, or implicit conversion. A single-bit select
uses the existing `DP0..DP7[7]` syntax.

## Declared derived-clock contract

The flattened runner does not infer clocks from ordinary output transitions.
The owning FullControl package declares exactly one functional derived edge:

```text
trigger input T2
  U33-8 EI_decode (source output)
    -> U31-3 1CLK (declared clock sink)
```

At execution, the runner validates that the named source is an output, that
the named sink is a `CLK` input explicitly marked `kind=clock`, and that both
are joined to the same concrete flattened net.  It invokes U31's edge method
only on a real `0 -> 1` transition of that source.  This is a topology contract
for the documented EI path; it is not a general output-to-clock inference rule.

## Evidence boundary

The contract proves explicit structural composition plus the live `/PC_LD`
strobe and IE state edge. It is not a FullControl whole-system promotion and does
not establish PCB timing, bus deadband, fetch sequencing, RAM contents, or a
physical maximum clock frequency.

The flattened executor also preserves child VCC/GND rails.  This is required:
an unpowered child can make a false control proof appear to pass.

Before a 512-case live promotion, add a vector runner that owns DBUS/IBUS
drivers phase-by-phase (never a fixed source during an active real driver),
then prove PC load edge/state observations and the complete opcode expectations
through the flattened hierarchy.  The U34/U7 handoff is evaluated as one
atomic chip-level simulation transaction: intermediate delayed events may
settle, but a conflict still fails if it remains at quiescence.  This matches
the canonical RTL handoff trace; it does not establish real 74HC output
disable/enable deadband, PCB timing, or a physical maximum clock frequency.
