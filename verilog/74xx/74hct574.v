`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HCT574 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HCT574: https://www.ti.com/lit/ds/symlink/sn74hct574.pdf | N, 20-pin PDIP |
//
// ## 74HCT574 - Octal D-Type Flip-Flop, 20-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | /OE |
// | 2 | 1D |
// | 3 | 2D |
// | 4 | 3D |
// | 5 | 4D |
// | 6 | 5D |
// | 7 | 6D |
// | 8 | 7D |
// | 9 | 8D |
// | 10 | GND |
// | 11 | CLK |
// | 12 | 8Q |
// | 13 | 7Q |
// | 14 | 6Q |
// | 15 | 5Q |
// | 16 | 4Q |
// | 17 | 3Q |
// | 18 | 2Q |
// | 19 | 1Q |
// | 20 | VCC |
//
//


// 74HCT574: octal d-type flip-flop
module ttl_74hct574 #(parameter WIDTH = 8, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input OE_bar,
  input Clk,
  input [WIDTH-1:0] D,
  output [WIDTH-1:0] Q
);

reg [WIDTH-1:0] q_current;

always @(posedge Clk) begin
  q_current <= D;
end

assign #(DELAY_RISE, DELAY_FALL) Q = OE_bar ? {WIDTH{1'bz}} : q_current;

endmodule
