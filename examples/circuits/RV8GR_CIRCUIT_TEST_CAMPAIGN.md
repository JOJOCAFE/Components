# RV8GR 22-Circuit Logical and Modeled-Timing Campaign

Generated deterministically by `tools/circuit_campaign_report.py`. Logical, direct live-model, and modeled-timing passes require fresh execution of named evidence. Blocked adapters remain visible and modeled timing never implies physical signoff.

Allowed outcomes: `pass`, `not_applicable`, `not_directly_executed`, and `physical_measurement_required`.

| Package | Logical | Direct live model | Composition/static | Modeled timing | Physical |
|---|---|---|---|---|---|
| RV8GR_RingCounter | pass | pass | pass | pass | physical_measurement_required |
| RV8GR_PC16 | pass | not_directly_executed | pass | not_directly_executed | physical_measurement_required |
| RV8GR_AddressMux16 | pass | not_directly_executed | pass | not_directly_executed | physical_measurement_required |
| RV8GR_BusOwnership | pass | not_directly_executed | pass | not_directly_executed | physical_measurement_required |
| RV8GR_InstructionLatch | pass | not_directly_executed | pass | not_directly_executed | physical_measurement_required |
| RV8GR_StorePath | pass | pass | pass | not_directly_executed | physical_measurement_required |
| RV8GR_DataPageMemory | pass | not_directly_executed | pass | not_directly_executed | physical_measurement_required |
| RV8GR_IRQLatch | pass | pass | pass | not_directly_executed | physical_measurement_required |
| RV8GR_RomDbusRead | pass | pass | pass | not_directly_executed | physical_measurement_required |
| RV8GR_AluAccumulator | pass | not_directly_executed | pass | not_directly_executed | physical_measurement_required |
| RV8GR_PageDataRegisters | pass | not_directly_executed | pass | not_directly_executed | physical_measurement_required |
| RV8GR_BranchJumpControl | pass | pass | pass | not_directly_executed | physical_measurement_required |
| RV8GR_VirtualTestHelpers | pass | pass | pass | not_applicable | not_applicable |
| RV8GR_FullControlOpcodeSweep | pass | not_directly_executed | pass | not_directly_executed | physical_measurement_required |
| RV8GR_ResetClockBringup | pass | pass | pass | not_directly_executed | physical_measurement_required |
| RV8GR_FetchCycleTrace | pass | not_directly_executed | pass | not_directly_executed | physical_measurement_required |
| RV8GR_StoreLoadBranchTrace | pass | not_directly_executed | pass | not_directly_executed | physical_measurement_required |
| RV8GR_PageJumpTrace | pass | not_directly_executed | pass | not_directly_executed | physical_measurement_required |
| RV8GR_InterruptTrace | pass | not_directly_executed | pass | not_directly_executed | physical_measurement_required |
| RV8GR_BootSequenceTrace | pass | not_directly_executed | pass | not_directly_executed | physical_measurement_required |
| RV8GR_Lab13MarkerTrace | pass | not_directly_executed | pass | not_directly_executed | physical_measurement_required |
| RV8GR_WholeSystemChipLevelVirtual | pass | not_directly_executed | pass | not_directly_executed | physical_measurement_required |

## Package Evidence

### RV8GR_RingCounter

- Stage: `clock_reset`
- Focus: T0/T1/T2 sequence, edge behavior, reset, lower-state recovery
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `pass` (runtime_package_proof_passed)
- Composition/static: `pass` (executable_static_package_check)
- Modeled timing: `pass` (runtime_package_timing_passed)
- Physical: `physical_measurement_required` (not_proven)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_RingCounter/circuit.json`, `examples/circuits/RV8GR_RingCounter/tests/ring_counter.json`, `python/tests/test_lib_circuits.py::test_rv8gr_ring_counter_sequence_and_reset`, `python/tests/test_lib_circuits.py::test_rv8gr_ring_counter_sequence_executes_with_component_models`, `python/tests/test_lib_circuits.py::test_rv8gr_ring_counter_package_shape`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[]`
- Timing blockers: `[]`
- Limitations: functional timing plus model slack Composition/static pass is package-shape validation, not composed-system execution. Physical stage 1 (clock_reset_ring_counter) remains an unmeasured capture contract.

### RV8GR_PC16

