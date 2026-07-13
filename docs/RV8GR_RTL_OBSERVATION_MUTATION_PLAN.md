# RV8GR RTL Observation and Mutation Plan

Scope: the software differential-hardening lane.  This plan adds benches and
trace assertions; it does not change RV8GR wiring, generated netlist, or the
baseline directed tests.

## Existing safe observation surface

The structural DUT is intentionally a named-net netlist.  A bench may observe
these nets hierarchically without changing RTL:

| Concern | Structural observation | Behavioural equivalent |
| --- | --- | --- |
| Phase | `n_T0`, `n_T1`, `n_T2` | `state` (`0`, `1`, `2`) |
| Architectural state | PC nets, `n_AC*`, `n_Z_flag`, `n_PG*`, `n_DP*`, `n_IE`, `n_IRQ_FF` | `pc`, `ac`, `z_flag`, `page_reg`, `data_page_reg`, `ie`, `irq_ff` |
| Address/data buses | `n_ABUS*`, `n_DBUS*`, `n_IBUS*` | `pc`, `data_addr_full`, `mem_read`, `ibus` |
| Memory control | `n_ABUS15`, `n_WR_DIR`, `n_bar_AC_BUF`, `n_BUF_OE_N` | derive from `state`, decode, and address; add trace-only wires if needed |
| Immediate handoff | `n_bar_IRL_OE`, `n_BUF_OE_N`, `n_WR_DIR`, `U34`, `U7` | derive from T2/decode; no direct tri-state instance exists |
| Reset and clock | `n_bar_RST`, `n_CLK` | `rst_n`, `clk` |

Use post-edge settlement (`#150` is the existing dual-compare convention)
for architectural checkpoints.  For an ownership transition, sample both the
transition instant and settled state; transient values are diagnostic evidence,
while an X/conflict that remains after the model settles is a failure.

## Mutation seams

Each negative test should be a dedicated testbench or an explicit test-only
wrapper.  Never `force` a production netlist in a normal pass bench.

1. **U34-to-U7 handoff** — at T2 immediate, force `n_bar_IRL_OE=0`,
   `n_BUF_OE_N=0`, and `n_WR_DIR=0` only in the mutation wrapper.  The IBUS
   must resolve to X/conflict.  The normal transition is U34 enabled / U7
   disabled; T2 memory load is U34 disabled / U7 DBUS-to-IBUS.
2. **ROM write protection** — use a testbench-only force on the ROM instance
   `/WE` during a ROM-selected write window.  The mutation must demonstrate a
   write attempt; the normal test asserts ROM `/WE` remains high.
3. **Store direction** — invert the U7 `DIR` test-only connection while
   asserting store (`n_STR`) in RAM space.  A correct test observes no valid
   RAM write or a resolved DBUS conflict, rather than merely a changed final
   register.
4. **OE ordering** — hold `n_BUF_OE_N=0` over an immediate T2 handoff or
   invert the U24-derived value in the wrapper.  Assert that U34 and U7 cannot
   both own IBUS after settlement.
5. **Reset release** — release `n_bar_RST` while holding clock low, then give
   one clean rising edge.  Mutate by releasing reset close to/after that edge;
   the test must reject a non-deterministic first phase or uninitialized
   state.  This is functional RTL evidence, not analogue recovery/removal
   signoff.

### Implemented checkpoint: reset release

The reset-release mutation is now implemented in the RV8GR source tree as
`tb/tb_rv8gr_reset_release_mutation.v` with
`tools/run_reset_release_mutation.sh`.  Its baseline releases reset while
clock is low and proves a one-hot phase and `PC=$0000` at the first edge.  Its
test-only bad-release case exits nonzero before it can be mistaken for a
passing zero-delay model.  Generated logs and VVP output stay under `/tmp`.

This closes only mutation item 5.  U34-to-U7 handoff, ROM `/WE`, store
direction, and output-enable ordering remain separate required kill tests.

### Implemented checkpoint: U34-to-U7 ownership

The U34/U7 ownership mutation is now implemented in RV8GR as
`tb/tb_rv8gr_u34_u7_handoff_mutation.v` with
`tools/run_u34_u7_handoff_mutation.sh`.  It isolates normal U34 ownership by
disabling the other legal IBUS driver (U14) and proving U7 high-Z.  Its
test-only fault enables U7 in the opposite DBUS-to-IBUS direction while U34
drives the opposite bit; the resolved IBUS value must become `X` and the
mutation run must exit nonzero.  It is a genuine primitive-resolution kill
test, but still not a measured physical deadband.

This closes mutation item 1.

### Implemented checkpoint: memory protection and U7 ordering

`tb/tb_rv8gr_memory_bus_mutation.v` with
`tools/run_memory_bus_mutation.sh` now covers mutation items 2–4 without
altering production RTL.  The baseline proves the ROM instance has `/WE`
tied high, an intended U7 store moves the selected IBUS byte to RAM DBUS, and
U7 is disabled while U34 owns IBUS.  Its three separate forced faults are
required to exit nonzero: a low-to-high ROM `/WE` pulse rewrites the EEPROM
model, reversed U7 direction stores a byte other than the selected IBUS byte,
and enabling U7 before U34 releases an opposite source resolves IBUS to `X`.

This closes mutation items 2, 3, and 4 at the digital-model level.  Together
with reset release and U34/U7 ownership, all planned software mutation kills
are implemented.  The physical boundary below remains open.

## Bench implementation order

1. Extract a reusable phase-record task from
   `tb/tb_rv8gr_dual_compare.v`: record PC, phase, buses, controls, selected
   memory, and write data each settled clock.
2. Add a chip-only mutation bench built from the same compile set as
   `tools/run_chip_level_full_verilog.sh`; its wrappers are local to the test
   bench source.
3. Extend the dual bench only after trace records have stable field names.
   Compare checkpoints at corresponding T0 boundaries, and compare each
   phase's structural trace against a behavioural trace adapter.

## Commands

Baseline structural gates:

```sh
COMPONENTS_ROOT=/home/jo/kiro/Components \
  /home/jo/kiro/RV8/RV8GR/tools/run_chip_level_verilog.sh
COMPONENTS_ROOT=/home/jo/kiro/Components \
  /home/jo/kiro/RV8/RV8GR/tools/run_chip_level_full_verilog.sh
COMPONENTS_ROOT=/home/jo/kiro/Components \
  /home/jo/kiro/RV8/RV8GR/tools/run_dual_verilog_compare.sh
```

The wrapper should retain their `RV8GR_BUILD_DIR` convention and write VVP,
VCD, ROM image, and failure trace only under `/tmp`.

## Source locations

- Behavioural model: `/home/jo/kiro/RV8/RV8GR/rtl/rv8gr_cpu.v`
- Structural netlist: `/home/jo/kiro/RV8/RV8GR/rtl/rv8gr_chip_level.v`
- Existing chip benches: `/home/jo/kiro/RV8/RV8GR/tb/tb_rv8gr_chip_level.v`,
  `tb_rv8gr_chip_full.v`, and `tb_rv8gr_dual_compare.v`
- Component primitive semantics: `verilog/74xx/74hc245.v`,
  `verilog/74xx/74hc541.v`, `verilog/memory/at28c256.v`, and
  `verilog/memory/62256.v`

## Boundary

The tests prove RTL-level ordering and resolution using the selected model
delays.  They do not prove a real 74HC deadband, EEPROM/SRAM turn-around,
or a PCB clock-frequency limit; those remain scope/measurement work.
