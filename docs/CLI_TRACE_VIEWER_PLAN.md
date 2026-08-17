# CLI Trace Viewer — Task Plan

**Goal:** Text-screen visualization of RV8GR circuits, step-by-step from
2 chips to 35 chips, readable by both students and AI.

**Source of truth:** `.component` files (same as Board, same as runtime)

---

## Design

```
$ python3 -m chiplib.cli trace examples/circuits/RV8GR_RingCounter/circuit.component --steps 6

RV8GR_RingCounter (2 chips: U8 74HC164, U24 74HC04)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 CLK | T0 | T1 | T2 | note
─────┼────┼────┼────┼──────────────────────
 ↑ 1 |  1 |  0 |  0 | phase T0 (fetch ctrl)
 ↑ 2 |  0 |  1 |  0 | phase T1 (fetch operand)
 ↑ 3 |  0 |  0 |  1 | phase T2 (execute)
 ↑ 4 |  1 |  0 |  0 | cycle 2 starts
 ↑ 5 |  0 |  1 |  0 |
 ↑ 6 |  0 |  0 |  1 |
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

For the full CPU executing a program:

```
$ python3 -m chiplib.cli trace examples/circuits/RV8GR_FetchCycleTrace/circuit.component --steps 6

RV8GR_FetchCycleTrace (11 chips)
ROM: [0000]=30 42 10 01 30 00 01 06
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 CLK | PC   | IRH  | IRL  | T0 T1 T2 | IBUS | note
─────┼──────┼──────┼──────┼──────────┼──────┼─────────────────
 ↑ 1 | 0001 |   30 |   -- |  1  0  0 |   30 | T0: fetch $30 (LI)
 ↑ 2 | 0002 |   30 |   42 |  0  1  0 |   42 | T1: fetch $42
 ↑ 3 | 0002 |   30 |   42 |  0  0  1 |   42 | T2: AC ← $42
 ↑ 4 | 0003 |   10 |   -- |  1  0  0 |   10 | T0: fetch $10 (ADDI)
 ↑ 5 | 0004 |   10 |   01 |  0  1  0 |   01 | T1: fetch $01
 ↑ 6 | 0004 |   10 |   01 |  0  0  1 |   01 | T2: AC ← AC+$01
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Principles

1. **One command** — `python3 -m chiplib.cli trace <file> [options]`
2. **Source = .component** — no new format, no new parser
3. **Engine = existing runtime** — flatten, preload, clock, probe
4. **Output = structured text** — columns, parseable by AI or grep
5. **Progressive** — Lab 01 shows 1 column (CLK), Lab 13 shows 10+
6. **AI-friendly** — plain ASCII, consistent column format, JSON option
7. **Student-friendly** — hex values, LED-style 0/1, Thai notes optional

---

## Options

| Flag | Purpose |
|------|---------|
| `--steps N` | Number of clock pulses (default: 12) |
| `--probes P1,P2,...` | Which probes to show (default: all) |
| `--format table` | ASCII table (default) |
| `--format json` | JSON array of snapshots (for AI piping) |
| `--format csv` | CSV (for spreadsheet) |
| `--program "LI $42; ADDI $01"` | Assemble inline and preload ROM |
| `--rom file.bin` | Load binary ROM image |
| `--watch net1,net2` | Show raw net values (debug) |
| `--annotate` | Add instruction decode notes |

---

## Tasks

### Phase 1: Core trace command (Bam)

1. **Add `trace` subcommand to `chiplib/cli.py`**
   - Parse args: file path, --steps, --probes, --format
   - Load .component, resolve, create session
   - Clock N times, collect probe snapshots after each

2. **Trace formatter: table**
   - Auto-detect column widths from probe names
   - Format bus values as hex (8-bit → 2 chars, 16-bit → 4 chars)
   - Format single-bit as 0/1
   - Header + separator + rows

3. **Trace formatter: JSON**
   - Array of `{ step, time_ns, probes: { name: value } }`
   - Suitable for AI consumption / piping

4. **Test: trace RingCounter**
   - Verify output matches expected T0/T1/T2 sequence
   - Add as test case in test_cli.py

### Phase 2: ROM program support (Bam)

5. **--rom flag: load .bin into ROM chip**
   - Find AT28C256/ROM device in circuit, load binary
   - Works for FetchCycleTrace, BootSequenceTrace

6. **--program flag: inline assembly**
   - Call rv8gr_asm.py to assemble string → bytes
   - Preload into ROM
   - `--program "LI $42; ADDI $01; SUBI $43; BEQ $00"`

7. **--annotate: instruction decode**
   - After each T0 fetch, decode IRH into mnemonic
   - Add to "note" column

### Phase 3: Lab progression (Noon + Bam)

8. **Lab trace scripts**
   - One script per lab: `trace_lab02.sh` through `trace_lab13.sh`
   - Each shows the relevant probes for that lab's lesson
   - Example: `trace_lab07.sh` shows IBUS, SUM, AC (ALU path)

9. **Student guide update**
   - Add "simulation check" section to each lab
   - "Before building, run: `python3 -m chiplib.cli trace ...`"
   - Compare trace output with LED observations

### Phase 4: AI integration (Bam)

10. **JSON trace as MCP tool response**
    - `trace_circuit` tool: takes .component source + steps, returns JSON trace
    - AI can ask "show me what happens when I clock this 6 times"

11. **Diff mode**
    - `--diff expected.json` — compare trace against golden reference
    - Useful for: "student's circuit differs at step 4"

---

## File locations

```
python/chiplib/cli.py          → add 'trace' subcommand
python/chiplib/trace.py        → trace engine (collect snapshots)
python/chiplib/trace_format.py → table/json/csv formatters
python/tests/test_trace.py     → trace output tests
docs/CLI_TRACE_VIEWER_PLAN.md  → this file
```

---

## Dependencies

- All existing: parse → resolve → flatten → runtime → probe
- Optional: rv8gr_asm.py for --program flag
- No new pip packages
- No browser, no DOM, no HTTP

---

## Success criteria

- `python3 -m chiplib.cli trace .../RV8GR_RingCounter/circuit.component --steps 6`
  produces correct T0/T1/T2 table
- `python3 -m chiplib.cli trace .../RV8GR_FetchCycleTrace/circuit.component --steps 6`
  shows ROM data flowing through the fetch path
- JSON output parseable by AI in one round-trip
- Lab 02 → Lab 13 progression works with increasing probe columns
- Student can verify breadboard matches trace before powering on
