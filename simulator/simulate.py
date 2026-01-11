from config import (
    CYCLES,
    INIT_TICKS,
    MODULES,
    PERIOD,
    STARTUP_TICKS,
    TABLES_PATH,
    load_microcode_data,
)
from simulator.simulation import LogLevel, SimulationEngine, State, WaveformChunk

READERS, WRITERS, MICROCODE = load_microcode_data()


class Simulator:
    simulation_engine: SimulationEngine
    period: int

    def __init__(self, simulation_engine: SimulationEngine, period: int):
        self.simulation_engine = simulation_engine
        self.period = period
        self._component_pins = simulation_engine.get_component_pins()

    @property
    def component_pins(self):
        return self._component_pins

    def check_conflicts(self, chunk: WaveformChunk):
        for network, state in chunk.network_states.items():
            if state == State.CONFLICT:
                self.log(
                    LogLevel.ERROR,
                    network,
                    f"Conflict: {chunk.network_drivers[network]}",
                )

    def log(self, level: LogLevel, source: str, message: str, tick: int | None = None):
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

        if tick is None:
            print(f"{color}[{source}] {message}\033[0m")
        else:
            print(f"{color}[{tick}][{source}] {message}\033[0m")

    def start(self, ticks_init: int, ticks_startup: int):
        self.simulation_engine.set_power(True)
        self.simulation_engine.set_component_variable("I:PAD2", "RESET", 1)
        self.simulation_engine.set_component_variable("I:PAD2", "WAIT", 0)

        for _ in range(ticks_init):
            chunk = self.tick(verbose=False)

        for component, pins in self._component_pins.items():
            if "VCC" not in pins:
                print(f"[{component}] No VCC pin to check")
                continue

            network_state = chunk.network_states[pins["VCC"]]
            if network_state != State.HIGH:
                self.log(LogLevel.ERROR, component, "Power not connected on pin VCC")
            else:
                self.log(LogLevel.OK, component, "Power connected on pin VCC")

        self.simulation_engine.set_component_variable("I:PAD2", "RESET", 0)

        for _ in range(ticks_startup):
            chunk = self.tick()

        return chunk

    def tick(self, verbose: bool = True):
        chunk = self.simulation_engine.tick()

        for level, source, message in chunk.logs:
            self.log(level, source, message, tick=chunk.tick)

        if verbose:
            self.check_conflicts(chunk)

        return chunk

    def step(self):
        self.simulation_engine.set_component_variable("I:PAD2", "CLOCK", 0)
        for _ in range(self.period // 2):
            c = self.tick(False)
            # print(f"STATE: NNSSSSFFFIIIIIIII [{c.tick}]")
            # print_bus(self, c, "STATE", "C3:/STATE", 17)
        chunk = self.tick()
        self.simulation_engine.set_component_variable("I:PAD2", "CLOCK", 1)
        for _ in range(self.period // 2):
            c = self.tick(False)
            # print(f"STATE: NNSSSSFFFIIIIIIII [{c.tick}]")
            # print_bus(self, c, "STATE", "C3:/STATE", 17)
        return chunk


def print_component(simulator: Simulator, chunk: WaveformChunk, component_name: str):
    pins = simulator.component_pins.get(component_name)
    if pins is None:
        return

    print(f"{component_name}:")

    for pin, network in pins.items():
        state = chunk.network_states[network]
        print(f"  - {pin} ({network}): {state}")


def print_bus(
    simulator: Simulator, chunk: WaveformChunk, name: str, network_name: str, size: int
):
    value = 0
    for i in range(size):
        network = f"{network_name}{i}!"
        if chunk.network_states[network] == State.HIGH:
            value |= 1 << i
        elif chunk.network_states[network] != State.LOW:
            simulator.log(LogLevel.WARNING, network, "Unexpected floating state")

    print(f"{name}: {value:0{size}b} ({value:#0{size//4+2}x})")


def read_register(
    simulator: Simulator,
    chunk: WaveformChunk,
    registers: list[str],
    size: int,
) -> int:
    if size % len(registers) != 0:
        raise ValueError("Size must be divisible by number of registers")

    result = 0
    size_per_register = size // len(registers)
    for i, comp in enumerate(registers):
        result |= (chunk.variables[comp]["Q"]) << (i * size_per_register)

    return result


def print_load_read(simulator: Simulator, chunk: WaveformChunk):
    load = 0
    read = 0
    for i in range(5):
        network = f"C1:/L{i}!"
        if chunk.network_states[network] == State.HIGH:
            if i != 4:
                load |= 1 << i
        elif chunk.network_states[network] != State.LOW:
            simulator.log(LogLevel.WARNING, network, "Unexpected floating state")
        elif i == 4:
            load |= 1 << i  # L4 is active low

        network = f"C1:/R{i}!"
        if chunk.network_states[network] == State.HIGH:
            if i != 4:
                read |= 1 << i
        elif chunk.network_states[network] != State.LOW:
            simulator.log(LogLevel.WARNING, network, "Unexpected floating state")
        elif i == 4:
            read |= 1 << i  # R4 is active low

    reader = READERS.get(load, "Unknown")
    writer = WRITERS.get(read, "Unknown")
    print(
        f"LOAD: {load:05b} ({load:#04x}/{reader}) <- READ: {read:05b} ({read:#04x}/{writer})"
    )


def print_interface_pins(simulator: Simulator, chunk: WaveformChunk):
    print("INTERFACE:")
    for pin, network in simulator.component_pins["I:PAD2"].items():
        if pin.startswith("ADDRESS") or pin.startswith("DATA"):
            continue

        state = chunk.network_states[network]
        print(f"  - {pin} ({network}): {state}")


def print_control_bus(simulator: Simulator, chunk: WaveformChunk):
    print("CONTROL BUS:")
    for idx in range(4):
        if idx == 3:
            table = "C2:TABLE7"
        else:
            table = f"C3:TABLE{idx*2 + 1}"

        for bit in range(8):
            network = simulator.component_pins[table].get(f"D{bit}")
            if network is None:
                continue

            state = chunk.network_states[network]
            print(f"  - CTL{idx * 8 + bit:02} ({network}): {state}")


def print_decoders(simulator: Simulator, chunk: WaveformChunk):
    for i in range(4):
        print(f"DECODER{i+1}:")
        pinout = simulator.component_pins[f"C1:DECODER{i+1}"]

        for j in range(4):
            network = pinout.get(f"A{j}")
            if network is None:
                print(f"  - A{j} not connected")
                continue

            if chunk.network_states[network] == State.HIGH:
                print(f"  - A{j} ({network}) is HIGH")
            else:
                print(f"  - A{j} ({network}) is LOW")

        for j in range(2):
            network = pinout.get(f"N_E{j}")
            if network is None:
                print(f"  - N_E{j} not connected")
                continue

            if chunk.network_states[network] == State.HIGH:
                print(f"  - N_E{j} ({network}) is HIGH")
            else:
                print(f"  - N_E{j} ({network}) is LOW")

        for j in range(16):
            network = pinout.get(f"Y{j}")
            if network is None:
                print(f"  - Y{j} not connected")
                continue

            if chunk.network_states[network] == State.HIGH:
                print(f"  - Y{j} ({network}) is HIGH")
            else:
                print(f"  - Y{j} ({network}) is LOW")


def print_register(
    simulator: Simulator,
    chunk: WaveformChunk,
    name: str,
    registers: list[str],
    size: int,
):
    result = read_register(simulator, chunk, registers, size)
    print(f"{name}: {result} ({result:#0{size//4+2}x})")


def process(cycle: int, simulator: Simulator, chunk: WaveformChunk):
    print(f"\033[53m>>>>>>>> Cycle {cycle} <<<<<<<<\033[0m")
    print("STATE: NNSSSSFFFIIIIIIII")
    print_bus(simulator, chunk, "STATE", "C3:/STATE", 17)
    print_bus(simulator, chunk, "INTERFACE DATA", "I:/DATA", 8)
    print_bus(simulator, chunk, "DATA", "PC:/DATA", 8)
    print_register(
        simulator,
        chunk,
        "PROGRAM COUNTER",
        [
            "PC:U4",
            "PC:U5",
            "PC:U2",
            "PC:U3",
        ],
        16,
    )
    print_register(
        simulator,
        chunk,
        "ADDRESS",
        [
            "I:U8",
            "I:U7",
            "I:U6",
            "I:U5",
        ],
        16,
    )
    print_register(
        simulator,
        chunk,
        "STACK POINTER",
        [
            "SP:U4",
            "SP:U5",
            "SP:U2",
            "SP:U3",
        ],
        16,
    )
    instruction = read_register(
        simulator,
        chunk,
        ["C1:INSTRUCTION1"],
        8,
    )
    mnemonic = MICROCODE.get(instruction, "UNKNOWN")
    print(f"INSTRUCTION: {instruction:08b} ({instruction:#04x}/{mnemonic})")

    for reg in ["ZH", "ZL", "YH", "YL", "XH", "XL"]:
        print_register(
            simulator,
            chunk,
            f"REGISTER {reg}",
            [f"REG:{reg}1"],
            8,
        )
    print_load_read(simulator, chunk)
    # print_interface_pins(simulator, chunk)
    # print_control_bus(simulator, chunk)
    # print_decoders(simulator, chunk)


def main():
    with open("all.bin", "rb") as f:
        rom_data = f.read()

    engine = SimulationEngine.load(MODULES, TABLES_PATH, rom_data)

    simulator = Simulator(engine, PERIOD)
    simulator.start(INIT_TICKS, STARTUP_TICKS)

    for cycle in range(CYCLES):
        chunk = simulator.step()
        process(cycle, simulator, chunk)

        network = simulator.component_pins["I:PAD2"].get("N_HALT")
        if network is None:
            raise RuntimeError("No N_HALT pin on I:PAD2")
        if chunk.network_states[network] == State.LOW:
            print("\033[33mCPU HALTED\033[0m")
            break


if __name__ == "__main__":
    main()
