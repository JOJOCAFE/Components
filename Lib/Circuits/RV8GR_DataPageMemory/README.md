# RV8GR DataPageMemory

This circuit proves the data-page memory path.

`SETDP` loads U32 with the high address byte used later by `LB` and `SB`.

`DP_Load = T2 AND XOR_MODE AND /ADDR_MODE AND /AC_WR`

When `/ADDR_MODE=0`, the address mux selects:

`ABUS = {DP, IRL}`

Then A15 chooses memory:

- `$0000-$7FFF`: ROM selected
- `$8000-$FFFF`: RAM selected

## Proof

The circuit proof checks:

- SETDP loads U32 only when the U33 decode is true.
- `$7FFF` selects ROM and `$8000` selects RAM.
- RAM write/readback works through `{DP,IRL}`.
- ROM can be read as data when `DP<$80`.
- ROM and RAM chip selects are never both active.

Run:

```sh
PYTHONPATH=python python3 -B -m tests.test_lib_circuits
```
