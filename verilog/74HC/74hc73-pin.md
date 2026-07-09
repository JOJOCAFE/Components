# 74HC73 DIP pinout

- Function: dual JK flip-flop with reset, negative-edge trigger
- Package verified: DIP14; NXP 74HC73N plastic dual in-line package SOT27-1
- Source: `../../source/74HC73_NXP_344664_DIPCHECK.pdf`

| Pin | Name |
| --- | --- |
| 1 | 1CP |
| 2 | 1R |
| 3 | 1K |
| 4 | VCC |
| 5 | 2CP |
| 6 | 2R |
| 7 | 2J |
| 8 | 2Q_bar |
| 9 | 2Q |
| 10 | 2K |
| 11 | GND |
| 12 | 1Q_bar |
| 13 | 1Q |
| 14 | 1J |

Notes:
- DIP verification: package/order table in the cited datasheet explicitly lists DIP/PDIP or an N/P plastic DIP package for this part.
- Datasheet prints complemented outputs with an overbar; `_bar` is used here for ASCII.
