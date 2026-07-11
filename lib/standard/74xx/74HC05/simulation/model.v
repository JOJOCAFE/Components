`timescale 1ns/1ps

//
// Embedded pinout documentation.
// This block replaces the former standalone pinout Markdown file.
// # 74HC05 DIP Pinout
//
// Active-low pins are written with a leading slash, for example `/OE`.
//
// | Manufacturer datasheet | DIP package checked |
// |---|---|
// | Texas Instruments SN74HC05: https://www.ti.com/lit/ds/symlink/sn74hc05.pdf | N, 14-pin PDIP |
//
// ## 74HC05 - Hex Inverter With Open-Drain Outputs, 14-Pin DIP
//
// | Pin | Name |
// |---:|---|
// | 1 | 1A |
// | 2 | 1Y |
// | 3 | 2A |
// | 4 | 2Y |
// | 5 | 3A |
// | 6 | 3Y |
// | 7 | GND |
// | 8 | 4Y |
// | 9 | 4A |
// | 10 | 5Y |
// | 11 | 5A |
// | 12 | 6Y |
// | 13 | 6A |
// | 14 | VCC |
//
//


// 74HC05: hex inverter with open-drain outputs
module ttl_74hc05 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [5:0] A,
  output [5:0] Y
);

wire [5:0] inv_value = ~A;

genvar i;
generate
  for (i = 0; i < 6; i = i + 1) begin : open_drain_outputs
    assign #(DELAY_RISE, DELAY_FALL) Y[i] = inv_value[i] ? 1'bz : 1'b0;
  end
endgenerate

endmodule
