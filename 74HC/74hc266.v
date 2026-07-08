`timescale 1ns/1ps

// 74HC266: Quad 2-input XNOR gate (OC)

// Note: For WIDTH_IN > 2, this is the "parity checker" interpretation of multi-input XOR (or XNOR)
// - conforms to chaining of XNOR to create arbitrary wider input, e.g. "(A XNOR B) XNOR C"

module ttl_74hc266 #(parameter BLOCKS = 4, WIDTH_IN = 2, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [BLOCKS*WIDTH_IN-1:0] A_2D,
  output [BLOCKS-1:0] Y
);

//------------------------------------------------//
wire [WIDTH_IN-1:0] A [0:BLOCKS-1];
reg [BLOCKS-1:0] computed;
integer i;

always @(*)
begin
  for (i = 0; i < BLOCKS; i++)
    computed[i] = ~(^A[i]);
end
//------------------------------------------------//

wire [BLOCKS*WIDTH_IN-1:0] A_pack_in;
assign A_pack_in = A_2D;
generate
  genvar unpk_idx;
  for (unpk_idx = 0; unpk_idx < BLOCKS; unpk_idx = unpk_idx + 1) begin: gen_unpack
    assign A[unpk_idx][WIDTH_IN-1:0] = A_pack_in[WIDTH_IN*unpk_idx+:WIDTH_IN];
  end
endgenerate
assign #(DELAY_RISE, DELAY_FALL) Y = computed;

endmodule
