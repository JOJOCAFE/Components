`timescale 1ns/1ps

// 74HC688: 8-bit identity comparator with active-low enable and output

module ttl_74hc688 #(parameter WIDTH = 8, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Enable_bar,
  input [WIDTH-1:0] A,
  input [WIDTH-1:0] B,
  output Equal_bar
);

//------------------------------------------------//
wire Equal_bar_computed;

assign Equal_bar_computed = Enable_bar ? 1'b1 : (A == B ? 1'b0 : 1'b1);
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Equal_bar = Equal_bar_computed;

endmodule
