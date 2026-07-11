# External Vendor Models

This folder stores official vendor product-page snapshots and simulation models
used by `tools/external_model_crosscheck.py`.

Current scope:

- `SN74HC00_TI_product.html`: TI product page snapshot for SN74HC00.
- `SN74HC00_TI_SCLM235.zip`: TI SN74HC00 Behavioral SPICE model download from
  `https://www.ti.com/lit/zip/sclm235`.
- `SN74HC00_TI_SCLM235/SN74HC00.cir`: extracted TI PSpice/TINA behavioral
  model. The cross-check parses the NAND function and timing table, then runs
  all four NAND truth cases through `ngspice` with PSpice compatibility mode
  enabled by `set ngbehavior=psa`.
- `SN74HC245_TI_product.html`: TI product page snapshot. The saved page confirms
  the bus-transceiver behavior but did not expose a chip-specific simulation
  model link during this pass.
- `SN74HC595_TI_product.html`: TI product page snapshot. The saved page confirms
  shift-register, storage-register, and 3-state output behavior but did not
  expose a chip-specific simulation model link during this pass.
- `SN74HC161_TI_product.html`, `SN74HC574_TI_product.html`,
  `SN74HC165_TI_product.html`, and `SN74HC166_TI_product.html`: TI product page
  snapshots for state-critical counter/register/shift-register parts. The saved
  pages confirm official product-page behavior terms but did not expose
  chip-specific simulation model ZIP links during this pass.
- `NE555_TI_product.html` and `MAX232_TI_product.html`: TI support/interface
  product page snapshots. The saved pages confirm official product-page
  descriptions, but no chip-specific model ZIP link was exposed in these
  snapshots.
- `LM358_TI_product.html`: TI product page snapshot for LM358. The saved page
  exposes official model links `/lit/zip/snom268`, `/lit/zip/snom670`, and
  `/lit/zip/snom671`.
- `LM358_TI_SNOM268.zip` plus `LM358_TI_SNOM268/lmx58_lm2904.lib`: TI PSpice
  op-amp macro-model archive and extracted library. The cross-check runs a
  non-inverting operating-point smoke through `ngspice` with PSpice
  compatibility mode enabled by `set ngbehavior=psa`.
- `LM358_TI_SNOM670.zip` plus `LM358_TI_SNOM670/LMx58_LM2904.TSM`: TI TINA
  macro archive and extracted macro.
- `LM358_TI_SNOM671.zip` plus
  `LM358_TI_SNOM671/LMx58_LM2904_RefDesign.TSC`: TI TINA reference design
  archive and extracted design.
- `LM393_TI_product.html`: TI product page snapshot for LM393. The saved page
  exposes official model links `/lit/zip/slcj016` and `/lit/zip/slcm004`.
- `LM393_TI_SLCJ016.zip` plus `LM393_TI_SLCJ016/lm393.lib`: TI PSpice
  comparator model archive and extracted library. The library identifies the
  included macro-model as LM2903B-family comparator content. The cross-check
  runs a comparator operating-point smoke through `ngspice` with PSpice
  compatibility mode enabled by `set ngbehavior=psa`.
- `LM393_TI_SLCM004.zip` plus `LM393_TI_SLCM004/TINA/Macro/LM393.TSM`: TI TINA
  macro archive and extracted macro.

Do not treat product-page text as simulator evidence. Reports must distinguish
`VENDOR_SIM_PASS`, `VENDOR_MODEL_STRUCTURAL_PASS`, and
`VENDOR_MODEL_PRESENT_NO_LOCAL_DIGITAL_MODEL` from
`SOURCE_CONFIRMED_NO_VENDOR_SIM`.
