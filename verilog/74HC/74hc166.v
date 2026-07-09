`timescale 1ns/1ps

// 74HC166: 8-bit parallel-load shift register with serial output

module ttl_74hc166 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Clear_bar,
  input ShiftLoad_bar,
  input Clk,
  input ClkInhibit,
  input Serial,
  input [7:0] D,
  output QH
);

reg [7:0] q;

always @(posedge Clk or negedge Clear_bar) begin
  if (!Clear_bar) begin
    q <= 8'h00;
  end else if (!ClkInhibit) begin
    if (!ShiftLoad_bar) begin
      q <= D;
    end else begin
      q <= {q[6:0], Serial};
    end
  end
end

assign #(DELAY_RISE, DELAY_FALL) QH = q[7];

endmodule
