`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HCT541 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HCT541: https://www.ti.com/lit/ds/symlink/sn74hct541.pdf | N, 20-pin PDIP |
//
// ## 74HCT541 - Octal Buffer/Line Driver, 20-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | /OE1 |
// | 2 | A1 |
// | 3 | A2 |
// | 4 | A3 |
// | 5 | A4 |
// | 6 | A5 |
// | 7 | A6 |
// | 8 | A7 |
// | 9 | A8 |
// | 10 | GND |
// | 11 | Y8 |
// | 12 | Y7 |
// | 13 | Y6 |
// | 14 | Y5 |
// | 15 | Y4 |
// | 16 | Y3 |
// | 17 | Y2 |
// | 18 | Y1 |
// | 19 | /OE2 |
// | 20 | VCC |
//
//


// 74HCT541: octal buffer/line driver
module ttl_74hct541 #(parameter WIDTH = 8, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input OE1_bar,
  input OE2_bar,
  input [WIDTH-1:0] A,
  output [WIDTH-1:0] Y
);

assign #(DELAY_RISE, DELAY_FALL) Y = (!OE1_bar && !OE2_bar) ? A : {WIDTH{1'bz}};

endmodule
