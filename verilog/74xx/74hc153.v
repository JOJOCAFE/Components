`timescale 1ns/1ps

// 74HC153: dual 4-line to 1-line data selector/multiplexer

module ttl_74hc153 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [1:0] Enable_bar,
  input [1:0] Select,
  input [3:0] C1,
  input [3:0] C2,
  output Y1,
  output Y2
);

wire y1_computed;
wire y2_computed;

assign y1_computed = Enable_bar[0] ? 1'b0 : C1[Select];
assign y2_computed = Enable_bar[1] ? 1'b0 : C2[Select];

assign #(DELAY_RISE, DELAY_FALL) Y1 = y1_computed;
assign #(DELAY_RISE, DELAY_FALL) Y2 = y2_computed;

endmodule
