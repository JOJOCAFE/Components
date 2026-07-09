# Components DB

Per-chip component database for the shared Components library.

This is the long-term chip-centered structure:

```text
db/
  74HC00/
    chip.json
  74HC04/
    chip.json
  62256/
    chip.json
  74HC161/
    chip.json
  74HC245/
    chip.json
  AT28C256/
    chip.json
  74HC74/
    chip.json
  74HC574/
    chip.json
  74HC138/
    chip.json
  SST39SF010A/
    chip.json
```

Each chip owns one manifest. The manifest may reference existing legacy files
while the repo migrates gradually:

- pinout evidence docs
- Verilog model
- Python behavior provider
- Verilog export mapping status
- tests
- datasheet/source evidence

The manifest shape is defined by `chip.schema.json`.

Missing properties are allowed, but they must be visible through manifest
status and loader reports. A chip folder is valid as long as `chip.json` is
readable and identifies the part.

The old layout remains active during migration:

- `verilog/74HC/`
- `Memory/`
- `python/chiplib/`

The DB is the new chip identity layer. Simulators, exporters, CLI tools, and
future UI/API code should eventually ask the DB what properties a chip has
instead of scattering chip facts across unrelated files.

The first seed set intentionally covers simple gates, a sequential counter, a
bidirectional bus transceiver, SRAM, and EEPROM:

- `74HC00`
- `74HC04`
- `74HC161`
- `74HC245`
- `62256`
- `AT28C256`

The next useful set adds flip-flop, register, decoder, and flash coverage:

- `74HC74`
- `74HC574`
- `74HC138`
- `SST39SF010A`

The DB now has one manifest for every active legacy Verilog model and pinout
entry: 62 DB parts for 62 legacy model parts.

Audit the DB against the active legacy catalog:

```sh
cd ../python
python3 -m chiplib.cli db --audit
python3 -m chiplib.cli db --status
```