- Stage: `program_counter`
- Focus: count/load priority, carry chain, /PC_LD, PC_INC
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `not_directly_executed` (runtime_package_proof_blocked)
- Composition/static: `pass` (executable_static_package_check)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (not_proven)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_PC16/circuit.json`, `examples/circuits/RV8GR_PC16/tests/pc16.json`, `python/tests/test_lib_circuits.py::test_rv8gr_pc16_vectors_execute`, `python/tests/test_lib_circuits.py::test_rv8gr_pc16_vectors_execute_with_component_models`, `python/tests/test_lib_circuits.py::test_rv8gr_pc16_package_shape`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[{"code": "unresolved_output", "path": "$.ports[6].name", "message": "port 'PC0..PC15' has no concrete net"}]`
- Timing blockers: `[{"code": "functional_promotion_required", "path": "examples/circuits/RV8GR_PC16/circuit.json", "message": "package timing cannot pass before its live functional proof is promoted"}]`
- Limitations: functional timing plus model slack Direct live execution is blocked; see runtime_evidence.functional.blocks. Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Composition/static pass is package-shape validation, not composed-system execution. Physical stage 2 (program_counter_branch_jump) remains an unmeasured capture contract.

### RV8GR_AddressMux16

- Stage: `address_path`
- Focus: PC vs {DP,IRL} address selection, ADDR_REQ, and A15 decode
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `not_directly_executed` (runtime_package_proof_blocked)
- Composition/static: `pass` (executable_static_package_check)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (not_proven)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_AddressMux16/circuit.json`, `examples/circuits/RV8GR_AddressMux16/tests/address_mux16.json`, `python/tests/test_lib_circuits.py::test_rv8gr_address_mux16_vectors_execute`, `python/tests/test_lib_circuits.py::test_rv8gr_address_mux16_vectors_execute_with_component_models`, `python/tests/test_lib_circuits.py::test_rv8gr_address_mux16_package_shape`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[{"code": "unresolved_output", "path": "$.ports[6].name", "message": "port 'ABUS0..ABUS15' has no concrete net"}, {"code": "unresolved_output", "path": "$.ports[7].name", "message": "port 'A15' has no concrete net"}]`
- Timing blockers: `[{"code": "functional_promotion_required", "path": "examples/circuits/RV8GR_AddressMux16/circuit.json", "message": "package timing cannot pass before its live functional proof is promoted"}]`
- Limitations: functional select timing plus model slack Direct live execution is blocked; see runtime_evidence.functional.blocks. Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Composition/static pass is package-shape validation, not composed-system execution. Physical stage 3 (memory_buses_address_mux) remains an unmeasured capture contract.

### RV8GR_BusOwnership

- Stage: `bus_safety`
- Focus: T0/T1/T2 IBUS/DBUS drivers and bus-fight detection
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `not_directly_executed` (runtime_package_proof_blocked)
- Composition/static: `pass` (executable_static_package_check)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (blocked_missing_deadband)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_BusOwnership/circuit.json`, `examples/circuits/RV8GR_BusOwnership/tests/bus_ownership.json`, `python/tests/test_lib_circuits.py::test_rv8gr_bus_ownership_phase_vectors_are_conflict_free`, `python/tests/test_lib_circuits.py::test_rv8gr_bus_ownership_package_shape`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[{"code": "ambiguous_symbolic_width", "path": "$.wiring[0].connections[3]", "message": "symbolic endpoint 'IBUS0..IBUS7' has no concrete live chip instance"}]`
- Timing blockers: `[{"code": "functional_promotion_required", "path": "examples/circuits/RV8GR_BusOwnership/circuit.json", "message": "package timing cannot pass before its live functional proof is promoted"}]`
- Limitations: bus logic proven; physical overlap timing still requires scope/source evidence Direct live execution is blocked; see runtime_evidence.functional.blocks. Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Composition/static pass is package-shape validation, not composed-system execution. Physical stage 3 (memory_buses_address_mux) remains an unmeasured capture contract.

### RV8GR_InstructionLatch

