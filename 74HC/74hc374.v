`timescale 1ns/1ps

// 74HC374: octal D-type flip-flop with 3-state outputs

module ttl_74hc374 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input OE_bar,
  input Clk,
  input [7:0] D,
  output [7:0] Q
);

reg [7:0] q;

always @(posedge Clk) begin
  q <= D;
end

assign #(DELAY_RISE, DELAY_FALL) Q = OE_bar ? 8'hzz : q;

endmodule
