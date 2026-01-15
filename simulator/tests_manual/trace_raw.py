#!/usr/bin/env python3
"""Compare raw simulation with debugger"""

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

with open("main.bin", "rb") as f:
    rom_data = f.read()

engine = SimulationEngine.load(MODULES, TABLES_PATH, rom_data)
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


print("Cycle | PC     | Instr Reg | AC   | Mnemonic")
print("-" * 60)

last_pc = -1
for cycle in range(40):
    chunk = step()
    pc = read_reg(chunk, ["PC:U4", "PC:U5", "PC:U2", "PC:U3"], 16)
    instr = read_reg(chunk, ["C1:INSTRUCTION1"], 8)
    xl = read_reg(chunk, ["REG:XL1"], 8)
    mnemonic = MICROCODE.get(instr, "UNK")

    if pc != last_pc:
        print(f"{cycle:5d} | 0x{pc:04X} | 0x{instr:02X}      | 0x{xl:02X} | {mnemonic}")
        last_pc = pc

    network = engine.get_component_pins()["I:PAD2"].get("N_HALT")
    if network and chunk.network_states[network] == State.LOW:
        print("\n=== HALTED ===")
        break
