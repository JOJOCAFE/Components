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

All active files in `74HC/*-pin.md` and `Memory/*-pin.md` are intended to be
manufacturer-backed DIP/PDIP evidence files. Parts without that evidence must
not stay in the active physical pinout catalog.

Verified 74HC pinout files currently cover:

`74HC00`, `74HC02`, `74HC04`, `74HC07`, `74HC08`, `74HC10`, `74HC11`,
`74HC14`, `74HC20`, `74HC21`, `74HC27`, `74HC30`, `74HC32`, `74HC42`,
`74HC73`, `74HC74`, `74HC85`, `74HC86`, `74HC112`, `74HC138`, `74HC139`,
`74HC147`, `74HC148`, `74HC151`, `74HC153`, `74HC154`, `74HC155`, `74HC157`,
`74HC158`, `74HC160`, `74HC161`, `74HC162`, `74HC163`, `74HC164`, `74HC165`,
`74HC166`, `74HC181`, `74HC193`, `74HC238`, `74HC240`, `74HC244`, `74HC245`,
`74HC251`, `74HC257`, `74HC266`, `74HC273`, `74HC283`, `74HC352`, `74HC374`,
`74HC377`, `74HC4078`, `74HC541`, `74HC574`, `74HC593`, `74HC595`,
`74HC688`, and `74HC922`.

Verified memory pinout files currently cover:

`62256`, `AS6C62256`, `AT28C256`, `CY7C199`, and `SST39SF010A`.

## Modeled

Modeled 74HC parts currently have `74HC/*.v` Verilog models and Python catalog
coverage:

`74HC00`, `74HC02`, `74HC04`, `74HC07`, `74HC08`, `74HC10`, `74HC11`,
`74HC14`, `74HC20`, `74HC21`, `74HC27`, `74HC30`, `74HC32`, `74HC42`,
`74HC73`, `74HC74`, `74HC85`, `74HC86`, `74HC112`, `74HC138`, `74HC139`,
`74HC147`, `74HC148`, `74HC151`, `74HC153`, `74HC154`, `74HC155`, `74HC157`,
`74HC158`, `74HC160`, `74HC161`, `74HC162`, `74HC163`, `74HC164`, `74HC165`,
`74HC166`, `74HC181`, `74HC193`, `74HC238`, `74HC240`, `74HC244`, `74HC245`,
`74HC251`, `74HC257`, `74HC266`, `74HC273`, `74HC283`, `74HC352`, `74HC374`,
`74HC377`, `74HC4078`, `74HC541`, `74HC574`, `74HC593`, `74HC595`,
`74HC688`, and `74HC922`.

Modeled memory parts:

`62256`, `AS6C62256`, `AT28C256`, `CY7C199`, and `SST39SF010A`.

## Tested

Runnable test coverage is split by layer:

- Python behavior/catalog tests: `python3 -B -m tests.test_chips`
- Python design/netlist/CLI tests: `python3 -B -m tests.test_design`,
  `python3 -B -m tests.test_netlist`, and `python3 -B -m tests.test_cli`
- 74HC Verilog smoke: `iverilog ... 74HC/*.v ... && vvp ...`
- Memory Verilog smoke: `iverilog ... Memory/*.v ... && vvp ...`

Structural netlist-export compile tests currently cover every mapped part below:

`74HC00`, `74HC02`, `74HC04`, `74HC07`, `74HC08`, `74HC10`, `74HC11`,
`74HC14`, `74HC20`, `74HC21`, `74HC27`, `74HC30`, `74HC32`, `74HC42`,
`74HC73`, `74HC74`, `74HC85`, `74HC86`, `74HC112`, `74HC138`, `74HC139`,
`74HC148`, `74HC151`, `74HC153`, `74HC154`, `74HC155`, `74HC157`, `74HC158`,
`74HC160`, `74HC161`, `74HC162`, `74HC163`, `74HC164`, `74HC165`, `74HC166`,
`74HC181`, `74HC193`, `74HC238`, `74HC240`, `74HC244`, `74HC245`, `74HC251`,
`74HC257`, `74HC266`, `74HC273`, `74HC283`, `74HC352`, `74HC374`, `74HC377`,
`74HC4078`, `74HC541`, `74HC574`, `74HC593`, `74HC595`, `74HC688`,
`74HC922`, `62256`, `AS6C62256`, `AT28C256`, `CY7C199`, and `SST39SF010A`.

## Remaining Export Gap

`74HC147` is verified and modeled, but it is not yet enabled for structural
`Design.to_verilog()` export. The current pinout/model contract needs review
because the pinout file does not expose a complete 4-output mapping that can be
lowered to the existing Verilog module without guessing.

## Missing Datasheet

These parts were removed or kept out of the active catalog because
manufacturer-verified HC-family DIP evidence was not available:

- `74HC150`
- `74HC260`
