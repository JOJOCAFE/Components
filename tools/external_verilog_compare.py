#!/usr/bin/env python3
"""Compare local Verilog chip models against optional external 74xx references.

The external references are not vendored here. Download them into a temporary
directory and pass that directory with --external-dir. This avoids mixing
third-party HDL licensing into the Components source tree.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


REFERENCE_FILES = [
    "counter_74161.v",
    "counter_74193.v",
    "d_ff_7474.v",
    "decoder_74138.v",
    "decoder_74139.v",
    "mux_74151.v",
    "mux_74157.v",
    "register_74273.v",
    "selector_74153.v",
    "shift_74164.v",
    "shift_74165.v",
]


LOCAL_FILES = [
    "Verilog/74xx/74hc74.v",
    "Verilog/74xx/74hc138.v",
    "Verilog/74xx/74hc139.v",
    "Verilog/74xx/74hc151.v",
    "Verilog/74xx/74hc153.v",
    "Verilog/74xx/74hc157.v",
    "Verilog/74xx/74hc161.v",
    "Verilog/74xx/74hc164.v",
    "Verilog/74xx/74hc165.v",
    "Verilog/74xx/74hc193.v",
    "Verilog/74xx/74hc273.v",
]


TESTBENCH = r"""
`timescale 1ns/1ps
module tb_external_compare;
  integer failures = 0;

  task check;
    input condition;
    input [255:0] message;
    begin
      if (!condition) begin
        $display("FAIL: %0s", message);
        failures = failures + 1;
      end
    end
  endtask

  reg [1:0] ff_preset_bar = 2'b11;
  reg [1:0] ff_clear_bar = 2'b11;
  reg [1:0] ff_d = 2'b10;
  reg [1:0] ff_clk = 2'b00;
  wire [1:0] ff_q;
  wire [1:0] ff_q_bar;
  wire ext_ff_q;
  wire ext_ff_q_bar;
  ttl_74hc74 local74(.Preset_bar(ff_preset_bar), .Clear_bar(ff_clear_bar), .D(ff_d), .Clk(ff_clk), .Q(ff_q), .Q_bar(ff_q_bar));
  d_ff_7474 ext74(.d(ff_d[0]), .cp(ff_clk[0]), .n_cd(ff_clear_bar[0]), .n_sd(ff_preset_bar[0]), .q(ext_ff_q), .n_q(ext_ff_q_bar));

  reg dec_g1 = 1'b1;
  reg dec_g2a_bar = 1'b0;
  reg dec_g2b_bar = 1'b0;
  reg dec_a = 1'b1;
  reg dec_b = 1'b0;
  reg dec_c = 1'b1;
  wire [7:0] dec_y_bar;
  wire [7:0] ext_dec_y_bar;
  ttl_74hc138 local138(.A(dec_a), .B(dec_b), .C(dec_c), .G1(dec_g1), .G2A_bar(dec_g2a_bar), .G2B_bar(dec_g2b_bar), .Y_bar(dec_y_bar));
  decoder_74138 ext138(.a({dec_c, dec_b, dec_a}), .n_e1(dec_g2a_bar), .n_e2(dec_g2b_bar), .e3(dec_g1), .n_o(ext_dec_y_bar));

  reg [1:0] dec2_en_bar = 2'b00;
  reg [1:0] dec2_a = 2'b10;
  reg [1:0] dec2_b = 2'b01;
  wire [3:0] dec2_y1_bar;
  wire [3:0] dec2_y2_bar;
  wire [3:0] ext_dec2_y1_bar;
  ttl_74hc139 local139(.Enable_bar(dec2_en_bar), .A(dec2_a), .B(dec2_b), .Y1_bar(dec2_y1_bar), .Y2_bar(dec2_y2_bar));
  decoder_74139 ext139(.a({dec2_b[0], dec2_a[0]}), .n_e(dec2_en_bar[0]), .n_o(ext_dec2_y1_bar));

  reg sel8_en_bar = 1'b0;
  reg [2:0] sel8_sel = 3'd6;
  reg [7:0] sel8_d = 8'b0100_0000;
  wire sel8_y;
  wire sel8_y_bar;
  wire ext_sel8_y;
  wire ext_sel8_y_bar;
  ttl_74hc151 local151(.Enable_bar(sel8_en_bar), .Select(sel8_sel), .D(sel8_d), .Y(sel8_y), .Y_bar(sel8_y_bar));
  mux_74151 ext151(.n_g(sel8_en_bar), .d(sel8_d), .a(sel8_sel[0]), .b(sel8_sel[1]), .c(sel8_sel[2]), .y(ext_sel8_y), .w(ext_sel8_y_bar));

  reg [1:0] mux4_en_bar = 2'b00;
  reg [1:0] mux4_sel = 2'd2;
  reg [3:0] mux4_c1 = 4'b0100;
  reg [3:0] mux4_c2 = 4'b1011;
  wire mux4_y1;
  wire mux4_y2;
  wire ext_mux4_y1;
  wire ext_mux4_y2;
  ttl_74hc153 local153(.Enable_bar(mux4_en_bar), .Select(mux4_sel), .C1(mux4_c1), .C2(mux4_c2), .Y1(mux4_y1), .Y2(mux4_y2));
  selector_74153 ext153(.i1(mux4_c1), .i2(mux4_c2), .s(mux4_sel), .e1(mux4_en_bar[0]), .e2(mux4_en_bar[1]), .y1(ext_mux4_y1), .y2(ext_mux4_y2));

  reg mux157_en_bar = 1'b0;
  reg mux157_sel = 1'b1;
  reg [3:0] mux157_a = 4'ha;
  reg [3:0] mux157_b = 4'h5;
  wire [3:0] mux157_y;
  wire [3:0] ext_mux157_y;
  ttl_74hc157 local157(.Enable_bar(mux157_en_bar), .Select(mux157_sel), .A(mux157_a), .B(mux157_b), .Y(mux157_y));
  mux_74157 ext157(.i0(mux157_a), .i1(mux157_b), .s(mux157_sel), .n_e(mux157_en_bar), .z(ext_mux157_y));

  reg ctr_clear_bar = 1'b0;
  reg ctr_load_bar = 1'b1;
  reg ctr_ent = 1'b1;
  reg ctr_enp = 1'b1;
  reg [3:0] ctr_d = 4'h9;
  reg ctr_clk = 1'b0;
  wire ctr_rco;
  wire [3:0] ctr_q;
  wire ext_ctr_rco;
  wire [3:0] ext_ctr_q;
  ttl_74hc161 local161(.Clear_bar(ctr_clear_bar), .Load_bar(ctr_load_bar), .ENT(ctr_ent), .ENP(ctr_enp), .D(ctr_d), .Clk(ctr_clk), .RCO(ctr_rco), .Q(ctr_q));
  counter_74161 ext161(.clk(ctr_clk), .clr_n(ctr_clear_bar), .enp(ctr_enp), .ent(ctr_ent), .load_n(ctr_load_bar), .P(ctr_d), .Q(ext_ctr_q), .rco(ext_ctr_rco));

  reg sr_clear_bar = 1'b0;
  reg sr_clk = 1'b0;
  reg sr_a = 1'b1;
  reg sr_b = 1'b1;
  wire [7:0] sr_q;
  wire [7:0] ext_sr_q;
  ttl_74hc164 local164(.Clear_bar(sr_clear_bar), .Clk(sr_clk), .A(sr_a), .B(sr_b), .Q(sr_q));
  shift_74164 ext164(.cp(sr_clk), .n_mr(sr_clear_bar), .dsa(sr_a), .dsb(sr_b), .q(ext_sr_q));

  reg pls_load_bar = 1'b0;
  reg pls_clk = 1'b0;
  reg pls_inhibit = 1'b0;
  reg pls_serial = 1'b0;
  reg [7:0] pls_d = 8'h80;
  wire pls_qh;
  wire pls_qh_bar;
  wire ext_pls_qh;
  wire ext_pls_qh_bar;
  ttl_74hc165 local165(.ShiftLoad_bar(pls_load_bar), .Clk(pls_clk), .ClkInhibit(pls_inhibit), .Serial(pls_serial), .D(pls_d), .QH(pls_qh), .QH_bar(pls_qh_bar));
  shift_74165 ext165(.q7(ext_pls_qh), .n_q7(ext_pls_qh_bar), .ds(pls_serial), .d(pls_d), .n_pl(pls_load_bar), .cp(pls_clk), .n_ce(~pls_inhibit));

  reg reg_clear_bar = 1'b0;
  reg reg_clk = 1'b0;
  reg [7:0] reg_d = 8'h3c;
  wire [7:0] reg273_q;
  wire [7:0] ext_reg273_q;
  ttl_74hc273 local273(.Clear_bar(reg_clear_bar), .Clk(reg_clk), .D(reg_d), .Q(reg273_q));
  register_74273 ext273(.d(reg_d), .n_mr(reg_clear_bar), .cp(reg_clk), .q(ext_reg273_q));

  initial begin
    #20;
    ff_clear_bar = 2'b00; #20;
    check(ff_q[0] == ext_ff_q && ff_q_bar[0] == ext_ff_q_bar, "74HC74 clear matches external");
    ff_clear_bar = 2'b11; ff_d[0] = 1'b1; #5; ff_clk[0] = 1'b1; #1 ff_clk[0] = 1'b0; #20;
    check(ff_q[0] == ext_ff_q && ff_q_bar[0] == ext_ff_q_bar, "74HC74 clocked D matches external");

    check(dec_y_bar == ext_dec_y_bar, "74HC138 matches external");
    check(dec2_y1_bar == ext_dec2_y1_bar, "74HC139 unit 1 matches external");
    check(sel8_y == ext_sel8_y && sel8_y_bar == ext_sel8_y_bar, "74HC151 matches external");
    check(mux4_y1 == ext_mux4_y1 && mux4_y2 == ext_mux4_y2, "74HC153 matches external");
    check(mux157_y == ext_mux157_y, "74HC157 matches external");

    #20; check(ctr_q == ext_ctr_q, "74HC161 clear matches external");
    ctr_clear_bar = 1'b1; ctr_load_bar = 1'b0; #1 ctr_clk = 1'b1; #1 ctr_clk = 1'b0; #20;
    check(ctr_q == ext_ctr_q, "74HC161 load matches external");
    ctr_load_bar = 1'b1; #1 ctr_clk = 1'b1; #1 ctr_clk = 1'b0; #20;
    check(ctr_q == ext_ctr_q && ctr_rco == ext_ctr_rco, "74HC161 count matches external");

    #20; check(sr_q == ext_sr_q, "74HC164 clear matches external");
    sr_clear_bar = 1'b1; #1 sr_clk = 1'b1; #1 sr_clk = 1'b0; #20;
    check(sr_q == ext_sr_q, "74HC164 shift matches external");

    #20; check(pls_qh == ext_pls_qh && pls_qh_bar == ext_pls_qh_bar, "74HC165 load matches external");
    pls_load_bar = 1'b1; #1 pls_clk = 1'b1; #1 pls_clk = 1'b0; #20;
    check(pls_qh == ext_pls_qh && pls_qh_bar == ext_pls_qh_bar, "74HC165 shift matches external");

    #20; check(reg273_q == ext_reg273_q, "74HC273 clear matches external");
    reg_clear_bar = 1'b1; #1 reg_clk = 1'b1; #1 reg_clk = 1'b0; #20;
    check(reg273_q == ext_reg273_q, "74HC273 clocked D matches external");

    if (failures == 0) begin
      $display("EXTERNAL VERILOG COMPARE PASSED");
      $finish;
    end
    $display("EXTERNAL VERILOG COMPARE FAILED: %0d failures", failures);
    $fatal(1);
  end
endmodule
"""


def run(external_dir: Path) -> int:
    missing = [name for name in REFERENCE_FILES if not (external_dir / name).is_file()]
    if missing:
        print("missing external reference files:")
        for name in missing:
            print(f"  {name}")
        return 2

    iverilog = shutil.which("iverilog")
    vvp = shutil.which("vvp")
    if iverilog is None or vvp is None:
        print("SKIP: iverilog/vvp not installed")
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        tb = Path(tmp) / "tb_external_compare.v"
        out = Path(tmp) / "tb_external_compare.vvp"
        tb.write_text(TESTBENCH, encoding="utf-8")
        cmd = [
            iverilog,
            "-g2012",
            "-Wall",
            "-o",
            str(out),
            *[str(ROOT / path) for path in LOCAL_FILES],
            *[str(external_dir / name) for name in REFERENCE_FILES],
            str(tb),
        ]
        compiled = subprocess.run(cmd, text=True, capture_output=True, check=False)
        if compiled.stdout:
            print(compiled.stdout, end="")
        if compiled.stderr:
            print(compiled.stderr, end="")
        if compiled.returncode != 0:
            return compiled.returncode

        simulated = subprocess.run([vvp, str(out)], text=True, capture_output=True, check=False)
        if simulated.stdout:
            print(simulated.stdout, end="")
        if simulated.stderr:
            print(simulated.stderr, end="")
        return simulated.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--external-dir", type=Path, required=True)
    args = parser.parse_args()
    return run(args.external_dir)


if __name__ == "__main__":
    raise SystemExit(main())
