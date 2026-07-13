# RV8GR Interrupt Enable

This small child owns only the real v1.0 path `U33-8 EI_decode -> U31-3 IE`.
It uses the documented `T2 AND SRC AND /XOR_MODE AND /AC_WR` decode and the
actual 74HC74 state element. It does not model IRQ release, polling software,
automatic vectoring, or physical timing signoff.
