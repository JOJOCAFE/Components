`timescale 1ns/1ps

// 74HC139: dual 2-line to 4-line decoder/demultiplexer, active-low outputs

module ttl_74hc139 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [1:0] Enable_bar,
  input [1:0] A,
  input [1:0] B,
  output [3:0] Y1_bar,
  output [3:0] Y2_bar
);

reg [3:0] y1_next;
reg [3:0] y2_next;

always @* begin
  y1_next = 4'hf;
  y2_next = 4'hf;
  if (!Enable_bar[0]) y1_next[{B[0], A[0]}] = 1'b0;
  if (!Enable_bar[1]) y2_next[{B[1], A[1]}] = 1'b0;
end

assign #(DELAY_RISE, DELAY_FALL) Y1_bar = y1_next;
assign #(DELAY_RISE, DELAY_FALL) Y2_bar = y2_next;

endmodule
