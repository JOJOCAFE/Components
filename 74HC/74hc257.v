`timescale 1ns/1ps

// 74HC257: quad 2-input multiplexer with 3-state outputs

module ttl_74hc257 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input OE_bar,
  input Select,
  input [3:0] A,
  input [3:0] B,
  output [3:0] Y
);

assign #(DELAY_RISE, DELAY_FALL) Y = OE_bar ? 4'hz : (Select ? B : A);

endmodule
