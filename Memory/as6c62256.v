`timescale 1ns/1ps

// AS6C62256: 32K x 8 static RAM wrapper

module mem_as6c62256 #(parameter ADDR_WIDTH = 15, DATA_WIDTH = 8, INIT_FILE = "")
(
  input [ADDR_WIDTH-1:0] A,
  inout [DATA_WIDTH-1:0] DQ,
  input CE_bar,
  input OE_bar,
  input WE_bar
);

  mem_62256 #(.ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH), .INIT_FILE(INIT_FILE)) ram (
    .A(A),
    .DQ(DQ),
    .CE_bar(CE_bar),
    .OE_bar(OE_bar),
    .WE_bar(WE_bar)
  );
endmodule
