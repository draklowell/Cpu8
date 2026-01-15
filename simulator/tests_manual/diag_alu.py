#!/usr/bin/env python3
"""Deep ALU diagnosis"""
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

# Test program
rom = bytearray(256)
rom[0] = 0x03  # ldi-ac-[byte]
rom[1] = 0x0A  # = 10
rom[2] = 0xDA  # cmpi-[byte]
rom[3] = 0x05  # compare with 5
rom[4] = 0x6B  # jz-[word]
rom[5] = 0x00
rom[6] = 0x0B
rom[10] = 0xDD  # hlt
rom[11] = 0xDD  # hlt

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


print("Diagnosing ALU operation during cmpi\n")

for cycle in range(25):
    chunk = step()
    pc = read_reg(chunk, ["PC:U4", "PC:U5", "PC:U2", "PC:U3"], 16)
    instr = read_reg(chunk, ["C1:INSTRUCTION1"], 8)
    ac = read_reg(chunk, ["REG:XL1"], 8)
    mnemonic = MICROCODE.get(instr, "UNK")

    # Read ALU inputs and outputs
    # U4 (low nibble) and U5 (high nibble)
    try:
        # ALU outputs F0-F3 from U4
        f0 = chunk.network_states.get("ALU:Net-(U4-F0)!", None)
        f1 = chunk.network_states.get("ALU:Net-(U4-F1)!", None)
        f2 = chunk.network_states.get("ALU:Net-(U4-F2)!", None)
        f3 = chunk.network_states.get("ALU:Net-(U4-F3)!", None)

        # ALU outputs F4-F7 from U5
        f4 = chunk.network_states.get("ALU:Net-(U5-F0)!", None)
        f5 = chunk.network_states.get("ALU:Net-(U5-F1)!", None)
        f6 = chunk.network_states.get("ALU:Net-(U5-F2)!", None)

        alu_low = (
            (1 if f0 == State.HIGH else 0)
            | ((1 if f1 == State.HIGH else 0) << 1)
            | ((1 if f2 == State.HIGH else 0) << 2)
            | ((1 if f3 == State.HIGH else 0) << 3)
        )
        alu_high = (
            (1 if f4 == State.HIGH else 0)
            | ((1 if f5 == State.HIGH else 0) << 1)
            | ((1 if f6 == State.HIGH else 0) << 2)
        )

        # STATE10 (zero flag to microcode ROM)
        s10 = chunk.network_states.get("C3:/STATE10!", None)
        z = "Z=1" if s10 == State.HIGH else "Z=0"

        # ALUZO (zero output from ALU)
        aluzo = chunk.network_states.get("ALU:Net-(BC1-ALUZO)!", None)
        zo = "ZO=1" if aluzo == State.HIGH else "ZO=0"

    except Exception as e:
        alu_low = -1
        alu_high = -1
        z = "?"
        zo = "?"
        print(f"Error: {e}")

    print(
        f"{cycle:2d} | PC=0x{pc:04X} | AC=0x{ac:02X} | ALU=0x{alu_high:01X}{alu_low:01X} | {z} | {zo} | {mnemonic}"
    )

    # Stop after jz
    if instr == 0xDD:
        break
