`timescale 1ns/1ps

// 74HC161: 4-bit binary counter with parallel load and asynchronous clear

module ttl_74hc161 #(parameter WIDTH = 4, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input Clear_bar,
  input Load_bar,
  input ENT,
  input ENP,
  input [WIDTH-1:0] D,
  input Clk,
  output RCO,
  output [WIDTH-1:0] Q
);

//------------------------------------------------//
reg [WIDTH-1:0] Q_current;
wire [WIDTH-1:0] Q_next;
wire RCO_current;

assign Q_next = Q_current + {{WIDTH-1{1'b0}}, 1'b1};

always @(posedge Clk or negedge Clear_bar)
begin
  if (!Clear_bar)
    Q_current <= {WIDTH{1'b0}};
  else if (!Load_bar)
    Q_current <= D;
  else if (ENT && ENP)
    Q_current <= Q_next;
end

assign RCO_current = ENT && (&Q_current);
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) RCO = RCO_current;
assign #(DELAY_RISE, DELAY_FALL) Q = Q_current;

endmodule
