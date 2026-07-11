#!/usr/bin/env python3
"""Add source-backed timing evidence extracted from local datasheet PDFs.

This intentionally records only values that were visible in local PDF text.
It does not replace conservative simulator timing; the audit report keeps those
defaults visible as mixed timing until public timing is separately normalized.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


UPDATES: dict[str, dict[str, Any]] = {
    "74HC02": {
        "conditions": "TI SN74HC02 switching characteristics, CL=50 pF, VCC=4.5 V, commercial SN74HC02.",
        "datasheet_typical_ns": {"input_to_output": 9, "transition": 8},
        "datasheet_max_ns_25c": {"input_to_output": 18, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"input_to_output": 23, "transition": 19},
    },
    "74HC03": {
        "conditions": "TI SN74HC03 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"tplh_input_to_output": 13, "tphl_input_to_output": 10, "transition": 8},
        "datasheet_max_ns_25c": {"tplh_input_to_output": 25, "tphl_input_to_output": 20, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"tplh_input_to_output": 31, "tphl_input_to_output": 25, "transition": 19},
    },
    "74HC05": {
        "conditions": "TI SN74HC05 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"tplh_input_to_output": 13, "tphl_input_to_output": 9, "transition": 8},
        "datasheet_max_ns_25c": {"tplh_input_to_output": 23, "tphl_input_to_output": 17, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"tplh_input_to_output": 29, "tphl_input_to_output": 21, "transition": 19},
        "datasheet_max_ns_minus55_to_125c": {"tplh_input_to_output": 35, "tphl_input_to_output": 26, "transition": 22},
    },
    "74HC07": {
        "conditions": "ST M74HC07 feature summary, VCC=6 V.",
        "datasheet_typical_ns": {"feature_tpd": 6},
    },
    "74HC08": {
        "conditions": "TI SN74HC08 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"input_to_output": 10, "transition": 8},
        "datasheet_max_ns_25c": {"input_to_output": 20, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"input_to_output": 25, "transition": 19},
        "datasheet_max_ns_minus55_to_125c": {"input_to_output": 30, "transition": 22},
    },
    "74HC11": {
        "conditions": "NXP 74HC11 dynamic characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"input_to_output": 12, "transition": 7},
        "datasheet_max_ns_25c": {"input_to_output": 20, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"input_to_output": 25, "transition": 19},
        "datasheet_max_ns_minus40_to_125c": {"input_to_output": 30, "transition": 22},
    },
    "74HC132": {
        "conditions": "TI SN74HC132 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"input_to_output": 18, "transition": 8},
        "datasheet_max_ns_minus40_to_85c": {"input_to_output": 31, "transition": 19},
        "datasheet_max_ns_minus55_to_125c": {"input_to_output": 37, "transition": 22},
    },
    "74HC14": {
        "conditions": "TI SN74HC14 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"input_to_output": 12, "transition": 8},
        "datasheet_max_ns_25c": {"input_to_output": 25, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"input_to_output": 31, "transition": 19},
        "datasheet_max_ns_minus55_to_125c": {"input_to_output": 38, "transition": 22},
    },
    "74HC147": {
        "conditions": "TI CD74HC147 feature summary, VCC=5 V, CL=15 pF, TA=25 C.",
        "datasheet_typical_ns": {"feature_tpd": 13},
    },
    "74HC148": {
        "conditions": "ST M74HC148 feature summary, VCC=5 V.",
        "datasheet_typical_ns": {"feature_tpd": 15},
    },
    "74HC154": {
        "conditions": "NXP 74HC154 dynamic characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"address_to_output": 13, "enable_to_output": 14, "transition": 7},
        "datasheet_max_ns_25c": {"address_to_output": 30, "enable_to_output": 30, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"address_to_output": 38, "enable_to_output": 38, "transition": 19},
        "datasheet_max_ns_minus40_to_125c": {"address_to_output": 45, "enable_to_output": 45, "transition": 22},
    },
    "74HC155": {
        "conditions": "ST M74HC155 feature summary, VCC=5 V.",
        "datasheet_typical_ns": {"feature_tpd": 12},
    },
    "74HC158": {
        "conditions": "TI SN74HC158 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"input_to_output": 18, "transition": 8},
        "datasheet_max_ns_25c": {"input_to_output": 25, "transition": 12},
        "datasheet_max_ns_minus40_to_85c": {"input_to_output": 31, "transition": 15},
    },
    "74HC160": {
        "conditions": "Renesas HD74HC160 switching characteristics, VCC=2 V, CL=50 pF.",
        "datasheet_max_ns_25c": {"clock_to_q": 160, "clear_to_q": 225, "enable_t_to_ripple_carry": 150, "clock_to_ripple_carry": 200, "output_rise_fall": 75},
        "datasheet_max_ns_minus40_to_85c": {"clock_to_q": 200, "clear_to_q": 280, "enable_t_to_ripple_carry": 190, "clock_to_ripple_carry": 250, "output_rise_fall": 95},
        "datasheet_min_ns_25c": {"setup_data_load_clear_to_clock": 125, "removal_clear_to_clock": 100, "pulse_width": 80},
        "datasheet_min_ns_minus40_to_85c": {"setup_data_load_clear_to_clock": 156, "removal_clear_to_clock": 125, "pulse_width": 100},
    },
    "74HC162": {
        "conditions": "Philips 74HC162 dynamic characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"clock_to_q": 21, "clock_to_terminal_count": 25, "cet_to_terminal_count": 14, "transition": 7},
        "datasheet_max_ns_25c": {"clock_to_q": 38, "clock_to_terminal_count": 43, "cet_to_terminal_count": 30, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"clock_to_q": 48, "clock_to_terminal_count": 54, "cet_to_terminal_count": 38, "transition": 19},
        "datasheet_max_ns_minus40_to_125c": {"clock_to_q": 57, "clock_to_terminal_count": 65, "cet_to_terminal_count": 45, "transition": 22},
        "datasheet_fmax_mhz": {"typical": 57, "min_25c": 30, "min_85c": 24, "min_125c": 20},
    },
    "74HC163": {
        "conditions": "TI SN74HC163 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"clock_to_q": 25, "transition": 8},
        "datasheet_max_ns_25c": {"clock_to_q": 41, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"clock_to_q": 51, "transition": 19},
        "datasheet_max_ns_minus55_to_125c": {"clock_to_q": 62, "transition": 22},
        "datasheet_fmax_mhz": {"typical": 40, "min_25c": 31, "min_85c": 25, "min_125c": 21},
    },
    "74HC165": {
        "conditions": "TI SN74HC165 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"shift_load_to_q": 20, "clock_to_q": 15, "h_to_q": 15},
        "datasheet_max_ns_25c": {"shift_load_to_q": 30, "clock_to_q": 30, "h_to_q": 30},
        "datasheet_fmax_mhz": {"typical": 50, "min_25c": 31, "sn54_min": 21, "sn74_min": 25},
    },
    "74HC166": {
        "conditions": "TI SN74HC166 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"clear_to_q": 18, "clock_to_q": 15, "transition": 8},
        "datasheet_max_ns_25c": {"clear_to_q": 24, "clock_to_q": 30, "transition": 15},
        "datasheet_max_ns_minus40_to_125c": {"clear_to_q": 36, "clock_to_q": 45, "transition": 22},
        "datasheet_fmax_mhz": {"typical": 31, "sn54_min": 21, "sn74_min": 21},
    },
    "74HC193": {
        "conditions": "TI SN74HC193 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"up_to_co": 24, "down_to_bo": 24, "count_to_q": 40, "load_to_q": 40, "clear_to_q": 36, "transition": 8},
        "datasheet_max_ns_25c": {"up_to_co": 33, "down_to_bo": 33, "count_to_q": 50, "load_to_q": 52, "clear_to_q": 48, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"up_to_co": 41, "down_to_bo": 41, "count_to_q": 63, "load_to_q": 65, "clear_to_q": 60, "transition": 19},
        "datasheet_max_ns_minus55_to_125c": {"up_to_co": 50, "down_to_bo": 50, "count_to_q": 75, "load_to_q": 78, "clear_to_q": 72, "transition": 22},
        "datasheet_fmax_mhz": {"typical": 55, "min_25c": 21, "sn74_min": 17, "sn54_min": 14},
    },
    "74HC20": {
        "conditions": "TI SN74HC20 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"input_to_output": 14, "transition": 9},
        "datasheet_max_ns_25c": {"input_to_output": 22, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"input_to_output": 28, "transition": 19},
        "datasheet_max_ns_minus55_to_125c": {"input_to_output": 33, "transition": 22},
    },
    "74HC238": {
        "conditions": "NXP 74HC238 dynamic characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"address_to_output": 17, "e3_to_output": 19, "enable_to_output": 18, "transition": 7},
        "datasheet_max_ns_25c": {"address_to_output": 30, "e3_to_output": 32, "enable_to_output": 31, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"address_to_output": 38, "e3_to_output": 40, "enable_to_output": 39, "transition": 19},
        "datasheet_max_ns_minus40_to_125c": {"address_to_output": 45, "e3_to_output": 48, "enable_to_output": 47, "transition": 22},
    },
    "74HC240": {
        "conditions": "TI SN74HC240 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"input_to_output": 10, "enable": 15, "disable": 22},
        "datasheet_max_ns_25c": {"input_to_output": 20, "enable": 30, "disable": 30},
        "datasheet_max_ns_minus40_to_85c": {"input_to_output": 25, "enable": 38, "disable": 38},
        "datasheet_max_ns_minus55_to_125c": {"input_to_output": 30, "enable": 45, "disable": 45},
    },
    "74HC244": {
        "conditions": "TI SN74HC244 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"input_to_output": 13},
        "datasheet_max_ns_25c": {"input_to_output": 23},
        "datasheet_max_ns_minus40_to_85c": {"input_to_output": 29},
        "datasheet_max_ns_minus40_to_125c": {"input_to_output": 34},
    },
    "74HC251": {
        "conditions": "TI SN74HC251 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"enable": 10, "disable": 15, "transition": 8},
        "datasheet_max_ns_25c": {"enable": 29, "disable": 39, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"enable": 36, "disable": 49, "transition": 19},
        "datasheet_max_ns_minus55_to_125c": {"enable": 42, "disable": 57, "transition": 22},
    },
    "74HC257": {
        "conditions": "TI SN74HC257 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"enable": 15, "disable": 15, "transition": 8},
        "datasheet_max_ns_25c": {"enable": 30, "disable": 30, "transition": 12},
        "datasheet_max_ns_minus40_to_85c": {"enable": 38, "disable": 38, "transition": 15},
        "datasheet_max_ns_minus55_to_125c": {"enable": 45, "disable": 45, "transition": 18},
    },
    "74HC266": {
        "conditions": "TI CD74HC266 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"tplh_input_to_output": 13, "tphl_input_to_output": 13},
        "datasheet_max_ns_25c": {"tplh_input_to_output": 25, "tphl_input_to_output": 20},
        "datasheet_max_ns_minus40_to_85c": {"tplh_input_to_output": 31, "tphl_input_to_output": 25},
    },
    "74HC27": {
        "conditions": "NXP 74HC27 dynamic characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"input_to_output": 10, "transition": 7},
        "datasheet_max_ns_25c": {"input_to_output": 18, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"input_to_output": 23, "transition": 19},
        "datasheet_max_ns_minus40_to_125c": {"input_to_output": 27, "transition": 22},
    },
    "74HC273": {
        "conditions": "TI SN74HC273 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_max_ns_minus40_to_85c": {"clear_to_q": 40, "clock_to_q": 40, "transition": 19},
        "datasheet_fmax_mhz": {"sn74_min": 21},
    },
    "74HC30": {
        "conditions": "TI CD74HC30 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"input_to_output": 9},
        "datasheet_max_ns_25c": {"input_to_output": 18},
        "datasheet_max_ns_minus40_to_85c": {"input_to_output": 23},
        "datasheet_max_ns_minus40_to_125c": {"input_to_output": 27},
    },
    "74HC352": {
        "conditions": "ST M74HC352 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"transition": 8, "path_1": 14, "path_2": 20, "path_3": 10, "path_4": 16, "path_5": 21},
        "datasheet_max_ns_25c": {"transition": 15, "path_1": 23, "path_2": 30, "path_3": 17, "path_4": 25, "path_5": 30},
        "datasheet_max_ns_minus40_to_85c": {"transition": 19, "path_1": 29, "path_2": 38, "path_3": 21, "path_4": 31, "path_5": 38},
        "datasheet_max_ns_minus55_to_125c": {"transition": 22, "path_1": 35, "path_2": 45, "path_3": 26, "path_4": 38, "path_5": 45},
    },
    "74HC374": {
        "conditions": "TI SN74HC374 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"clock_to_q": 17, "enable": 16, "disable": 17, "transition": 8},
        "datasheet_max_ns_25c": {"clock_to_q": 36, "enable": 30, "disable": 30, "transition": 12},
        "datasheet_max_ns_minus40_to_85c": {"clock_to_q": 45, "enable": 38, "disable": 38, "transition": 15},
        "datasheet_max_ns_minus55_to_125c": {"clock_to_q": 54, "enable": 45, "disable": 45, "transition": 18},
        "datasheet_fmax_mhz": {"typical": 60, "min_25c": 30, "sn74_min": 24, "sn54_min": 20},
    },
    "74HC377": {
        "conditions": "TI SN74HC377 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"clock_to_q": 15, "transition": 8},
        "datasheet_max_ns_25c": {"clock_to_q": 32, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"clock_to_q": 40, "transition": 19},
        "datasheet_max_ns_minus55_to_125c": {"clock_to_q": 48, "transition": 22},
        "datasheet_fmax_mhz": {"typical": 54, "min_25c": 25, "sn74_min": 20, "sn54_min": 16},
    },
    "74HC4049": {
        "conditions": "TI CD74HC4049 feature summary, VCC=5 V, CL=15 pF, TA=25 C.",
        "datasheet_typical_ns": {"feature_tpd": 6},
    },
    "74HC4050": {
        "conditions": "TI CD74HC4050 feature summary, VCC=5 V, CL=15 pF, TA=25 C.",
        "datasheet_typical_ns": {"feature_tpd": 6},
    },
    "74HC4078": {
        "conditions": "ST M74HC4078 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"input_to_output": 12, "transition": 8},
        "datasheet_max_ns_25c": {"input_to_output": 19, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"input_to_output": 24, "transition": 19},
        "datasheet_max_ns_minus55_to_125c": {"input_to_output": 29, "transition": 22},
    },
    "74HC4520": {
        "conditions": "TI CD74HC4520 prerequisite timing, VCC=4.5 V.",
        "datasheet_fmax_mhz": {"min_25c": 30, "min_85c": 24, "min_125c": 20},
        "datasheet_min_ns_25c": {"clock_pulse_width": 16, "reset_pulse_width": 20},
        "datasheet_min_ns_minus40_to_85c": {"clock_pulse_width": 20, "reset_pulse_width": 25},
        "datasheet_min_ns_minus55_to_125c": {"clock_pulse_width": 24, "reset_pulse_width": 30},
    },
    "74HC4538": {
        "conditions": "TI CD74HC4538 prerequisite pulse timing, VCC=4.5 V.",
        "datasheet_min_ns_25c": {"input_pulse_width": 16, "reset_low_width": 16},
        "datasheet_min_ns_minus40_to_85c": {"input_pulse_width": 20, "reset_low_width": 20},
        "datasheet_min_ns_minus55_to_125c": {"input_pulse_width": 24, "reset_low_width": 24},
    },
    "74HC593": {
        "conditions": "ST M54HC593 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"rco_transition": 8, "q_transition": 7, "propagation_path_a": 27, "propagation_path_b": 28},
        "datasheet_max_ns_25c": {"rco_transition": 15, "q_transition": 12, "propagation_path_a": 42, "propagation_path_b": 44},
        "datasheet_max_ns_minus40_to_85c": {"rco_transition": 19, "q_transition": 15, "propagation_path_a": 53, "propagation_path_b": 55},
        "datasheet_max_ns_minus55_to_125c": {"rco_transition": 22, "q_transition": 18, "propagation_path_a": 63, "propagation_path_b": 66},
    },
    "74HC595": {
        "conditions": "TI SN74HC595 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"srclr_to_qh": 18, "output_enable": 15},
        "datasheet_max_ns_25c": {"srclr_to_qh": 35, "output_enable": 30},
        "datasheet_max_ns_minus40_to_85c": {"srclr_to_qh": 44, "output_enable": 37},
        "datasheet_max_ns_minus55_to_125c": {"srclr_to_qh": 52, "output_enable": 45},
        "datasheet_fmax_mhz": {"typical": 38, "min_25c": 31, "sn74_min": 25, "sn54_min": 21},
    },
    "74HC85": {
        "conditions": "Motorola MC74HC85 maximum propagation delays, CL=50 pF, VCC=4.5 V.",
        "datasheet_max_ns_25c": {"a_or_b_to_greater_or_less": 46, "a_or_b_to_equal": 40, "cascade_to_greater_or_less": 35, "equal_input_to_equal_output": 29, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"a_or_b_to_greater_or_less": 58, "a_or_b_to_equal": 50, "cascade_to_greater_or_less": 44, "equal_input_to_equal_output": 36, "transition": 19},
        "datasheet_max_ns_minus55_to_125c": {"a_or_b_to_greater_or_less": 69, "a_or_b_to_equal": 60, "cascade_to_greater_or_less": 53, "equal_input_to_equal_output": 44, "transition": 22},
    },
    "74HC922": {
        "conditions": "MM74C922 timing characteristics, VCC=5 V.",
        "datasheet_typical_ns": {"data_available_to_output": 60, "output_to_high_z": 80, "high_z_to_output": 100},
        "datasheet_max_ns": {"data_available_to_output": 150, "output_to_high_z": 200, "high_z_to_output": 250},
    },
    "74HCT04": {
        "conditions": "TI SN74HCT04 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"input_to_output": 14, "transition": 9},
        "datasheet_max_ns_25c": {"input_to_output": 20, "transition": 15},
        "datasheet_max_ns_minus40_to_85c": {"input_to_output": 25, "transition": 19},
        "datasheet_max_ns_minus55_to_125c": {"input_to_output": 30, "transition": 22},
    },
    "74HCT14": {
        "conditions": "TI SN74HCT14 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"input_to_output": 20},
        "datasheet_max_ns_25c": {"input_to_output": 32},
        "datasheet_max_ns_minus40_to_85c": {"input_to_output": 40},
        "datasheet_max_ns_minus55_to_125c": {"input_to_output": 48},
    },
    "74HCT245": {
        "conditions": "TI SN74HCT245 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"input_to_output": 14},
        "datasheet_max_ns_25c": {"input_to_output": 20},
        "datasheet_max_ns_minus40_to_85c": {"input_to_output": 28},
        "datasheet_max_ns_minus55_to_125c": {"input_to_output": 33},
    },
    "74HCT541": {
        "conditions": "TI SN74HCT541 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_typical_ns": {"input_to_output": 13},
        "datasheet_max_ns_25c": {"input_to_output": 23},
        "datasheet_max_ns_minus40_to_85c": {"input_to_output": 29},
        "datasheet_max_ns_minus55_to_125c": {"input_to_output": 34},
    },
    "74HCT574": {
        "conditions": "TI SN74HCT574 switching characteristics, CL=50 pF, VCC=4.5 V.",
        "datasheet_fmax_mhz": {"typical": 36, "min_25c": 30, "sn74_min": 24, "sn54_min": 20},
        "datasheet_typical_ns": {"clock_to_q": 30, "enable": 26},
        "datasheet_max_ns_25c": {"clock_to_q": 36, "enable": 30},
        "datasheet_max_ns_minus40_to_85c": {"clock_to_q": 45, "enable": 38},
        "datasheet_max_ns_minus55_to_125c": {"clock_to_q": 54, "enable": 45},
    },
    "CY7C199": {
        "conditions": "Cypress CY7C199 switching characteristics, -20/-25/-35/-45 speed grades.",
        "datasheet_read_cycle_ns": {"speed_20": 20, "speed_25": 25, "speed_35": 35, "speed_45": 45},
        "datasheet_address_access_max_ns": {"speed_20": 20, "speed_25": 25, "speed_35": 35, "speed_45": 45},
        "datasheet_oe_access_max_ns": {"speed_20": 9, "speed_25": 10, "speed_35": 16, "speed_45": 16},
        "datasheet_high_z_max_ns": {"speed_20": 9, "speed_25": 11, "speed_35": 15, "speed_45": 15},
        "datasheet_write_cycle_ns": {"speed_20": 20, "speed_25": 25, "speed_35": 35, "speed_45": 45},
        "datasheet_write_pulse_min_ns": {"speed_20": 15, "speed_25": 18, "speed_35": 22, "speed_45": 22},
        "datasheet_data_setup_min_ns": {"speed_20": 10, "speed_25": 10, "speed_35": 15, "speed_45": 15},
        "datasheet_hold_min_ns": {"address_hold": 0, "data_hold": 0},
    },
}


def definition_paths() -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for definition in sorted((ROOT / "lib" / "standard").glob("*/**/definition/definition.json")):
        data = json.loads(definition.read_text(encoding="utf-8"))
        part = str(data.get("part") or definition.parents[1].name)
        paths[part] = definition
    return paths


def main() -> int:
    paths = definition_paths()
    missing = sorted(set(UPDATES) - set(paths))
    if missing:
        raise SystemExit(f"Missing definition(s): {', '.join(missing)}")

    for part, update in sorted(UPDATES.items()):
        path = paths[part]
        data = json.loads(path.read_text(encoding="utf-8"))
        layers = data.setdefault("definition_layers", {})
        timing = layers.setdefault(
            "timing",
            {
                "schema": "db.component.timing",
                "version": 1,
                "part": part,
                "delay": {},
            },
        )
        delay = timing.setdefault("delay", {})
        delay["status"] = "datasheet-backed"
        delay["source_check"] = "datasheet timing values extracted from local source PDF text; see docs/TIMING_CROSSCHECK_REPORT.md"
        delay["conditions"] = update["conditions"]
        for key, value in update.items():
            if key != "conditions":
                delay[key] = value
        timing.setdefault("evidence", first_evidence(data))

        top = data.setdefault("timing", {})
        top["datasheet"] = {
            "status": "datasheet-backed",
            "conditions": update["conditions"],
            "values": {k: v for k, v in update.items() if k != "conditions"},
        }

        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    print(f"updated {len(UPDATES)} timing definition(s)")
    return 0


def first_evidence(data: dict[str, Any]) -> dict[str, Any]:
    for entry in (data.get("datasheet") or {}).get("sources") or []:
        if isinstance(entry, dict):
            return entry
    for entry in data.get("sources") or []:
        if isinstance(entry, dict):
            return entry
    return {"label": "local source PDF", "used_for": ["timing"]}


if __name__ == "__main__":
    raise SystemExit(main())