- Stage: `fetch_decode`
- Focus: T0/T1 edge capture and T2 hold
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `not_directly_executed` (runtime_package_proof_blocked)
- Composition/static: `pass` (executable_static_package_check)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (not_proven)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_InstructionLatch/circuit.json`, `examples/circuits/RV8GR_InstructionLatch/tests/instruction_latch.json`, `python/tests/test_lib_circuits.py::test_rv8gr_instruction_latch_vectors_execute`, `python/tests/test_lib_circuits.py::test_rv8gr_instruction_latch_vectors_execute_with_component_models`, `python/tests/test_lib_circuits.py::test_rv8gr_instruction_latch_package_shape`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[{"code": "unresolved_output", "path": "$.ports[4].name", "message": "port 'IR_HIGH0..7' has no concrete net"}]`
- Timing blockers: `[{"code": "functional_promotion_required", "path": "examples/circuits/RV8GR_InstructionLatch/circuit.json", "message": "package timing cannot pass before its live functional proof is promoted"}]`
- Limitations: functional timing plus model slack; selected ROM grade required Direct live execution is blocked; see runtime_evidence.functional.blocks. Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Composition/static pass is package-shape validation, not composed-system execution. Physical stage 4 (instruction_alu_accumulator_zero) remains an unmeasured capture contract.

### RV8GR_StorePath

- Stage: `memory_write`
- Focus: IBUS to DBUS write direction and memory output disable
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `pass` (runtime_package_proof_passed)
- Composition/static: `pass` (executable_static_package_check)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (blocked_missing_memory_write_deadband)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_StorePath/circuit.json`, `examples/circuits/RV8GR_StorePath/tests/store_path.json`, `python/tests/test_lib_circuits.py::test_rv8gr_store_path_vectors_execute`, `python/tests/test_lib_circuits.py::test_rv8gr_store_path_package_shape`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[]`
- Timing blockers: `[{"code": "timing_execution_failed", "path": "examples/circuits/RV8GR_StorePath/circuit.json", "message": "no package-specific threshold-enforcing timing execution adapter"}]`
- Limitations: functional store timing plus model slack; selected SRAM/ROM output-disable timing required Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Composition/static pass is package-shape validation, not composed-system execution. Physical stage 3 (memory_buses_address_mux) remains an unmeasured capture contract.

### RV8GR_DataPageMemory

- Stage: `memory_page`
- Focus: SETDP, RAM read/write, ROM read via DP, and $7FFF/$8000 boundary
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `not_directly_executed` (runtime_package_proof_blocked)
- Composition/static: `pass` (executable_static_package_check)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (candidate_source_backed_not_measured)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_DataPageMemory/circuit.json`, `examples/circuits/RV8GR_DataPageMemory/tests/data_page_memory.json`, `python/tests/test_lib_circuits.py::test_rv8gr_data_page_memory_vectors_execute`, `python/tests/test_lib_circuits.py::test_rv8gr_data_page_setdp_executes_with_component_models`, `python/tests/test_lib_circuits.py::test_rv8gr_data_page_memory_package_shape`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[{"code": "unresolved_output", "path": "$.ports[7].name", "message": "port 'DP0..DP7' has no concrete net"}, {"code": "unresolved_output", "path": "$.ports[8].name", "message": "port 'ABUS0..ABUS15' has no concrete net"}]`
- Timing blockers: `[{"code": "functional_promotion_required", "path": "examples/circuits/RV8GR_DataPageMemory/circuit.json", "message": "package timing cannot pass before its live functional proof is promoted"}]`
- Limitations: functional timing plus source-backed SRAM options; installed SRAM marking and measured read/float timing required Direct live execution is blocked; see runtime_evidence.functional.blocks. Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Composition/static pass is package-shape validation, not composed-system execution. Physical stage 3 (memory_buses_address_mux) remains an unmeasured capture contract.

### RV8GR_IRQLatch

- Stage: `interrupt`
- Focus: IE set, /IRQ release latch, sticky IRQ_FF, no v1.0 vector
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `pass` (runtime_package_proof_passed)
- Composition/static: `pass` (executable_static_package_check)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (not_proven)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_IRQLatch/circuit.json`, `examples/circuits/RV8GR_IRQLatch/tests/irq_latch.json`, `python/tests/test_lib_circuits.py::test_rv8gr_irq_latch_vectors_execute`, `python/tests/test_lib_circuits.py::test_rv8gr_irq_latch_vectors_execute_with_component_model`, `python/tests/test_lib_circuits.py::test_rv8gr_irq_latch_package_shape`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[]`
- Timing blockers: `[{"code": "timing_execution_failed", "path": "examples/circuits/RV8GR_IRQLatch/circuit.json", "message": "no package-specific threshold-enforcing timing execution adapter"}]`
- Limitations: functional edge behavior only; external switch edge quality must be measured Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Composition/static pass is package-shape validation, not composed-system execution. Physical stage 6 (irq_and_rv8_bus) remains an unmeasured capture contract.

