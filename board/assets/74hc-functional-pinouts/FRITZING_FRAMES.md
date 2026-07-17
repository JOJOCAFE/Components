# Definition-backed Fritzing-style DIP frames

The outside-frame style is adapted from [https://github.com/Adr-hyng/74LS-Series-Fritzing-Parts/tree/main/Schematic](https://github.com/Adr-hyng/74LS-Series-Fritzing-Parts/tree/main/Schematic), licensed CC BY-SA 3.0. These derived SVGs are therefore distributed under CC BY-SA 3.0 with this attribution.

Local `symbol/dip.json` files—not the external 74LS schematics—supply pin numbers, names, sides, and directions. The external connector metadata is not reused because it can differ from visible labels.

For 74HC04, 74HC05, 74HC08, and 74HC14, the manifest links the existing Components internal functional-pinout SVG. A Board may compose that internal art inside this frame, but must obtain connectable ports from the resolved definition.
