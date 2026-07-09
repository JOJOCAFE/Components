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

- `74HC/`
- `Memory/`
- `python/chiplib/`

The DB is the new chip identity layer. Simulators, exporters, CLI tools, and
future UI/API code should eventually ask the DB what properties a chip has
instead of scattering chip facts across unrelated files.
