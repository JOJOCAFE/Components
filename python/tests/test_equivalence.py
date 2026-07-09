"""Python-vs-Verilog equivalence smoke tests for representative chips."""

from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from chiplib import Z, create_chip


ROOT = Path(__file__).resolve().parents[2]


def set_byte(chip, pins, value):
    for i, pin in enumerate(pins):
        chip.set_input(pin, (value >> i) & 1)


def get_byte(chip, pins):
    return sum((1 if chip.read(pin) == 1 else 0) << i for i, pin in enumerate(pins))


def eval_chip(chip):
    chip.update()
    chip.commit()


def run_verilog(module_file: str, testbench: str) -> str | None:
    iverilog = shutil.which("iverilog")
    vvp = shutil.which("vvp")
    if iverilog is None or vvp is None:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        tb = Path(tmp) / "tb_equivalence.v"
        out = Path(tmp) / "tb_equivalence.vvp"
        tb.write_text(testbench, encoding="utf-8")
        compiled = subprocess.run(
            [iverilog, "-g2012", "-Wall", "-o", str(out), str(ROOT / module_file), str(tb)],
            text=True,
            capture_output=True,
            check=False,
        )
        assert compiled.returncode == 0, compiled.stderr
        simulated = subprocess.run([vvp, str(out)], text=True, capture_output=True, check=False)
        assert simulated.returncode == 0, simulated.stderr
        return simulated.stdout


def result_int(output: str, key: str) -> int:
    match = re.search(rf"RESULT {key} ([0-9a-fA-FxzXZ]+)", output)
    assert match is not None, output
    text = match.group(1).lower()
    assert "x" not in text
    assert "z" not in text
    return int(text, 16)


def test_74hc00_python_matches_verilog_vectors():
    vectors = [(0, 0), (0, 1), (1, 0), (1, 1)]
    expected_bits = []
    for a, b in vectors:
        chip = create_chip("74HC00", "U")
        chip.set_input(1, a)
        chip.set_input(2, b)
        eval_chip(chip)
        expected_bits.append(chip.read(3))
    expected = sum(bit << i for i, bit in enumerate(expected_bits))

    output = run_verilog(
        "verilog/74xx/74hc00.v",
        """
`timescale 1ns/1ps
module tb;
  reg [3:0] a = 4'b1010;
  reg [3:0] b = 4'b1100;
  wire [3:0] y;
  ttl_74hc00 dut(.A(a), .B(b), .Y(y));
  initial begin #1; $display("RESULT NAND %h", y); $finish; end
endmodule
""",
    )
    if output is None:
        return
    assert result_int(output, "NAND") == expected


def test_74hc161_python_matches_verilog_count_sequence():
    chip = create_chip("74HC161", "U")
    for pin, value in [(1, 0), (9, 1), (7, 1), (10, 1)]:
        chip.set_input(pin, value)
    eval_chip(chip)
    chip.set_input(1, 1)
    for _ in range(3):
        chip.clock_edge()
        chip.commit()
    expected_q = get_byte(chip, [14, 13, 12, 11])
    expected_rco = chip.read(15)

    output = run_verilog(
        "verilog/74xx/74hc161.v",
        """
`timescale 1ns/1ps
module tb;
  reg clear_bar = 0;
  reg load_bar = 1;
  reg ent = 1;
  reg enp = 1;
  reg [3:0] d = 4'h0;
  reg clk = 0;
  wire rco;
  wire [3:0] q;
  ttl_74hc161 dut(.Clear_bar(clear_bar), .Load_bar(load_bar), .ENT(ent), .ENP(enp), .D(d), .Clk(clk), .RCO(rco), .Q(q));
  initial begin
    #1; clear_bar = 1; #1; clear_bar = 0; #1; clear_bar = 1;
    repeat (3) begin #1 clk = 1; #1 clk = 0; end
    #1; $display("RESULT COUNT %h", {rco, q}); $finish;
  end
endmodule
""",
    )
    if output is None:
        return
    assert result_int(output, "COUNT") == ((expected_rco << 4) | expected_q)


def test_74hc245_python_matches_verilog_a_to_b_and_high_z():
    chip = create_chip("74HC245", "U")
    set_byte(chip, [2, 3, 4, 5, 6, 7, 8, 9], 0x3C)
    chip.set_input(1, 1)
    chip.set_input(19, 0)
    eval_chip(chip)
    expected_b = get_byte(chip, [18, 17, 16, 15, 14, 13, 12, 11])
    chip.set_input(19, 1)
    eval_chip(chip)
    assert chip.read(18) == Z

    output = run_verilog(
        "verilog/74xx/74hc245.v",
        """
`timescale 1ns/1ps
module tb;
  reg oe_bar = 0;
  reg dir = 1;
  reg [7:0] a_drv = 8'h3c;
  reg drive_a = 1;
  wire [7:0] a;
  wire [7:0] b;
  assign a = drive_a ? a_drv : 8'hzz;
  ttl_74hc245 dut(.OE_bar(oe_bar), .DIR(dir), .A(a), .B(b));
  initial begin
    #1; $display("RESULT XCV %h", b);
    oe_bar = 1; drive_a = 0;
    #1; if (b !== 8'hzz) begin $display("FAIL high-z"); $finish(1); end
    $finish;
  end
endmodule
""",
    )
    if output is None:
        return
    assert result_int(output, "XCV") == expected_b


def run_all():
    test_74hc00_python_matches_verilog_vectors()
    test_74hc161_python_matches_verilog_count_sequence()
    test_74hc245_python_matches_verilog_a_to_b_and_high_z()


if __name__ == "__main__":
    run_all()
    print("Components equivalence tests passed")