### RV8GR_RomDbusRead

- Stage: `memory_read`
- Focus: DBUS to IBUS read direction and ROM /OE safety
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `pass` (runtime_package_proof_passed)
- Composition/static: `pass` (executable_static_package_check)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (blocked_missing_deadband)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_RomDbusRead/circuit.json`, `examples/circuits/RV8GR_RomDbusRead/tests/rom_dbus_read.json`, `python/tests/test_lib_circuits.py::test_rv8gr_rom_dbus_read_vectors_execute`, `python/tests/test_lib_circuits.py::test_rv8gr_rom_dbus_read_executes_with_component_models`, `python/tests/test_lib_circuits.py::test_rv8gr_rom_dbus_read_package_shape`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[]`
- Timing blockers: `[{"code": "timing_execution_failed", "path": "examples/circuits/RV8GR_RomDbusRead/circuit.json", "message": "no package-specific threshold-enforcing timing execution adapter"}]`
- Limitations: functional read timing plus model slack; ROM output-float evidence required Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Composition/static pass is package-shape validation, not composed-system execution. Physical stage 3 (memory_buses_address_mux) remains an unmeasured capture contract.

### RV8GR_AluAccumulator

- Stage: `alu`
- Focus: ALU path timing, AC latch edge, Z flag settle
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `not_directly_executed` (runtime_package_proof_blocked)
- Composition/static: `pass` (executable_static_package_check)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (not_proven)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_AluAccumulator/circuit.json`, `examples/circuits/RV8GR_AluAccumulator/tests/alu_accumulator.json`, `python/tests/test_lib_circuits.py::test_rv8gr_alu_accumulator_vectors_execute`, `python/tests/test_lib_circuits.py::test_rv8gr_alu_adder_vectors_execute_with_component_models`, `python/tests/test_lib_circuits.py::test_rv8gr_alu_accumulator_package_shape`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[{"code": "proof_state_not_executable", "path": "examples/circuits/RV8GR_AluAccumulator/tests/alu_accumulator.json#$.vectors[3].start_ac", "message": "remaining independent vectors require loading accumulator state through a public API; CircuitRunner exposes no chip-state injection"}]`
- Timing blockers: `[{"code": "functional_promotion_required", "path": "examples/circuits/RV8GR_AluAccumulator/circuit.json", "message": "package timing cannot pass before its live functional proof is promoted"}]`
- Limitations: tightest listed model path; physical 5 MHz still not proven Direct live execution is blocked; see runtime_evidence.functional.blocks. Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Composition/static pass is package-shape validation, not composed-system execution. Physical stage 4 (instruction_alu_accumulator_zero) remains an unmeasured capture contract.

### RV8GR_PageDataRegisters

- Stage: `page_registers`
- Focus: PG_CLK and DP_Load edge timing
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `not_directly_executed` (runtime_package_proof_blocked)
- Composition/static: `pass` (executable_static_package_check)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (not_proven)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_PageDataRegisters/circuit.json`, `examples/circuits/RV8GR_PageDataRegisters/tests/page_data_registers.json`, `python/tests/test_lib_circuits.py::test_rv8gr_page_register_setpg_edge_vectors_execute`, `python/tests/test_lib_circuits.py::test_rv8gr_page_register_setpg_executes_with_component_model`, `python/tests/test_lib_circuits.py::test_rv8gr_page_data_registers_package_shape`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[{"code": "unresolved_output", "path": "$.ports[11].name", "message": "port 'PG0..PG7' has no concrete net"}, {"code": "unresolved_output", "path": "$.ports[12].name", "message": "port 'DP0..DP7' has no concrete net"}, {"code": "unresolved_output", "path": "$.ports[14].name", "message": "output 'PC_LOAD0..PC_LOAD15' has no concrete chip endpoint"}]`
- Timing blockers: `[{"code": "functional_promotion_required", "path": "examples/circuits/RV8GR_PageDataRegisters/circuit.json", "message": "package timing cannot pass before its live functional proof is promoted"}]`
- Limitations: functional timing plus model slack Direct live execution is blocked; see runtime_evidence.functional.blocks. Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Composition/static pass is package-shape validation, not composed-system execution. Physical stage 5 (page_store_load_full_system) remains an unmeasured capture contract.

