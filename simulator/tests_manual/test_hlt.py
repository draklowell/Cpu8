"""Test HLT timing"""

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

with open("../asm_toolchain/examples_asm/main.bin", "rb") as f:
    rom_data = f.read()

engine = SimulationEngine.load(MODULES, TABLES_PATH, rom_data)
component_pins = engine.get_component_pins()

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


# Run until we see halt
print("Full execution trace (showing PC and halt status):")
for cycle in range(70):
    chunk = step()
    pc = read_register(chunk, ["PC:U4", "PC:U5", "PC:U2", "PC:U3"], 16)
    instr = read_register(chunk, ["C1:INSTRUCTION1"], 8)
    mnem = MICROCODE.get(instr, "???")

    network = component_pins["I:PAD2"].get("N_HALT")
    halted = chunk.network_states[network] == State.LOW if network else False

    # Only print when near hlt or halted
    if pc >= 0x000B or halted:
        status = "HALTED!" if halted else ""
        print(
            f"Cycle {cycle:2}: PC=0x{pc:04X}, instr=0x{instr:02X} ({mnem:16}) {status}"
        )

    if halted:
        break
