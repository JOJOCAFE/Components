`timescale 1ns/1ps

// 74HC574: octal D-type flip-flop with 3-state outputs

module ttl_74hc574 #(parameter WIDTH = 8, DELAY_RISE = 0, DELAY_FALL = 0, SAMPLE_DELAY = 0)
(
  input OE_bar,
  input Clk,
  input [WIDTH-1:0] D,
  output [WIDTH-1:0] Q
);

//------------------------------------------------//
reg [WIDTH-1:0] Q_current;
wire [WIDTH-1:0] Q_drive;

always @(posedge Clk)
begin
  if (SAMPLE_DELAY == 0)
    Q_current <= D;
  else begin
    #SAMPLE_DELAY;
    Q_current <= D;
  end
end

assign Q_drive = OE_bar ? {WIDTH{1'bz}} : Q_current;
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Q = Q_drive;

endmodule
