from loader import load
from motherboard import Motherboard
from simulator.base import NetworkState

CYCLES = 20
PERIOD = 10
INIT_TICKS = 20
TICKS = CYCLES * PERIOD * 2


def check_conflicts(motherboard: Motherboard):
    for network in motherboard.cpu.networks.values():
        if network.state == NetworkState.CONFLICT:
            network.error(f"Conflict: {network.drivers}")


def print_state(motherboard: Motherboard):
    state = ""
    for i in range(17):
        name = f"C3:/STATE{i}!"
        network = motherboard.cpu.networks[name]
        if network.state == NetworkState.DRIVEN_HIGH:
            state += "1"
        elif network.state == NetworkState.DRIVEN_LOW:
            state += "0"
        elif network.state == NetworkState.FLOATING:
            state += "Z"
        elif network.state == NetworkState.CONFLICT:
            state += "X"

    print("IISSSSFFFRRRRRRRR")
    print(state[::-1])  # Reverse for display


def print_internal_io(motherboard: Motherboard):
    read = 0
    load = 0
    for i in range(5):
        name = f"C1:/L{i}!"
        network = motherboard.cpu.networks[name]
        if network.state == NetworkState.DRIVEN_HIGH:
            load |= 1 << i
        elif network.state != NetworkState.DRIVEN_LOW:
            network.warn("Unexpected floating state")

        name = f"C1:/R{i}!"
        network = motherboard.cpu.networks[name]
        if network.state == NetworkState.DRIVEN_HIGH:
            read |= 1 << i
        elif network.state != NetworkState.DRIVEN_LOW:
            network.warn("Unexpected floating state")

    print(f"{load:02x} <- {read:02x}")


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

    for component in motherboard.cpu.components.values():
        if hasattr(component, "VCC"):
            if not component.get(component.VCC):
                component.error(f"Power not connected")
            else:
                component.ok("Power connected")
        else:
            component.log("No VCC pin to check")

    motherboard.log(f"Starting simulation for {TICKS // PERIOD // 2} cycles")
    clock = False
    for cycle in range(TICKS):
        if cycle % PERIOD == 0:
            print_internal_io(motherboard)
            print_state(motherboard)
            # print(motherboard.cpu.networks["C1:/~{MemoryWriter}!"])
            # print(motherboard.cpu.networks["C1:/~{MemoryReader}!"])
            for i in range(4):
                decoder = motherboard.cpu.components[f"C1:DECODER{i+1}"]
                result = 0
                for j in range(16):
                    val = decoder.get(getattr(decoder, f"Y{j}"))
                    if val:
                        result |= 1 << j

                print(f"DECODER{i+1}: {result:016b}")

            if clock:
                print(f"--- Cycle {cycle // PERIOD // 2}")
            clock = not clock
            motherboard.cpu.interface.set_clock(clock)

        motherboard.propagate()
        check_conflicts(motherboard)
        # print(motherboard.cpu.networks["C3:/STATE0!"].state)

    motherboard.log("Simulation finished")


if __name__ == "__main__":
    main()
