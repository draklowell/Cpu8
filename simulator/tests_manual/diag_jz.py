#!/usr/bin/env python3
"""Diagnose JZ instruction - check zero flag propagation"""
import sys

sys.path.insert(0, "/Users/nikitalenyk/Desktop/Cpu8/simulator")

from config import (
    INIT_TICKS,
    MODULES,
    PERIOD,
    STARTUP_TICKS,
    TABLES_PATH,
    load_microcode_data,
)

from simulator.simulation import SimulationEngine, State

READERS, WRITERS, MICROCODE, CYCLES = load_microcode_data()

# Simple test program:
# 0000: ldi-ac-[byte] 0x0A    ; AC = 10 (non-zero)
# 0002: cmpi-[byte] 0x05      ; compare AC with 5, should set Z=0 (10 != 5)
# 0004: jz-[word] 0x000B      ; should NOT jump (Z=0)
# 0007: nop
# 0008: nop
# 0009: nop
# 000A: hlt                   ; correct end - JZ did not jump
# 000B: hlt                   ; wrong end - JZ jumped incorrectly
rom = bytearray(256)
rom[0] = 0x03  # ldi-ac-[byte] (opcode 0x03)
rom[1] = 0x0A  # immediate = 10
rom[2] = 0xDA  # cmpi-[byte] (opcode 0xDA)
rom[3] = 0x05  # compare with 5
rom[4] = 0x6B  # jz-[word] (opcode 0x6B)
rom[5] = 0x00  # addr high = 0x00
rom[6] = 0x0B  # addr low = 0x0B  -> target = 0x000B
rom[7] = 0x00  # nop
rom[8] = 0x00  # nop
rom[9] = 0x00  # nop
rom[10] = 0xDD  # hlt (opcode 0xDD) - correct end
rom[11] = 0xDD  # hlt - wrong end if JZ jumped incorrectly

engine = SimulationEngine.load(MODULES, TABLES_PATH, bytes(rom))
engine.set_power(True)
engine.set_component_variable("I:PAD2", "RESET", 1)
engine.set_component_variable("I:PAD2", "WAIT", 0)

for _ in range(INIT_TICKS):
    engine.tick()
engine.set_component_variable("I:PAD2", "RESET", 0)
for _ in range(STARTUP_TICKS):
    engine.tick()


def step():
    engine.set_component_variable("I:PAD2", "CLOCK", 0)
    for _ in range(PERIOD // 2):
        engine.tick()
    engine.tick()
    engine.set_component_variable("I:PAD2", "CLOCK", 1)
    for _ in range(PERIOD // 2):
        chunk = engine.tick()
    return chunk


def read_reg(chunk, regs, size):
    result = 0
    for i, comp in enumerate(regs):
        result |= chunk.variables[comp]["Q"] << (i * (size // len(regs)))
    return result


print("Diagnosing JZ instruction with non-zero AC\n")
print("Cyc | PC     | Instr | AC   | ZeroOut | Mnemonic")
print("-" * 60)

for cycle in range(50):
    chunk = step()
    pc = read_reg(chunk, ["PC:U4", "PC:U5", "PC:U2", "PC:U3"], 16)
    instr = read_reg(chunk, ["C1:INSTRUCTION1"], 8)
    ac = read_reg(chunk, ["REG:XL1"], 8)
    mnemonic = MICROCODE.get(instr, "UNK")

    # Read STATE10 (zero flag input to microcode ROM)
    try:
        s10_net = "C3:/STATE10!"
        s10_state = chunk.network_states.get(s10_net, None)
        if s10_state == State.HIGH:
            zero_str = "Z=1"
        elif s10_state == State.LOW:
            zero_str = "Z=0"
        else:
            zero_str = f"{s10_state}"
    except Exception as e:
        zero_str = f"err"

    print(
        f"{cycle:3d} | 0x{pc:04X} | 0x{instr:02X}  | 0x{ac:02X} | {zero_str} | {mnemonic}"
    )

    # Check for halt
    try:
        network = engine.get_component_pins()["I:PAD2"].get("N_HALT")
        if network and chunk.network_states[network] == State.LOW:
            print(f"\n=== HALTED at PC=0x{pc:04X} ===")
            if pc == 0x000A:
                print("SUCCESS: JZ did NOT jump (correct behavior)")
            elif pc == 0x000B:
                print("FAILURE: JZ jumped when it should not have!")
            break
    except:
        pass