### RV8GR_BranchJumpControl

- Stage: `branch_jump`
- Focus: /PC_LD, branch condition, no unintended load
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `pass` (runtime_package_proof_passed)
- Composition/static: `pass` (executable_static_package_check)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (not_proven)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_BranchJumpControl/circuit.json`, `examples/circuits/RV8GR_BranchJumpControl/tests/branch_jump_control.json`, `python/tests/test_lib_circuits.py::test_rv8gr_branch_jump_opcode_sweep_matches_verilog_bench_equation`, `python/tests/test_lib_circuits.py::test_rv8gr_branch_jump_control_package_shape`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[]`
- Timing blockers: `[{"code": "timing_execution_failed", "path": "examples/circuits/RV8GR_BranchJumpControl/circuit.json", "message": "no package-specific threshold-enforcing timing execution adapter"}]`
- Limitations: functional timing plus model slack Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Composition/static pass is package-shape validation, not composed-system execution. Physical stage 2 (program_counter_branch_jump) remains an unmeasured capture contract.

### RV8GR_VirtualTestHelpers

- Stage: `test_infrastructure`
- Focus: clock profiles, phase probes, bus contention observation, R/C estimates
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `pass` (runtime_package_proof_passed)
- Composition/static: `pass` (executable_static_package_check)
- Modeled timing: `not_applicable` (runtime_timing_not_applicable)
- Physical: `not_applicable` (not_applicable)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_VirtualTestHelpers/circuit.json`, `examples/circuits/RV8GR_VirtualTestHelpers/tests/virtual_test_helpers.json`, `python/tests/test_lib_circuits.py::test_rv8gr_virtual_clock_profiles_execute`, `python/tests/test_lib_circuits.py::test_rv8gr_virtual_test_helpers_package_shape`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[]`
- Timing blockers: `[]`
- Limitations: virtual observation helpers do not prove hardware timing Composition/static pass is package-shape validation, not composed-system execution. Virtual test infrastructure has no independent physical package to measure.

### RV8GR_FullControlOpcodeSweep

- Stage: `control_decode`
- Focus: all opcode/Z cases, reserved mixes, side-effect drift
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `not_directly_executed` (runtime_package_proof_blocked)
- Composition/static: `pass` (executable_static_package_check)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (not_proven)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_FullControlOpcodeSweep/circuit.json`, `examples/circuits/RV8GR_FullControlOpcodeSweep/tests/full_control_opcode_sweep.json`, `python/tests/test_lib_circuits.py::test_rv8gr_full_control_opcode_sweep_all_512_cases_match_verilog_equation`, `python/tests/test_lib_circuits.py::test_rv8gr_full_control_opcode_sweep_package_shape`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[{"code": "composite_not_executable", "path": "$.chips[0].part", "message": "nested circuit 'RV8GR_BusOwnership' is not executable"}, {"code": "composite_not_executable", "path": "$.chips[1].part", "message": "nested circuit 'RV8GR_AluAccumulator' is not executable"}, {"code": "composite_not_executable", "path": "$.chips[2].part", "message": "nested circuit 'RV8GR_PageDataRegisters' is not executable"}, {"code": "composite_not_executable", "path": "$.chips[3].part", "message": "nested circuit 'RV8GR_BranchJumpControl' is not executable"}, {"code": "composite_not_executable", "path": "$.chips[4].part", "message": "nested circuit 'RV8GR_VirtualTestHelpers' is not executable"}]`
- Timing blockers: `[{"code": "functional_promotion_required", "path": "examples/circuits/RV8GR_FullControlOpcodeSweep/circuit.json", "message": "package timing cannot pass before its live functional proof is promoted"}]`
- Limitations: control equations proven functionally; gate delay timing remains covered by specific paths Direct live execution is blocked; see runtime_evidence.functional.blocks. Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Composition/static pass is package-shape validation, not composed-system execution. No package-specific physical stage exists; shared board captures still gate physical claims.

### RV8GR_ResetClockBringup

