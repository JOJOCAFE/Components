`timescale 1ns/1ps

// 74HC14: hex Schmitt-trigger inverter

module ttl_74hc14 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [5:0] A,
  output [5:0] Y
);

wire [5:0] Y_computed;

assign Y_computed = ~A;

assign #(DELAY_RISE, DELAY_FALL) Y = Y_computed;

endmodule
