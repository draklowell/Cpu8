from simulator.simulation import LogLevel, SimulationEngine, State, WaveformChunk

CYCLES = 4
PERIOD = 400
INIT_TICKS = 200
STARTUP_TICKS = 200

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

    def log(self, level: LogLevel, source: str, message: str):
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

    # def print_bus(self, chunk: WaveformChunk, bus_name: str, width: int):
    #     value = 0
    #     for i in range(width):
    #         name = f"{bus_name}{i}!"
    #         state_val = chunk.network_states[name]
    #         if state_val == State.HIGH:
    #             value |= 1 << i
    #         elif state_val != State.LOW:
    #             self.log(LogLevel.WARNING, name, "Unexpected floating state")
    #     print(f">>> Bus {bus_name}: {value:0{width}b} ({value:#0{width//4+2}x})")

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
            self.log(level, source, message)

        if verbose:
            self.check_conflicts(chunk)

        return chunk

    def step(self):
        self.simulation_engine.set_component_variable("I:PAD2", "CLOCK", 0)
        for _ in range(self.period // 2):
            self.tick(False)
        chunk = self.tick()
        self.simulation_engine.set_component_variable("I:PAD2", "CLOCK", 1)
        for _ in range(self.period // 2):
            self.tick(False)
        return chunk


def process(cycle: int, simulator: Simulator, chunk: WaveformChunk):
    print(f"\033[53m>>>>>>>> Cycle {cycle} <<<<<<<<\033[0m")
    state = 0
    for i in range(17):
        network = f"C3:/STATE{i}!"
        if chunk.network_states[network] == State.HIGH:
            state |= 1 << i
        elif chunk.network_states[network] != State.LOW:
            simulator.log(LogLevel.WARNING, network, "Unexpected floating state")
    print(f"STATE: {state:017b} ({state&0xffff:#06x})")

    data = 0
    for i in range(8):
        network = f"I:/DATA{i}!"
        # network = f"PC:/DATA{i}!"
        if chunk.network_states[network] == State.HIGH:
            data |= 1 << i
        elif chunk.network_states[network] != State.LOW:
            simulator.log(LogLevel.WARNING, network, "Unexpected floating state")
    print(f"DATA: {data:08b} ({data:#04x})")

    result = 0
    for i, comp in enumerate(
        [
            "PC:U4",
            "PC:U5",
            "PC:U2",
            "PC:U3",
        ]
    ):
        result |= (chunk.variables[comp]["Q"]) << (i * 4)
    print(f"PC: {result} ({result:#06x})")

    result = 0
    for i, comp in enumerate(
        [
            "I:U8",
            "I:U7",
            "I:U6",
            "I:U5",
        ]
    ):
        result |= (chunk.variables[comp]["Q"]) << (i * 4)
    print(f"ADDR: {result} ({result:#06x})")

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

    print(f"LOAD: {load:05b} ({load:#04x}) <- READ: {read:05b} ({read:#04x})")

    # for i in range(4):
    #     print(f"  DECODER{i+1}:")
    #     pinout = simulator.component_pins[f"C1:DECODER{i+1}"]

    #     for j in range(4):
    #         network = pinout.get(f"A{j}")
    #         if network is None:
    #             print(f"  - A{j} not connected")
    #             continue

    #         if chunk.network_states[network] == State.HIGH:
    #             print(f"  - A{j} ({network}) is HIGH")
    #         else:
    #             print(f"  - A{j} ({network}) is LOW")

    #     for j in range(2):
    #         network = pinout.get(f"N_E{j}")
    #         if network is None:
    #             print(f"  - N_E{j} not connected")
    #             continue

    #         if chunk.network_states[network] == State.HIGH:
    #             print(f"  - N_E{j} ({network}) is HIGH")
    #         else:
    #             print(f"  - N_E{j} ({network}) is LOW")

    #     for j in range(16):
    #         network = pinout.get(f"Y{j}")
    #         if network is None:
    #             print(f"  - Y{j} not connected")
    #             continue

    #         if chunk.network_states[network] == State.HIGH:
    #             print(f"  - Y{j} ({network}) is HIGH")
    #         else:
    #             print(f"  - Y{j} ({network}) is LOW")


def main():
    with open("main.bin", "rb") as f:
        rom_data = f.read()

    engine = SimulationEngine.load(MODULES, TABLES_PATH, rom_data)

    simulator = Simulator(engine, PERIOD)
    process(0, simulator, simulator.start(INIT_TICKS, STARTUP_TICKS))

    for cycle in range(CYCLES):
        process(cycle + 1, simulator, simulator.step())


if __name__ == "__main__":
    main()
