`timescale 1ns/1ps

// 74HC4078: 8-input NOR/OR gate

module ttl_74hc4078 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [7:0] A,
  output X,
  output Y
);

wire any_high;

assign any_high = |A;

assign #(DELAY_RISE, DELAY_FALL) X = ~any_high;
assign #(DELAY_RISE, DELAY_FALL) Y = any_high;

endmodule
