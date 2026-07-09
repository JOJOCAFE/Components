`timescale 1ns/1ps

// 74HC164: 8-bit serial-in parallel-out shift register with asynchronous clear

module ttl_74hc164 #(parameter WIDTH = 8, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Clear_bar,
  input Clk,
  input A,
  input B,
  output [WIDTH-1:0] Q
);

//------------------------------------------------//
reg [WIDTH-1:0] Q_current;
wire Serial_in;

assign Serial_in = A & B;

always @(posedge Clk or negedge Clear_bar)
begin
  if (!Clear_bar)
    Q_current <= {WIDTH{1'b0}};
  else
    Q_current <= {Q_current[WIDTH-2:0], Serial_in};
end
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Q = Q_current;

endmodule
