# Board vector pinout artwork

The SVGs in this directory are clean-room redraws of the functional-pinout
samples in `resource/temp/`. `functional-pinout-graphs.json` is their
machine-readable connectivity companion: every gate has named A/B/Y nodes
mapped to physical package pins. Together they are scalable Board presentation
assets, not the source of pin, logic, timing, or electrical truth.

- Pin names and numbers were checked against the local TI source PDFs in
  `source/` and the matching package `symbol/dip.json` records.
- `74HC03` is visibly marked as open-drain: its outputs require an external
  pull-up in real hardware. The drawing does not simulate that requirement.
- A Board client may scale an SVG freely, but must obtain connectable ports and
  all behavior from the resolved Component/device definition, never this art.
- A Board renderer must draw its mesh from the graph's gate-port-to-pin mapping,
  then use the package definition to label and validate the physical nodes. It
  must never infer connectivity from an SVG line's coordinates.

The temporary PNGs remain as review references only; they are not served by the
Board and are not copied into the vector files.

## Generic gate primitives

`logic-gates/mil-with-pins/` contains a separate CC0-licensed set of generic
MIL gate artwork with visible input/output leads. It is for a future primitive
gate editor, not a substitute for definition-backed IC functional-pinout art.
Its local README records the upstream source and the same presentation-only
boundary applies.

`logic-gates/mil-no-pins/` contains the matching no-pin variants, including a
standalone inversion bubble. Use them only where the editor renders its own
definition-backed terminals and labels.

The matching `mil-with-pins-png/` and `mil-no-pins-png/` folders provide 19
CC0 raster fallbacks/thumbnails. Board/editor rendering remains SVG-first;
the PNGs do not alter the presentation-only boundary.
