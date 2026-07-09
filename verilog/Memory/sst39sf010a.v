`timescale 1ns/1ps

// SST39SF010A: 128K x 8 flash EEPROM, simulation model

module mem_sst39sf010a #(parameter ADDR_WIDTH = 17, DATA_WIDTH = 8, INIT_FILE = "")
(
  input [ADDR_WIDTH-1:0] A,
  inout [DATA_WIDTH-1:0] DQ,
  input CE_bar,
  input OE_bar,
  input WE_bar
);

  reg [DATA_WIDTH-1:0] memory [0:(1 << ADDR_WIDTH)-1];
  wire read_enable;
  wire write_enable;

  assign read_enable = !CE_bar && !OE_bar && WE_bar;
  assign write_enable = !CE_bar && OE_bar && !WE_bar;
  assign DQ = read_enable ? memory[A] : {DATA_WIDTH{1'bz}};

  always @(negedge WE_bar) begin
    if (write_enable)
      memory[A] <= DQ;
  end

  initial begin
    if (INIT_FILE != "")
      $readmemh(INIT_FILE, memory);
  end
endmodule