- Stage: `bringup`
- Focus: reset idle/release, one-hot phase pushes, PC known-state policy, clock profiles
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `pass` (runtime_package_proof_passed)
- Composition/static: `pass` (executable_static_package_check)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (blocked_missing_clock_scope_capture)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_ResetClockBringup/circuit.json`, `examples/circuits/RV8GR_ResetClockBringup/tests/reset_clock_bringup.json`, `python/tests/test_lib_circuits.py::test_rv8gr_reset_clock_bringup_reset_idle_and_release`, `python/tests/test_lib_circuits.py::test_rv8gr_reset_clock_bringup_package_shape`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[]`
- Timing blockers: `[{"code": "timing_execution_failed", "path": "examples/circuits/RV8GR_ResetClockBringup/circuit.json", "message": "no package-specific threshold-enforcing timing execution adapter"}]`
- Limitations: functional reset/clock timing proven; physical edge quality requires scope evidence Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Composition/static pass is package-shape validation, not composed-system execution. Physical stage 1 (clock_reset_ring_counter) remains an unmeasured capture contract.

### RV8GR_FetchCycleTrace

- Stage: `instruction_trace`
- Focus: T0 control fetch, T1 operand fetch, T2 LI execute, PC motion, bus owners
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `not_directly_executed` (runtime_package_proof_blocked)
- Composition/static: `pass` (executable_composed_system_test)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (not_proven)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_FetchCycleTrace/circuit.json`, `examples/circuits/RV8GR_FetchCycleTrace/tests/fetch_cycle_trace.json`, `python/tests/test_lib_circuits.py::test_rv8gr_fetch_cycle_basic_fetch_matches_verilog_task`, `python/tests/test_lib_circuits.py::test_rv8gr_fetch_cycle_bus_driver_policy_is_conflict_free`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[{"code": "unresolved_output", "path": "$.ports[4].name", "message": "output 'PC0..PC15' has no concrete chip endpoint"}, {"code": "unresolved_output", "path": "$.ports[5].name", "message": "port 'ABUS0..ABUS15' has no concrete net"}, {"code": "unresolved_output", "path": "$.ports[8].name", "message": "port 'IRH0..IRH7' has no concrete net"}, {"code": "unresolved_output", "path": "$.ports[9].name", "message": "port 'IRL0..IRL7' has no concrete net"}, {"code": "unresolved_output", "path": "$.ports[10].name", "message": "port 'AC0..AC7' has no concrete net"}]`
- Timing blockers: `[{"code": "functional_promotion_required", "path": "examples/circuits/RV8GR_FetchCycleTrace/circuit.json", "message": "package timing cannot pass before its live functional proof is promoted"}]`
- Limitations: functional trace timing; physical memory/clock evidence covered by lower-level paths Direct live execution is blocked; see runtime_evidence.functional.blocks. Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. No package-specific physical stage exists; shared board captures still gate physical claims.

### RV8GR_StoreLoadBranchTrace

- Stage: `instruction_trace`
- Focus: SB RAM write, LB RAM read, BEQ PC load, bus owners, PC/AC/RAM state
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `not_directly_executed` (runtime_package_proof_blocked)
- Composition/static: `pass` (executable_composed_system_test)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (not_proven)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_StoreLoadBranchTrace/circuit.json`, `examples/circuits/RV8GR_StoreLoadBranchTrace/tests/store_load_branch_trace.json`, `python/tests/test_lib_circuits.py::test_rv8gr_store_load_branch_trace_vectors_execute`, `python/tests/test_lib_circuits.py::test_rv8gr_store_load_branch_trace_bus_policy_is_conflict_free`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[{"code": "composite_not_executable", "path": "$.chips[4].part", "message": "nested circuit 'RV8GR_BranchJumpControl' is not executable"}, {"code": "ambiguous_range_width", "path": "$.wiring[0]", "message": "vector net 'ABUS0..ABUS15' has 15 scalar endpoints; expected a multiple of width 16"}]`
- Timing blockers: `[{"code": "functional_promotion_required", "path": "examples/circuits/RV8GR_StoreLoadBranchTrace/circuit.json", "message": "package timing cannot pass before its live functional proof is promoted"}]`
- Limitations: functional trace timing; physical store/load deadband covered by lower-level paths Direct live execution is blocked; see runtime_evidence.functional.blocks. Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Physical stage 5 (page_store_load_full_system) remains an unmeasured capture contract.

### RV8GR_PageJumpTrace

