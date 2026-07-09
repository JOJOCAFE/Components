`timescale 1ns/1ps

// 74HC240: octal inverting buffer/line driver with 3-state outputs

module ttl_74hc240 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input OE1_bar,
  input OE2_bar,
  input [7:0] A,
  output [7:0] Y
);

assign #(DELAY_RISE, DELAY_FALL) Y[3:0] = OE1_bar ? 4'hz : ~A[3:0];
assign #(DELAY_RISE, DELAY_FALL) Y[7:4] = OE2_bar ? 4'hz : ~A[7:4];

endmodule
