`timescale 1ns/1ps

// 74HC21: dual 4-input AND gate

module ttl_74hc21 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [1:0] A,
  input [1:0] B,
  input [1:0] C,
  input [1:0] D,
  output [1:0] Y
);

//------------------------------------------------//
wire [1:0] Y_computed;

assign Y_computed = A & B & C & D;
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Y = Y_computed;

endmodule
