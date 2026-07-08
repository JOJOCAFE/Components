`timescale 1ns/1ps

// 74HC541: octal buffer/line driver with 3-state outputs

module ttl_74hc541 #(parameter WIDTH = 8, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input OE1_bar,
  input OE2_bar,
  input [WIDTH-1:0] A,
  output [WIDTH-1:0] Y
);

//------------------------------------------------//
wire [WIDTH-1:0] Y_computed;

assign Y_computed = (!OE1_bar && !OE2_bar) ? A : {WIDTH{1'bz}};
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Y = Y_computed;

endmodule
