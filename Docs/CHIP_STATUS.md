# Chip Status

Status snapshot for the shared Components library.

## Status Meanings

- `verified`: pinout documentation exists and cites manufacturer-backed DIP,
  PDIP, P-DIP, or equivalent through-hole package evidence.
- `modeled`: a behavior model exists in Verilog and the Python catalog can
  instantiate the part by name.
- `tested`: covered by the runnable Python catalog/behavior tests, Verilog smoke
  tests, or structural netlist-export compile tests.
- `missing-datasheet`: excluded from the active catalog because manufacturer HC
  DIP package evidence was not available.

## Verified

All active embedded pinout comments in `Verilog/74xx/*.v` and
`Verilog/Memory/*.v` are intended to be manufacturer-backed DIP/PDIP evidence.
Parts without that evidence must not stay in the active physical pinout
catalog.

Verified 74HC/HCT embedded pinout documentation currently covers:

`74HC00`, `74HC02`, `74HC03`, `74HC04`, `74HC05`, `74HC07`, `74HC08`, `74HC10`, `74HC11`,
`74HC14`, `74HC132`, `74HC138`, `74HC139`, `74HC147`, `74HC148`, `74HC151`,
`74HC153`, `74HC154`, `74HC155`, `74HC157`, `74HC158`, `74HC160`, `74HC161`, `74HC162`,
`74HC163`, `74HC164`, `74HC165`, `74HC166`, `74HC193`, `74HC20`, `74HC21`,
`74HC27`, `74HC238`, `74HC240`, `74HC244`, `74HC245`, `74HC251`, `74HC257`, `74HC266`,
`74HC273`, `74HC283`, `74HC30`, `74HC32`, `74HC352`, `74HC374`, `74HC377`,
`74HC4049`, `74HC4050`, `74HC4078`, `74HC4520`, `74HC4538`, `74HC541`, `74HC574`,
`74HC593`, `74HC595`, `74HC688`, `74HC74`, `74HC85`, `74HC86`, `74HC922`,
`74HCT04`, `74HCT14`, `74HCT245`, `74HCT541`, and `74HCT574`.

Verified memory embedded pinout documentation currently covers:

`62256`, `AS6C62256`, `AT28C256`, `CY7C199`, and `SST39SF010A`.

## Modeled

Modeled 74HC/HCT parts currently have DB-local Verilog/Python model metadata or legacy `Verilog/74xx/*.v` coverage:

`74HC00`, `74HC02`, `74HC03`, `74HC04`, `74HC05`, `74HC07`, `74HC08`, `74HC10`, `74HC11`,
`74HC14`, `74HC132`, `74HC138`, `74HC139`, `74HC147`, `74HC148`, `74HC151`,
`74HC153`, `74HC154`, `74HC155`, `74HC157`, `74HC158`, `74HC160`, `74HC161`, `74HC162`,
`74HC163`, `74HC164`, `74HC165`, `74HC166`, `74HC193`, `74HC20`, `74HC21`,
`74HC27`, `74HC238`, `74HC240`, `74HC244`, `74HC245`, `74HC251`, `74HC257`, `74HC266`,
`74HC273`, `74HC283`, `74HC30`, `74HC32`, `74HC352`, `74HC374`, `74HC377`,
`74HC4049`, `74HC4050`, `74HC4078`, `74HC4520`, `74HC4538`, `74HC541`, `74HC574`,
`74HC593`, `74HC595`, `74HC688`, `74HC74`, `74HC85`, `74HC86`, `74HC922`,
`74HCT04`, `74HCT14`, `74HCT245`, `74HCT541`, and `74HCT574`.

Modeled memory parts:

`62256`, `AS6C62256`, `AT28C256`, `CY7C199`, and `SST39SF010A`.

## Tested

Runnable test coverage is split by layer:

- Python behavior/catalog tests: `python3 -B -m tests.test_chips`
- Python design/netlist/CLI tests: `python3 -B -m tests.test_design`,
  `python3 -B -m tests.test_netlist`, and `python3 -B -m tests.test_cli`
- 74xx Verilog smoke: `iverilog ... Verilog/74xx/*.v ... && vvp ...`
- Memory Verilog smoke: `iverilog ... Verilog/Memory/*.v ... && vvp ...`

Structural netlist-export compile tests currently cover every mapped part below:

`74HC00`, `74HC02`, `74HC04`, `74HC07`, `74HC08`, `74HC10`, `74HC11`,
`74HC14`, `74HC20`, `74HC21`, `74HC27`, `74HC30`, `74HC32`,
`74HC74`, `74HC85`, `74HC86`, `74HC138`, `74HC139`,
`74HC147`, `74HC148`, `74HC151`, `74HC153`, `74HC154`, `74HC155`, `74HC157`,
`74HC158`, `74HC160`, `74HC161`, `74HC162`, `74HC163`, `74HC164`, `74HC165`, `74HC166`,
`74HC193`, `74HC238`, `74HC240`, `74HC244`, `74HC245`, `74HC251`,
`74HC257`, `74HC266`, `74HC273`, `74HC283`, `74HC352`, `74HC374`, `74HC377`,
`74HC4078`, `74HC541`, `74HC574`, `74HC593`, `74HC595`, `74HC688`,
`74HC922`, `62256`, `AS6C62256`, `AT28C256`, `CY7C199`, and `SST39SF010A`.

## Export Notes

`74HC147` structural export is enabled with an explicit `/I0` input port. The
repository TI pin table has only `/Y1`, `/Y2`, and `/Y3` bonded outputs, so the
lowest `Y_bar` vector bit is exported as an internal open placeholder instead
of being mapped to a physical package pin.

## Missing Datasheet

No active 74HC/HCT or memory DB package is currently listed here. Parts without
manufacturer-verified DIP evidence should remain absent from the active DB until
source evidence is added.
