`timescale 1ns/1ps

// 74HC251: 8-line to 1-line data selector/multiplexer with 3-state outputs

module ttl_74hc251 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input OE_bar,
  input [2:0] Select,
  input [7:0] D,
  output Y,
  output Y_bar
);

wire selected;

assign selected = D[Select];
assign #(DELAY_RISE, DELAY_FALL) Y = OE_bar ? 1'bz : selected;
assign #(DELAY_RISE, DELAY_FALL) Y_bar = OE_bar ? 1'bz : ~selected;

endmodule
