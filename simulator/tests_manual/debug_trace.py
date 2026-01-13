"""
Debug trace for step_full_instruction
"""

from debug.base import DebuggerCore

d = DebuggerCore("../asm_toolchain/examples_asm/main.bin")
d.initialize()

print(f"Initial: PC=0x{d.state.pc:04X}, instr=0x{d.state.instruction:02X}")
print()

# Step through first instruction cycle by cycle
start_pc = d.state.pc
start_instr = d.state.instruction
_, instr_size, _ = d.disasm.disassemble_at(start_pc)
instr_end = start_pc + instr_size

print(f"Instruction at 0x{start_pc:04X}, size={instr_size}, ends at 0x{instr_end:04X}")
print(f"Expected next PC: 0x{instr_end:04X}, opcode there: 0x{d.rom[instr_end]:02X}")
print()

for i in range(50):
    d.step_instruction()
    pc = d.state.pc
    instr = d.state.instruction
    rom_at_pc = d.rom[pc] if pc < len(d.rom) else 0xFF

    match = "MATCH" if instr == rom_at_pc else ""
    outside = "OUTSIDE" if (pc < start_pc or pc >= instr_end) else ""

    # Check stability condition
    stable = outside and match
    marker = " <-- STABLE" if stable else ""

    print(
        f"Cycle {i+1:2}: PC=0x{pc:04X}, instr=0x{instr:02X}, rom[pc]=0x{rom_at_pc:02X} {match:5} {outside:7}{marker}"
    )
