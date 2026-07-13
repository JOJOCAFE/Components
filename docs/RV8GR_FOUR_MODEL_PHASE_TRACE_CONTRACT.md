# RV8GR Four-Model Phase Trace Contract (proposal)

## Status and scope

This is an additive **software differential-hardening** contract.  It defines
what a future RV8GR instruction-stream harness must observe and compare across
four executable models:

1. RV8GR `CPUSim`;
2. RV8GR `ComponentsCPUSim`;
3. behavioural RV8GR Verilog RTL; and
4. RV8GR chip-level/optimised Verilog RTL.

It does not change RV8GR logic, KiCad, Components circuit wiring, or any
existing directed proof.  It also does not claim physical 74HC timing,
deadband, or maximum clock frequency.  Those remain separate evidence tasks.

The contract supplements the existing package traces and the full-control
T2-only proof.  A forced-T2 opcode test is not a fetch/execution transaction:
it cannot satisfy this contract by itself.

## Intent and source ownership

The RV8GR repository is authoritative for the intended CPU ISA, reset state,
memory map, RTL behaviour, and lab programs.  Components is authoritative only
for its reusable package definitions and the observation adapter it supplies.

The comparison harness must therefore record, for every run:

- the RV8GR source revision and source paths used for CPUSim and both RTLs;
- the Components revision and circuit/adaptor paths used for ComponentsCPUSim;
- the ROM image digest, RAM seed/digest, deterministic random seed, and
  explicit initial AC, Z, PG, DP, IE, and IRQ state;
- the mapping-manifest version that maps each model's local signal to a field
  in this contract.

No adapter may reconstruct an architectural result from expected values or use
one model's state to fill a field in another.  A mapping is valid only when it
reads the named model's own state, port, trace event, or declared memory
callback.

## Transaction and sampling boundary

One instruction transaction begins immediately before the rising edge that
enters `T0` and ends after the rising edge that completes its `T2` execution
phase and after that model has reached its documented quiescent/delta-settled
state.  Reset is a separate transaction and must settle before instruction 0.

The canonical phase sequence is:

```text
reset-settled -> T0-settled -> T1-settled -> T2-settled -> next T0-settled
```

`T0`, `T1`, and `T2` are observations of the phase state **after** the active
edge and settling, not a request to force a control input.  At each normal
phase sample exactly one of them must be high.  A model that exposes only a
phase counter may map it to the three one-hot fields; the mapping manifest must
state the conversion.

All four models use a common seed/program and start state.  They are compared
at every available phase sample, then again at the instruction boundary.  A
final-state-only comparison is insufficient.

## Canonical record

Each model writes JSON Lines records.  The canonical object is intentionally
small enough for CPUSim, ComponentsCPUSim, behavioural RTL and chip-level RTL
to produce without requiring identical internal hierarchy.

```json
{
  "schema": "rv8gr.phase-trace@1",
  "run": {"seed": 17, "program_sha256": "...", "instruction": 4},
  "model": "chip_level_rtl",
  "sample": "T2-settled",
  "phase": {"T0": 0, "T1": 0, "T2": 1},
  "state": {"PC": "0x0084", "IR": "0x31", "AC": "0x00", "Z": 1,
            "PG": "0x00", "DP": "0x80", "IE": 0, "IRQ": 0,
            "HLT": 0},
  "memory": {"ABUS": "0x8000", "ROM_OE_N": 1, "ROM_WE_N": 1,
             "RAM_OE_N": 1, "RAM_WE_N": 1,
             "write": null},
  "bus": {"DBUS": "unavailable", "IBUS": "unavailable",
          "DBUS_owners": "unavailable", "IBUS_owners": "unavailable"},
  "availability": {"DBUS": "unavailable", "IBUS": "unavailable",
                   "DBUS_owners": "unavailable", "IBUS_owners": "unavailable"}
}
```

Values are integers or canonical uppercase hexadecimal strings with fixed
width (`0x00` for 8-bit, `0x0000` for 16-bit).  A field that is not observable
is written as JSON `null` and named in `availability` as `"unavailable"`;
the string in the example is explanatory only.  `write` is either `null` or
`{"address":"0x8000","value":"0xAA"}` and is emitted only for an
architecturally committed RAM write.

