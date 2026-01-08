import os

from loader import load
from motherboard import Motherboard

CYCLES = 2
PERIOD = 10
INIT_TICKS = 20
TICKS = CYCLES * PERIOD * 2


def main():
    cpu = load()
    motherboard = Motherboard(cpu)

    with open("main.bin", "rb") as f:
        rom_data = f.read()

    motherboard.set_rom(rom_data)
    motherboard.cpu.backplane.power_on()
    motherboard.cpu.interface.set_reset(False)
    motherboard.cpu.interface.set_wait(False)

    for cycle in range(INIT_TICKS):
        motherboard.propagate()

    for module_name, module_dot in motherboard.export().items():
        with open(f"output_{module_name}.gv", "w") as f:
            f.write(module_dot)

    # motherboard.log(f"Starting simulation for {TICKS // PERIOD // 2} cycles")
    # clock = False
    # for cycle in range(TICKS):
    #     if cycle % PERIOD == 0:
    #         clock = not clock
    #         motherboard.cpu.interface.set_clock(clock)

    #     motherboard.propagate()
    # motherboard.log("Simulation finished")


if __name__ == "__main__":
    main()
