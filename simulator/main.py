from simulator.simulation import LogLevel, SimulationEngine, State, WaveformChunk

CYCLES = 20
PERIOD = 10
INIT_TICKS = 20
TICKS = CYCLES * PERIOD * 2

MODULES = [
    ("netlists/alu_hub.frp", "ALU"),
    ("netlists/core_1.frp", "C1"),
    ("netlists/core_2.frp", "C2"),
    ("netlists/core_3.frp", "C3"),
    ("netlists/interface.frp", "I"),
    ("netlists/program_counter.frp", "PC"),
    ("netlists/register_file_accum.frp", "REG"),
    ("netlists/stack_pointer.frp", "SP"),
]

TABLES_PATH = "../microcode/bin"


def check_conflicts(chunk: WaveformChunk):
    for network, state in chunk.network_states.items():
        if state == State.CONFLICT:
            print(
                f"\033[33m[{network}] Conflict: {chunk.network_drivers[network]}\033[0m"
            )


def print_logs(chunk: WaveformChunk):
    for level, source, message in chunk.logs:
        if level == LogLevel.INFO:
            color = "\033[34m"
        elif level == LogLevel.OK:
            color = "\033[32m"
        elif level == LogLevel.WARNING:
            color = "\033[33m"
        elif level == LogLevel.ERROR:
            color = "\033[31m"
        else:
            color = "\033[0m"

        print(f"{color}[{source}] {message}\033[0m")


def print_state(chunk: WaveformChunk):
    state = ""
    for i in range(17):
        name = f"C3:/STATE{i}!"
        state_val = chunk.network_states[name]
        if state_val == State.HIGH:
            state += "1"
        elif state_val == State.LOW:
            state += "0"
        elif state_val == State.FLOATING:
            state += "Z"
        elif state_val == State.CONFLICT:
            state += "X"

    print("IISSSSFFFRRRRRRRR")
    print(state[::-1])  # Reverse for display


def print_internal_io(chunk: WaveformChunk):
    read = 0
    load = 0
    for i in range(5):
        name = f"C1:/L{i}!"
        state_val = chunk.network_states[name]
        if state_val == State.HIGH:
            load |= 1 << i
        elif state_val != State.LOW:
            print(f"\033[33m[{name}] Unexpected floating state\033[0m")

        name = f"C1:/R{i}!"
        state_val = chunk.network_states[name]
        if state_val == State.HIGH:
            read |= 1 << i
        elif state_val != State.LOW:
            print(f"\033[33m[{name}] Unexpected floating state\033[0m")
    print(f"{load:02x} <- {read:02x}")


def main():
    with open("main.bin", "rb") as f:
        rom_data = f.read()

    engine = SimulationEngine.load(MODULES, TABLES_PATH, rom_data)

    pin_aliases = engine.get_component_pin_aliases()
    pin_networks = engine.get_component_pin_networks()

    engine.set_power(True)
    engine.set_reset(True)
    engine.set_wait(False)

    for cycle in range(INIT_TICKS):
        chunk = engine.tick()

    engine.set_reset(False)

    for component, aliases in pin_aliases.items():
        for pin, alias in aliases:
            if alias != "VCC":
                continue

            network = pin_networks[component][pin]
            network_state = chunk.network_states[network]
            if network_state != State.HIGH:
                print(f"\033[31m[{component}] Power not connected on pin {pin}\033[0m")
            else:
                print(f"\033[32m[{component}] Power connected on pin {pin}\033[0m")
            break
        else:
            print(f"[{component}] No VCC pin to check")

    clock = False
    for cycle in range(TICKS):
        chunk = engine.tick()

        print_logs(chunk)
        check_conflicts(chunk)
        if cycle % PERIOD == 0:
            print_internal_io(chunk)
            print_state(chunk)
            for i in range(4):
                result = 0
                for j in range(16):
                    for pin, name in pin_aliases[f"C1:DECODER{i+1}"]:
                        if name == f"Y{j}":
                            network = pin_networks[f"C1:DECODER{i+1}"].get(pin)
                            break
                    else:
                        raise ValueError(f"Pin Y{j} not found on DECODER{i+1}")

                    if network is None:
                        continue

                    if chunk.network_states[network] == State.HIGH:
                        result |= 1 << j

                print(f"DECODER{i+1}: {result:016b}")

            if clock:
                print(f"--- Cycle {cycle // PERIOD // 2}")
            clock = not clock
            engine.set_clock(clock)


if __name__ == "__main__":
    main()
