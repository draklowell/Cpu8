import datetime

from vcd import VCDWriter
from vcd.writer import Variable

from config import CYCLES, INIT_TICKS, MODULES, PERIOD, STARTUP_TICKS, TABLES_PATH
from simulate import Simulator
from simulator.simulation import LogLevel, SimulationEngine, State, WaveformChunk

STATE_MAPPING = {
    State.CONFLICT: "x",
    State.FLOATING: "z",
    State.HIGH: 1,
    State.LOW: 0,
}


class SimulatorVCD(Simulator):
    _writer: VCDWriter
    _network_variables: dict[str, Variable]
    _component_variables: dict[str, dict[str, Variable]]

    def __init__(
        self, simulation_engine: SimulationEngine, period: int, writer: VCDWriter
    ):
        super().__init__(simulation_engine, period)
        self._writer = writer

        self._network_variables = {}
        for component, pins in self._component_pins.items():
            for pin, network in pins.items():
                if network in self._network_variables:
                    self._writer.register_alias(
                        component,
                        pin,
                        self._network_variables[network],
                    )
                else:
                    self._network_variables[network] = self._writer.register_var(
                        component,
                        pin,
                        "wire",
                        size=1,
                    )

        self._component_variables = {}
        for (
            component,
            variables,
        ) in self.simulation_engine.get_component_variable_sizes().items():
            self._component_variables[component] = {}
            for variable, size in variables.items():
                if size is None:
                    self._component_variables[component][variable] = None
                else:
                    self._component_variables[component][variable] = (
                        self._writer.register_var(
                            component,
                            variable,
                            "logic",
                            size=size,
                        )
                    )

    def tick(self, verbose: bool = True):
        chunk = self.simulation_engine.tick()

        for level, source, message in chunk.logs:
            self.log(level, source, message, tick=chunk.tick)

        for network, state in chunk.network_states.items():
            if network not in self._network_variables:
                self.log(
                    LogLevel.ERROR,
                    network,
                    "No associated variable in VCDWriter",
                    chunk.tick,
                )
                continue

            state_vcd = STATE_MAPPING[state]
            if self._network_variables[network].value != state_vcd:
                self._writer.change(
                    self._network_variables[network], chunk.tick * 15, state_vcd
                )

        for component, variables in chunk.variables.items():
            if component not in self._component_variables:
                self.log(
                    LogLevel.ERROR,
                    component,
                    "No associated component variables in VCDWriter",
                    chunk.tick,
                )
                continue

            for variable, value in variables.items():
                if variable not in self._component_variables[component]:
                    self.log(
                        LogLevel.ERROR,
                        component,
                        f"No associated component variable {variable} in VCDWriter",
                        chunk.tick,
                    )
                    continue

                if self._component_variables[component][variable] is None:
                    continue

                if self._component_variables[component][variable].value != value:
                    self._writer.change(
                        self._component_variables[component][variable],
                        chunk.tick * 15,
                        value,
                    )

        if verbose:
            self.check_conflicts(chunk)

        return chunk


def main():
    with open("main.bin", "rb") as f:
        rom_data = f.read()

    engine = SimulationEngine.load(MODULES, TABLES_PATH, rom_data)

    with open("output.vcd", "w") as file:
        with VCDWriter(file, "1 ns", date="today", scope_sep=":") as writer:
            simulator = SimulatorVCD(engine, PERIOD, writer)
            simulator.start(INIT_TICKS, STARTUP_TICKS)

            for _ in range(CYCLES):
                chunk = simulator.step()

                network = simulator.component_pins["I:PAD2"].get("N_HALT")
                if network is None:
                    raise RuntimeError("No N_HALT pin on I:PAD2")
                if chunk.network_states[network] == State.LOW:
                    print("\033[33mCPU HALTED\033[0m")
                    break


if __name__ == "__main__":
    main()