- Stage: `instruction_trace`
- Focus: SETDP, SETPG, J, page-register state, PC page loading
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `not_directly_executed` (runtime_package_proof_blocked)
- Composition/static: `pass` (executable_composed_system_test)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (not_proven)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_PageJumpTrace/circuit.json`, `examples/circuits/RV8GR_PageJumpTrace/tests/page_jump_trace.json`, `python/tests/test_lib_circuits.py::test_rv8gr_page_jump_trace_vectors_execute`, `python/tests/test_lib_circuits.py::test_rv8gr_page_jump_trace_sequence_uses_latched_pg_for_jump`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[{"code": "composite_not_executable", "path": "$.chips[3].part", "message": "nested circuit 'RV8GR_BranchJumpControl' is not executable"}, {"code": "unresolved_output", "path": "$.ports[7].name", "message": "output '/PC_LD' has no concrete chip endpoint"}]`
- Timing blockers: `[{"code": "functional_promotion_required", "path": "examples/circuits/RV8GR_PageJumpTrace/circuit.json", "message": "package timing cannot pass before its live functional proof is promoted"}]`
- Limitations: functional trace timing; page-register setup covered by lower-level paths Direct live execution is blocked; see runtime_evidence.functional.blocks. Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Physical stage 5 (page_store_load_full_system) remains an unmeasured capture contract.

### RV8GR_InterruptTrace

- Stage: `instruction_trace`
- Focus: EI, DI inert behavior, /IRQ LOW hold, release latch, sticky IRQ_FF
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `not_directly_executed` (runtime_package_proof_blocked)
- Composition/static: `pass` (executable_composed_system_test)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (not_proven)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_InterruptTrace/circuit.json`, `examples/circuits/RV8GR_InterruptTrace/tests/interrupt_trace.json`, `python/tests/test_lib_circuits.py::test_rv8gr_interrupt_trace_vectors_execute`, `python/tests/test_lib_circuits.py::test_rv8gr_interrupt_trace_matches_full_control_ei_assumption`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[{"code": "unsupported_port_direction", "path": "$.ports[11].direction", "message": "direction 'power' is not executable"}]`
- Timing blockers: `[{"code": "functional_promotion_required", "path": "examples/circuits/RV8GR_InterruptTrace/circuit.json", "message": "package timing cannot pass before its live functional proof is promoted"}]`
- Limitations: functional trace timing; external IRQ edge quality requires measurement Direct live execution is blocked; see runtime_evidence.functional.blocks. Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Physical stage 6 (irq_and_rv8_bus) remains an unmeasured capture contract.

### RV8GR_BootSequenceTrace

- Stage: `instruction_trace`
- Focus: SETDP $80, SETPG $00, LI $00, J self, 12-clock manual bring-up
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `not_directly_executed` (runtime_package_proof_blocked)
- Composition/static: `pass` (executable_composed_system_test)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (not_proven)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_BootSequenceTrace/circuit.json`, `examples/circuits/RV8GR_BootSequenceTrace/tests/boot_sequence_trace.json`, `python/tests/test_lib_circuits.py::test_rv8gr_boot_sequence_trace_vectors_execute`, `python/tests/test_lib_circuits.py::test_rv8gr_boot_sequence_trace_ends_in_manual_loop_state`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[{"code": "composite_not_executable", "path": "$.chips[1].part", "message": "nested circuit 'RV8GR_AluAccumulator' is not executable"}]`
- Timing blockers: `[{"code": "functional_promotion_required", "path": "examples/circuits/RV8GR_BootSequenceTrace/circuit.json", "message": "package timing cannot pass before its live functional proof is promoted"}]`
- Limitations: functional boot trace only; physical single-step and edge evidence still required Direct live execution is blocked; see runtime_evidence.functional.blocks. Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Physical stage 5 (page_store_load_full_system) remains an unmeasured capture contract.

### RV8GR_Lab13MarkerTrace

