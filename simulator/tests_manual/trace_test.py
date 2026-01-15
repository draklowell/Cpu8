"""
Test script to trace PC through instruction execution
"""

from config import (
    INIT_TICKS,
    MODULES,
    PERIOD,
    STARTUP_TICKS,
    TABLES_PATH,
    load_microcode_data,
)
from simulator.simulation import SimulationEngine, State

READERS, WRITERS, MICROCODE = load_microcode_data()

# Load our test ROM
with open("../asm_toolchain/examples_asm/main.bin", "rb") as f:
    rom_data = f.read()

engine = SimulationEngine.load(MODULES, TABLES_PATH, rom_data)
component_pins = engine.get_component_pins()

# Initialize
engine.set_power(True)
engine.set_component_variable("I:PAD2", "RESET", 1)
engine.set_component_variable("I:PAD2", "WAIT", 0)

for _ in range(INIT_TICKS):
    chunk = engine.tick()

engine.set_component_variable("I:PAD2", "RESET", 0)

for _ in range(STARTUP_TICKS):
    chunk = engine.tick()


def read_register(chunk, registers, size):
    result = 0
    size_per_register = size // len(registers)
    for i, comp in enumerate(registers):
        result |= (chunk.variables[comp]["Q"]) << (i * size_per_register)
    return result


def step():
    engine.set_component_variable("I:PAD2", "CLOCK", 0)
    for _ in range(PERIOD // 2):
        engine.tick()
    chunk = engine.tick()
    engine.set_component_variable("I:PAD2", "CLOCK", 1)
    for _ in range(PERIOD // 2):
        chunk = engine.tick()
    return chunk


# Disassembly for reference
print("=== ROM Disassembly ===")
print("0x0000: 14 FF FE    ldi-sp-0xFFFE")
print("0x0003: 04 00 0F    ld-ac-0x000F")
print("0x0006: 10 00 10    ld-zh-0x0010")
print("0x0009: 7D 00 0D    call-0x000D")
print("0x000C: DD          hlt")
print("0x000D: 8A          add-zh")
print("0x000E: 84          ret")
print()

# Execute and trace - show EVERY cycle during call
print("=== Execution Trace ===")
print("Cycle | PC     | Instruction | Mnemonic         | Status")
print("-" * 70)

for cycle in range(80):
    chunk = step()
    pc = read_register(chunk, ["PC:U4", "PC:U5", "PC:U2", "PC:U3"], 16)
    instr = read_register(chunk, ["C1:INSTRUCTION1"], 8)
    mnem = MICROCODE.get(instr, "???")

    network = component_pins["I:PAD2"].get("N_HALT")
    halted = chunk.network_states[network] == State.LOW if network else False

    status = "HALT!" if halted else ""
    # Print ALL cycles to see the pattern
    print(f"{cycle:5} | 0x{pc:04X} | 0x{instr:02X}        | {mnem:16} | {status}")

    if halted:
        break
