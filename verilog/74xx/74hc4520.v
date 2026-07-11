`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC4520 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments CD74HC4520: https://www.ti.com/lit/ds/symlink/cd74hc4520.pdf | N, 16-pin PDIP |
//
// ## 74HC4520 - Dual 4-Bit Binary Counter, 16-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | 1CP |
// | 2 | 1E |
// | 3 | 1Q0 |
// | 4 | 1Q1 |
// | 5 | 1Q2 |
// | 6 | 1Q3 |
// | 7 | 1MR |
// | 8 | GND |
// | 9 | 2CP |
// | 10 | 2E |
// | 11 | 2Q0 |
// | 12 | 2Q1 |
// | 13 | 2Q2 |
// | 14 | 2Q3 |
// | 15 | 2MR |
// | 16 | VCC |
//
//


// 74HC4520: dual 4-bit binary counter
module ttl_74hc4520 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [1:0] CP,
  input [1:0] E,
  input [1:0] MR,
  output [3:0] Q1,
  output [3:0] Q2
);

reg [3:0] q1 = 4'h0;
reg [3:0] q2 = 4'h0;

always @(posedge CP[0] or posedge MR[0]) begin
  if (MR[0]) q1 <= 4'h0;
  else if (E[0]) q1 <= q1 + 4'h1;
end

always @(posedge CP[1] or posedge MR[1]) begin
  if (MR[1]) q2 <= 4'h0;
  else if (E[1]) q2 <= q2 + 4'h1;
end

assign #(DELAY_RISE, DELAY_FALL) Q1 = MR[0] ? 4'h0 : q1;
assign #(DELAY_RISE, DELAY_FALL) Q2 = MR[1] ? 4'h0 : q2;

endmodule
