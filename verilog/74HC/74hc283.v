`timescale 1ns/1ps

// 74HC283: 4-bit binary full adder with carry

module ttl_74hc283 #(parameter WIDTH = 4, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [WIDTH-1:0] A,
  input [WIDTH-1:0] B,
  input C_in,
  output [WIDTH-1:0] Sum,
  output C_out
);

//------------------------------------------------//
reg [WIDTH-1:0] Sum_computed;
reg C_computed;

always @(*)
begin
  {C_computed, Sum_computed} = {1'b0, A} + {1'b0, B} + C_in;
end
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Sum = Sum_computed;
assign #(DELAY_RISE, DELAY_FALL) C_out = C_computed;

endmodule
