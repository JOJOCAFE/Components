`timescale 1ns/1ps

// 74HC593: 8-bit binary counter with input register and 3-state I/O bus

module ttl_74hc593 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  inout [7:0] A_Q,
  input CLOAD,
  output RCO,
  input CCLR,
  input CCK,
  input CCKEN,
  input CCKEN_bar,
  input RCK,
  input RCKEN,
  input G,
  input G_bar
);

reg [7:0] counter;
reg [7:0] input_register;

wire output_enabled;
wire count_enabled;

assign output_enabled = G | ~G_bar;
assign count_enabled = CCKEN | ~CCKEN_bar;

always @(posedge RCK) begin
  if (!RCKEN) begin
    input_register <= A_Q;
  end
end

always @(posedge CCK or negedge CCLR or negedge CLOAD) begin
  if (!CCLR) begin
    counter <= 8'h00;
  end else if (!CLOAD) begin
    counter <= output_enabled ? input_register : A_Q;
  end else if (count_enabled) begin
    counter <= counter + 8'h01;
  end
end

assign #(DELAY_RISE, DELAY_FALL) A_Q = output_enabled ? counter : 8'hzz;
assign #(DELAY_RISE, DELAY_FALL) RCO = (counter == 8'h00);

endmodule
