`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HCT245 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HCT245: https://www.ti.com/lit/ds/symlink/sn74hct245.pdf | N, 20-pin PDIP |
//
// ## 74HCT245 - Octal Bus Transceiver, 20-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | DIR |
// | 2 | A1 |
// | 3 | A2 |
// | 4 | A3 |
// | 5 | A4 |
// | 6 | A5 |
// | 7 | A6 |
// | 8 | A7 |
// | 9 | A8 |
// | 10 | GND |
// | 11 | B8 |
// | 12 | B7 |
// | 13 | B6 |
// | 14 | B5 |
// | 15 | B4 |
// | 16 | B3 |
// | 17 | B2 |
// | 18 | B1 |
// | 19 | /OE |
// | 20 | VCC |
//
//


// 74HCT245: octal bus transceiver
module ttl_74hct245 #(parameter WIDTH = 8, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input OE_bar,
  input DIR,
  inout [WIDTH-1:0] A,
  inout [WIDTH-1:0] B
);

assign #(DELAY_RISE, DELAY_FALL) A = (!OE_bar && !DIR) ? B : {WIDTH{1'bz}};
assign #(DELAY_RISE, DELAY_FALL) B = (!OE_bar &&  DIR) ? A : {WIDTH{1'bz}};

endmodule
