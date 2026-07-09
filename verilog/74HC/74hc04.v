`timescale 1ns/1ps

// 74HC04: hex inverter

module ttl_74hc04 #(parameter WIDTH = 6, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [WIDTH-1:0] A,
  output [WIDTH-1:0] Y
);

//------------------------------------------------//
wire [WIDTH-1:0] Y_computed;

assign Y_computed = ~A;
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Y = Y_computed;

endmodule
