`timescale 1ns/1ps

// 74HC08: quad 2-input AND gate

module ttl_74hc08 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [3:0] A,
  input [3:0] B,
  output [3:0] Y
);

wire [3:0] Y_computed;

assign Y_computed = A & B;

assign #(DELAY_RISE, DELAY_FALL) Y = Y_computed;

endmodule
