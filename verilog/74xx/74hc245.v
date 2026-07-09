`timescale 1ns/1ps

// 74HC245: octal bus transceiver with 3-state outputs

module ttl_74hc245 #(parameter WIDTH = 8, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input OE_bar,
  input DIR,
  inout [WIDTH-1:0] A,
  inout [WIDTH-1:0] B
);

//------------------------------------------------//
wire [WIDTH-1:0] A_drive;
wire [WIDTH-1:0] B_drive;

assign A_drive = (!OE_bar && !DIR) ? B : {WIDTH{1'bz}};
assign B_drive = (!OE_bar &&  DIR) ? A : {WIDTH{1'bz}};
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) A = A_drive;
assign #(DELAY_RISE, DELAY_FALL) B = B_drive;

endmodule
