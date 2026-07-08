`timescale 1ns/1ps

// 74HC151: 8-line to 1-line data selector/multiplexer

module ttl_74hc151 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Enable_bar,
  input [2:0] Select,
  input [7:0] D,
  output Y,
  output Y_bar
);

wire y_computed;

assign y_computed = Enable_bar ? 1'b0 : D[Select];

assign #(DELAY_RISE, DELAY_FALL) Y = y_computed;
assign #(DELAY_RISE, DELAY_FALL) Y_bar = ~y_computed;

endmodule
