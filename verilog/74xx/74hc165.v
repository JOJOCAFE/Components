`timescale 1ns/1ps

// 74HC165: 8-bit parallel-load shift register

module ttl_74hc165 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input ShiftLoad_bar,
  input Clk,
  input ClkInhibit,
  input Serial,
  input [7:0] D,
  output QH,
  output QH_bar
);

reg [7:0] q;

always @(posedge Clk or negedge ShiftLoad_bar) begin
  if (!ShiftLoad_bar) begin
    q <= D;
  end else if (!ClkInhibit) begin
    q <= {q[6:0], Serial};
  end
end

assign #(DELAY_RISE, DELAY_FALL) QH = q[7];
assign #(DELAY_RISE, DELAY_FALL) QH_bar = ~q[7];

endmodule
