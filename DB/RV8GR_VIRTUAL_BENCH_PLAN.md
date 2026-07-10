# RV8GR Virtual Bench Plan

Purpose: generated report mapping the 18 RV8GR chip split records to the virtual test instruments declared in `DB/VIRTUAL_TEST_GENERATOR_CONTRACT.json`.

Machine-readable source: `DB/RV8GR_VIRTUAL_BENCH_PLAN.json`.

## Summary

- RV8GR chips: 18
- Split records per chip: 5
- Total chip/record mappings: 90
- OutputAssert mappings: 90
- DelayNoise propagation-stress mappings: 18
- Required instruments all declared: true

## Record Mapping

| Split record | Virtual instruments | Generated checks |
|---|---|---|
| `truth_table` | `InputSource`, `Probe`, `OutputAssert` | drive each input vector; sample every named output; assert expected logic value |
| `timing` | `ClockSource`, `Switch`, `Probe`, `OutputAssert` | apply required clock profile; sample after declared delay; assert setup/hold or no-edge behavior |
| `tri_state` | `InputSource`, `BusProbe`, `OutputAssert` | enable output; disable output; assert high-Z when disabled |
| `bus_fight` | `BusProbe`, `OutputAssert` | force safe single-driver vector; force conflict vector; assert conflict is reported |
| `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` | apply source transition; inject optional delay/noise; sample destination after timing budget; assert output still meets expectation |

## RV8GR Chip Coverage

| Part | Role | Split records mapped | Propagation stress |
|---|---|---|---|
| `74HC00` | NAND gates for control decode and glue logic. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `74HC04` | Inverters for active-low control and reset/clock glue. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `74HC21` | Dual 4-input AND gates for decode and control qualification. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `74HC32` | OR gates for control composition. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `74HC74` | Positive-edge D flip-flops for flags, IRQ latch, and synchronous state. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `74HC86` | XOR gates for ALU and compare/control paths. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `74HC157` | Quad muxes for address and data path selection. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `74HC161` | Positive-edge program counter and counter-style state. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `74HC164` | Serial-in parallel-out ring/control sequencing support. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `74HC245` | Bidirectional bus transceiver for shared bus isolation. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `74HC283` | 4-bit binary adders for the ALU. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `74HC541` | Octal buffers for unidirectional bus and LED/probe-visible outputs. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `74HC574` | Positive-edge octal registers for IR, AC, page, and data-path latches. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `74HC688` | 8-bit equality comparator for branch/page/control decisions. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `62256` | Generic 32K x 8 SRAM-compatible RAM footprint. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `AS6C62256` | Alliance 32K x 8 SRAM option for RAM. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `AT28C256` | 32K x 8 EEPROM option for program ROM. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |
| `SST39SF010A` | Flash ROM option for program storage. | `truth_table`, `timing`, `tri_state`, `bus_fight`, `propagation` | `ClockSource`, `Probe`, `RCParasitic`, `DelayNoise`, `OutputAssert` |

## Boundary

Generated virtual benches prove model behavior and stress selected assumptions. Physical hardware still needs real voltage, timing, and oscilloscope evidence.
