`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC4538 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments CD74HC4538: https://www.ti.com/lit/ds/symlink/cd74hc4538.pdf | N, 16-pin PDIP |
//
// ## 74HC4538 - Dual Precision Monostable Multivibrator, 16-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | 1Cx |
// | 2 | 1RxCx |
// | 3 | /1R |
// | 4 | 1A |
// | 5 | 1B |
// | 6 | 1Q |
// | 7 | /1Q |
// | 8 | GND |
// | 9 | /2Q |
// | 10 | 2Q |
// | 11 | 2B |
// | 12 | 2A |
// | 13 | /2R |
// | 14 | 2RxCx |
// | 15 | 2Cx |
// | 16 | VCC |
//
//


// 74HC4538: dual precision monostable multivibrator
module ttl_74hc4538 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [1:0] A,
  input [1:0] B,
  input [1:0] R_bar,
  output [1:0] Q,
  output [1:0] Q_bar
);

reg [1:0] q = 2'b00;

always @(posedge A[0] or negedge R_bar[0]) begin
  if (!R_bar[0]) q[0] <= 1'b0;
  else q[0] <= 1'b1;
end

always @(posedge A[1] or negedge R_bar[1]) begin
  if (!R_bar[1]) q[1] <= 1'b0;
  else q[1] <= 1'b1;
end

assign #(DELAY_RISE, DELAY_FALL) Q = q;
assign #(DELAY_RISE, DELAY_FALL) Q_bar = ~q;

endmodule
