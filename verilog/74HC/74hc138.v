`timescale 1ns/1ps

// 74HC138: 3-line to 8-line decoder/demultiplexer, active-low outputs

module ttl_74hc138 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input A,
  input B,
  input C,
  input G1,
  input G2A_bar,
  input G2B_bar,
  output [7:0] Y_bar
);

wire enabled;
wire [2:0] sel;
reg [7:0] y_next;

assign enabled = G1 & ~G2A_bar & ~G2B_bar;
assign sel = {C, B, A};

always @* begin
  y_next = 8'hff;
  if (enabled) begin
    y_next[sel] = 1'b0;
  end
end

assign #(DELAY_RISE, DELAY_FALL) Y_bar = y_next;

endmodule
