# RV8GR Batch 2 Verification Audit

Scope: practical Task 3 audit for the RV8GR Batch 2 package records. This is
not a completion claim for all migrated ICs.

## Representative Deepened Records

These chips now have chip-specific truth vectors plus datasheet-backed timing
and electrical records.

| Part | Truth vectors | Datasheet timing | Electrical data |
| --- | --- | --- | --- |
| 74HC00 | `nand_00`, `nand_01`, `nand_10`, `nand_11` | TI SN74HC00 section 6.7, A/B to Y, CL = 50 pF, 4.5 V: typ 9 ns, max 18 ns at 25 C, max 23 ns over -40 C to 85 C | TI SN74HC00 sections 6.3 and 6.5: VCC 2 V to 6 V, input thresholds, 20 uA max ICC at 6 V, 10 pF max input capacitance |
| 74HC04 | `invert_0`, `invert_1` | TI SN74HC04 section 6.7, A to Y, CL = 50 pF, 4.5 V: typ 9 ns, max 19 ns at 25 C, max 24 ns over -40 C to 85 C | TI SN74HC04 sections 6.3 and 6.5: VCC 2 V to 6 V, input thresholds, 20 uA max ICC at 6 V, 10 pF max input capacitance |
| 74HC32 | `or_00`, `or_01`, `or_10`, `or_11` | TI SN74HC32 section 6.8, A/B to Y, CL = 50 pF, 4.5 V: typ 10 ns, max 20 ns at 25 C, max 25 ns over -40 C to 85 C | TI SN74HC32 sections 6.3 and 6.6: VCC 2 V to 6 V, input thresholds, 20 uA max ICC at 6 V, 10 pF max input capacitance |

## Per-Chip Truth Tests Added

These requested chips now have executable per-chip truth records instead of
intent-only or `basic_function` placeholders.

| Part | Explicit behavior now covered |
| --- | --- |
| 74HC161 | async clear, parallel load, enabled count, hold when ENP is low, terminal-count RCO high, and RCO low when ENT is low |
| 74HC245 | DIR=1 A-to-B, DIR=0 B-to-A, reverse data patterns, `/OE=1` high-Z in both directions, and bus-fight records for external driver conflicts plus disabled no-conflict |
| 74HC574 | rising-edge latch, hold after D changes, second latch value, `/OE=1` high-Z, and re-enable restoring the last latched value |
| 62256 | write/read at two addresses, chip-disabled high-Z, output-disabled high-Z, and write-mode high-Z |
| AT28C256 | write/read at two addresses, chip-disabled high-Z, output-disabled high-Z, and write-mode high-Z |
| 74HC21 | four-input AND low/high cases on both gates |
| 74HC74 | async clear, async preset, rising clock D capture low/high, and second flip-flop capture |
| 74HC86 | full XOR truth table |
| 74HC164 | async clear and rising-edge serial shift sequence |
| 74HC283 | addition with no carry, carry-in, and carry-out |
| 74HC541 | enabled buffer output, both output-enable pins, and high-Z cases |
| 74HC688 | equal, not-equal, single-bit mismatch, and disabled output-high cases |
| AS6C62256 | write/read at two addresses, chip-disabled high-Z, output-disabled high-Z, and write-mode high-Z |
| SST39SF010A | write/read at two addresses, chip-disabled high-Z, output-disabled high-Z, and write-mode high-Z |

## Edge Criteria

Every IC truth-table record now declares `edge_criteria`.

- Clocked chips identify rising or falling trigger edge.
- Non-trigger-edge or no-rising-edge hold behavior must be explicit for
  clocked chips.
- Level-sensitive chips declare `trigger_edge: none`.
- Memory chips declare their write/read control window and high-Z cases.

## Existing Explicit Records

These Batch 2 records already had explicit functional vectors before this pass,
but were not re-audited for full datasheet timing/electrical extraction here:

- `74HC157`
- `74HC245`

## Known Remaining Placeholders

No RV8GR-used Batch 2 truth-table record still uses a `basic_function`
placeholder or intent-only vector.

Next practical target: extend the same edge-criteria execution depth from the
RV8GR-used chips to the rest of the migrated IC catalog.
