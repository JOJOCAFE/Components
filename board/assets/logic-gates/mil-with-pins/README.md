# MIL gate symbols with pins

These SVG files are imported presentation assets from
[`cludewn/logic-gate-symbols`](https://github.com/cludewn/logic-gate-symbols),
`main/mil/svg/with-pins`, retrieved on 2026-07-15. The upstream repository
declares the set **CC0-1.0**.

Included symbols: AND, buffer, NAND, NOR, NOT, input-negative NOT, OR, XOR,
and XNOR. They are useful as generic primitive-gate artwork for a future gate
editor.

They are not a Components Device definition, pin map, netlist, or behavioral
model. A Board or gate editor must create connectable ports from its resolved
Component/Device contract, then place this artwork behind those ports. Never
infer a port position, port direction, logic function, timing, or electrical
fact from an SVG path.

This import is pinned to upstream commit
`72a6e9caa3d50ba1d6de8ec08051c36b87410c2d`. When refreshing the set,
record the new immutable source revision and re-check the license before
replacement.
