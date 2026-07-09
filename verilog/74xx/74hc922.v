`timescale 1ns/1ps

// 74HC922/MM74C922: 16-key encoder behavioral model

module ttl_74hc922 #(parameter DELAY_RISE = 0, DELAY_FALL = 0)
(
  input [3:0] RowY,
  output reg [3:0] ColumnX,
  input Oscillator,
  input KeybounceMask,
  input OutputEnable,
  output [3:0] DataOut,
  output DataAvailable
);

reg [1:0] scan_col;
reg [3:0] latched_code;
reg data_available;
integer row_index;

initial begin
  scan_col = 2'd0;
  ColumnX = 4'b1110;
  latched_code = 4'h0;
  data_available = 1'b0;
end

always @(posedge Oscillator) begin
  scan_col <= scan_col + 2'd1;
  ColumnX <= ~(4'b0001 << (scan_col + 2'd1));
end

always @* begin
  data_available = 1'b0;
  latched_code = {2'b00, scan_col};

  for (row_index = 0; row_index < 4; row_index = row_index + 1) begin
    if (!RowY[row_index]) begin
      data_available = 1'b1;
      latched_code = {row_index[1:0], scan_col};
    end
  end
end

assign #(DELAY_RISE, DELAY_FALL) DataAvailable = data_available & KeybounceMask;
assign #(DELAY_RISE, DELAY_FALL) DataOut = OutputEnable ? 4'hz : latched_code;

endmodule