## Required fields and comparison rules

| Field group | Required at each settled phase | Comparison rule |
| --- | --- | --- |
| Phase | `T0`, `T1`, `T2` | Exact one-hot equality. |
| Architectural state | `PC`, `IR`, `AC`, `Z`, `PG`, `DP`, `IE`, `IRQ`, `HLT` | Exact equality when the field is available in all four models. |
| Address/control | `ABUS`, `ROM_OE_N`, `ROM_WE_N`, `RAM_OE_N`, `RAM_WE_N` | Exact equality at the matching phase when available in all four models. |
| Committed RAM write | `write` | Exact same no-write/write decision, address, and value at T2 and instruction boundary. |
| Bus observations | `DBUS`, `IBUS`, and owner sets | Exact equality only after a declared mapping is available for every compared model. |

The first mismatch must retain all four raw records, the program image, seed,
start state, mapping manifest, and source revisions.  The harness must report
the earliest differing instruction and phase, not merely the final failure.

## Mapping manifest

The harness must keep mappings separate from traces, for example:

```json
{
  "schema": "rv8gr.phase-trace-mapping@1",
  "model": "components_cpusim",
  "source_revision": "<git revision>",
  "fields": {
    "state.PC": {"source": "<declared public state path>", "kind": "direct"},
    "phase.T0": {"source": "<phase counter path>", "kind": "one_hot_decode"},
    "memory.write": {"source": "<write callback>", "kind": "commit_event"},
    "bus.DBUS": {"kind": "unavailable", "reason": "no stable public probe"}
  }
}
```

Only `direct`, `one_hot_decode`, and `commit_event` mappings are allowed in
version 1.  `one_hot_decode` must state its truth table.  A mapping that derives
state from opcode expectations, another model, or a post-hoc final state is
invalid.  The manifest is reviewed with any adapter change, so renamed RTL
nets cannot silently change trace meaning.

## Deliberately unavailable signals

The following may begin as unavailable; their absence must be visible and
must not be converted into a passing comparison:

| Signal | Why it may be unavailable | Promotion rule |
| --- | --- | --- |
| `DBUS` and `IBUS` values | High-level simulators may not expose resolved physical buses. | Compare only after every model exports a stable, documented probe. |
| Bus owner sets | CPUSim need not model physical output-enable ownership. | Do not infer owners from value; compare only using named enable/owner probes. |
| Sub-chip delayed transitions | Different simulators have different delta/delay engines. | Do not compare transient events; sample settled phase boundaries only. |
| Internal derived clocks | These are implementation details except documented source/sink contracts. | Compare their architectural consequence, or expose a named documented probe. |
| Electrical X/Z strength and analogue timing | Not uniformly represented and not physical signoff evidence. | Keep in dedicated chip/electrical tests and hardware scope work. |

An unavailable field is not a wildcard.  It is excluded from that field's
cross-model equality check and leaves a named coverage gap in the resulting
report.  A run may pass its **available-field** comparison while still being
ineligible for a bus-ownership or physical-timing promotion.

## Acceptance sequence

1. Add and review one mapping manifest per model using public/declared sources.
2. Establish the reset transaction and one known fetch/execute program trace.
3. Run deterministic seeded streams, retaining replay artifacts for every
   mismatch.
4. Add end-to-end reserved/non-ISA encodings and record observed effects;
   never rename them as NOPs without this evidence.
5. Extend bus fields only when all four models expose equivalent named probes.
6. Keep electrical deadband and PCB speed claims outside this contract.

## Relationship to existing evidence

- `examples/circuits/RV8GR_END_TO_END_TEST_PLAN.md` Stage 4A is the lane-level
  campaign that requires this contract.
- `docs/RV8GR_COMPOSITION_CONTRACT.md` remains the narrow, declared
  FullControl composition/derived-clock contract.
- Existing package traces (`RV8GR_FetchCycleTrace`,
  `RV8GR_StoreLoadBranchTrace`, `RV8GR_PageJumpTrace`, and
  `RV8GR_InterruptTrace`) remain directed component evidence.  They are
  useful seed programs and expected behaviours, not four-model trace adapters.
