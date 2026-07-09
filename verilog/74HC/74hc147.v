`timescale 1ns/1ps

// 74HC147: 10-line to 4-line priority encoder

module ttl_74hc147 #(parameter WIDTH_IN = 9, WIDTH_OUT = 4, DELAY_RISE = 0, DELAY_FALL = 0)
(
  input I0_bar,
  input [WIDTH_IN-1:0] A_bar,
  output [WIDTH_OUT-1:0] Y_bar
);

//------------------------------------------------//
reg [WIDTH_OUT-1:0] computed;

always @(*)
begin
  casez ({A_bar, I0_bar})
    10'b0?????????: computed = 4'b1001;  // highest priority (inverted)
    10'b10????????: computed = 4'b1000;
    10'b110???????: computed = 4'b0111;
    10'b1110??????: computed = 4'b0110;
    10'b11110?????: computed = 4'b0101;
    10'b111110????: computed = 4'b0100;
    10'b1111110???: computed = 4'b0011;
    10'b11111110??: computed = 4'b0010;
    10'b111111110?: computed = 4'b0001;
    10'b1111111110: computed = 4'b0000;
    10'b1111111111: computed = 4'b0000;
    default:        computed = 4'b0000;
  endcase
end
//------------------------------------------------//

assign #(DELAY_RISE, DELAY_FALL) Y_bar = ~computed;

endmodule