- Stage: `instruction_trace`
- Focus: Lab 13 LI/ADDI/SUBI/BEQ flow, $AA marker, bus owners, final pass state
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `not_directly_executed` (runtime_package_proof_blocked)
- Composition/static: `pass` (executable_composed_system_test)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (not_proven)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_Lab13MarkerTrace/circuit.json`, `examples/circuits/RV8GR_Lab13MarkerTrace/tests/lab13_marker_trace.json`, `python/tests/test_lib_circuits.py::test_rv8gr_lab13_marker_trace_rom_and_rows_match_source_program`, `python/tests/test_lib_circuits.py::test_rv8gr_lab13_marker_trace_marker_flow_and_final_pass_state`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[{"code": "composite_not_executable", "path": "$.chips[4].part", "message": "nested circuit 'RV8GR_AluAccumulator' is not executable"}, {"code": "composite_not_executable", "path": "$.chips[5].part", "message": "nested circuit 'RV8GR_BranchJumpControl' is not executable"}, {"code": "ambiguous_range_width", "path": "$.wiring[0]", "message": "scalar net 'ROM_DBUS' cannot bind a multi-pin range"}, {"code": "unresolved_output", "path": "$.ports[13].name", "message": "output '/PC_LD' has no concrete chip endpoint"}, {"code": "unresolved_output", "path": "$.ports[14].name", "message": "output 'ACC_CLK' has no concrete chip endpoint"}]`
- Timing blockers: `[{"code": "functional_promotion_required", "path": "examples/circuits/RV8GR_Lab13MarkerTrace/circuit.json", "message": "package timing cannot pass before its live functional proof is promoted"}]`
- Limitations: functional Lab 13 marker trace only; physical single-step, oscillator, and bus-deadband evidence still required Direct live execution is blocked; see runtime_evidence.functional.blocks. Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. Physical stage 5 (page_store_load_full_system) remains an unmeasured capture contract.

### RV8GR_WholeSystemChipLevelVirtual

- Stage: `whole_system_virtual`
- Focus: chip bench plan, boot, Lab 13, RAM/page/IRQ/bus traces, R/C and delay-noise stress nets
- Logical: `pass` (named_logical_test_executed)
- Direct live model: `not_directly_executed` (runtime_package_proof_blocked)
- Composition/static: `pass` (executable_composed_system_test)
- Modeled timing: `not_directly_executed` (runtime_package_timing_blocked)
- Physical: `physical_measurement_required` (not_proven)
- Evidence: `examples/circuits/RV8GR_COVERAGE_INDEX.json`, `examples/circuits/RV8GR_WholeSystemChipLevelVirtual/circuit.json`, `examples/circuits/RV8GR_WholeSystemChipLevelVirtual/tests/whole_system_chip_level_virtual.json`, `python/tests/test_lib_circuits.py::test_rv8gr_whole_system_chip_level_virtual_includes_required_gates`, `python/tests/test_lib_circuits.py::test_rv8gr_whole_system_chip_level_virtual_catches_ai_fault_patterns`, `examples/circuits/timing_margins.json`, `examples/circuits/physical_capture_plan.json`, `examples/circuits/RV8GR_CIRCUIT_RUNTIME_EVIDENCE.json`
- Logical blockers: `[]`
- Functional blockers: `[{"code": "composite_not_executable", "path": "$.chips[0].part", "message": "nested circuit 'RV8GR_BootSequenceTrace' is not executable"}, {"code": "composite_not_executable", "path": "$.chips[1].part", "message": "nested circuit 'RV8GR_Lab13MarkerTrace' is not executable"}, {"code": "composite_not_executable", "path": "$.chips[2].part", "message": "nested circuit 'RV8GR_StoreLoadBranchTrace' is not executable"}, {"code": "composite_not_executable", "path": "$.chips[3].part", "message": "nested circuit 'RV8GR_PageJumpTrace' is not executable"}, {"code": "composite_not_executable", "path": "$.chips[4].part", "message": "nested circuit 'RV8GR_InterruptTrace' is not executable"}, {"code": "composite_not_executable", "path": "$.chips[5].part", "message": "nested circuit 'RV8GR_BusOwnership' is not executable"}, {"code": "unresolved_output", "path": "$.ports[4].name", "message": "port 'ABUS0..ABUS15' has no concrete net"}, {"code": "unresolved_output", "path": "$.ports[10].name", "message": "port 'RAM_/OE' has no concrete net"}, {"code": "unresolved_output", "path": "$.ports[11].name", "message": "port 'RAM_/WE' has no concrete net"}, {"code": "unresolved_output", "path": "$.ports[12].name", "message": "port 'ROM_/OE' has no concrete net"}]`
- Timing blockers: `[{"code": "functional_promotion_required", "path": "examples/circuits/RV8GR_WholeSystemChipLevelVirtual/circuit.json", "message": "package timing cannot pass before its live functional proof is promoted"}]`
- Limitations: virtual whole-system chip-level stress only; physical voltage/frequency/scope evidence still required Direct live execution is blocked; see runtime_evidence.functional.blocks. Package-level modeled timing is blocked; see runtime_evidence.timing.blocks. No package-specific physical stage exists; shared board captures still gate physical claims.
