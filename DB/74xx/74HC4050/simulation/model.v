`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC4050 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments CD74HC4050: https://www.ti.com/lit/ds/symlink/cd74hc4050.pdf | N, 16-pin PDIP |
//
// ## 74HC4050 - Hex Non-Inverting Buffer, 16-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | VCC |
// | 2 | 1Y |
// | 3 | 1A |
// | 4 | 2Y |
// | 5 | 2A |
// | 6 | 3Y |
// | 7 | 3A |
// | 8 | GND |
// | 9 | 4A |
// | 10 | 4Y |
// | 11 | 5A |
// | 12 | 5Y |
// | 13 | NC |
// | 14 | 6A |
// | 15 | 6Y |
// | 16 | NC |
//
//


// 74HC4050: hex non-inverting buffer
module ttl_74hc4050 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [5:0] A,
  output [5:0] Y
);

assign #(DELAY_RISE, DELAY_FALL) Y = A;

endmodule
