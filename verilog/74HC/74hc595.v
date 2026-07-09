`timescale 1ns/1ps

// 74HC595: 8-bit serial-in shift register with output storage register

module ttl_74hc595 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input SER,
  input SRCLK,
  input RCLK,
  input SRCLR_bar,
  input OE_bar,
  output [7:0] Q,
  output QH_prime
);

reg [7:0] shift_q;
reg [7:0] store_q;

always @(posedge SRCLK or negedge SRCLR_bar) begin
  if (!SRCLR_bar) shift_q <= 8'h00;
  else shift_q <= {shift_q[6:0], SER};
end

always @(posedge RCLK) begin
  store_q <= shift_q;
end

assign #(DELAY_RISE, DELAY_FALL) Q = OE_bar ? 8'hzz : store_q;
assign #(DELAY_RISE, DELAY_FALL) QH_prime = shift_q[7];

endmodule
