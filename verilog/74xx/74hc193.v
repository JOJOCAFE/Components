`timescale 1ns/1ps

// 74HC193: 4-bit synchronous up/down binary counter

module ttl_74hc193 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Clear,
  input Load_bar,
  input Up,
  input Down,
  input [3:0] D,
  output [3:0] Q,
  output Carry_bar,
  output Borrow_bar
);

reg [3:0] q;

always @(posedge Up or posedge Clear or negedge Load_bar) begin
  if (Clear) q <= 4'h0;
  else if (!Load_bar) q <= D;
  else if (Down) q <= q + 4'h1;
end

always @(posedge Down or posedge Clear or negedge Load_bar) begin
  if (Clear) q <= 4'h0;
  else if (!Load_bar) q <= D;
  else if (Up) q <= q - 4'h1;
end

assign #(DELAY_RISE, DELAY_FALL) Q = q;
assign #(DELAY_RISE, DELAY_FALL) Carry_bar = ~(Up == 1'b0 && q == 4'hf);
assign #(DELAY_RISE, DELAY_FALL) Borrow_bar = ~(Down == 1'b0 && q == 4'h0);

endmodule
