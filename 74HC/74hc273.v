`timescale 1ns/1ps

// 74HC273: octal D-type flip-flop with asynchronous clear

module ttl_74hc273 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Clear_bar,
  input Clk,
  input [7:0] D,
  output [7:0] Q
);

reg [7:0] q;

always @(posedge Clk or negedge Clear_bar) begin
  if (!Clear_bar) q <= 8'h00;
  else q <= D;
end

assign #(DELAY_RISE, DELAY_FALL) Q = q;

endmodule
