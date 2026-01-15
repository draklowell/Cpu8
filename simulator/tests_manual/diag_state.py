#!/usr/bin/env python3
"""Deep diagnosis of STATE lines"""
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

# Same test program
rom = bytearray(256)
rom[0] = 0x03  # ldi-ac-[byte]
rom[1] = 0x0A  # = 10
rom[2] = 0xDA  # cmpi-[byte]
rom[3] = 0x05  # compare with 5
rom[4] = 0x6B  # jz-[word]
rom[5] = 0x00  # high
rom[6] = 0x0B  # low = 0x0B
rom[7] = 0x00  # nop
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

# Print all component names containing TABLE or FLAG or STATE
print("=== Component names ===")
all_pins = engine.get_component_pins()
for name in sorted(all_pins.keys()):
    if "TABLE" in name.upper() or "FLAG" in name.upper():
        print(f"  {name}")

# Find TABLE1
for name in all_pins.keys():
    if "TABLE1" in name:
        print(f"\n=== {name} pins ===")
        for pin, net in sorted(all_pins[name].items(), key=lambda x: str(x[0])):
            print(f"  pin {pin}: network {net}")
        break
