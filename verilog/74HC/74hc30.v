`timescale 1ns/1ps

// 74HC30: single 8-input NAND gate

module ttl_74hc30 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [7:0] A,
  output Y
);

wire Y_computed;

assign Y_computed = ~&A;

assign #(DELAY_RISE, DELAY_FALL) Y = Y_computed;

endmodule
