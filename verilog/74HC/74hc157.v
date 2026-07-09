`timescale 1ns/1ps

// 74HC157: quad 2-input multiplexer with active-low enable

module ttl_74hc157 #(parameter WIDTH = 4, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Enable_bar,
  input Select,
  input [WIDTH-1:0] A,
  input [WIDTH-1:0] B,
  output [WIDTH-1:0] Y
);

//------------------------------------------------//
wire [WIDTH-1:0] Y_computed;

assign Y_computed = Enable_bar ? {WIDTH{1'b0}} : (Select ? B : A);
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Y = Y_computed;

endmodule
