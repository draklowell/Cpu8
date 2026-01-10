from dataclasses import dataclass

from simulator.base import LogLevel, State, WaveformChunk
from simulator.engine.entities.base import MessagingProvider, NetworkState
from simulator.engine.entities.cpu import CPU
from simulator.engine.entities.interface import Interface
from simulator.engine.loader import load
from simulator.engine.motherboard import Motherboard

STATE_MAPPING = {
    NetworkState.DRIVEN_HIGH: State.HIGH,
    NetworkState.DRIVEN_LOW: State.LOW,
    NetworkState.FLOATING: State.FLOATING,
    NetworkState.CONFLICT: State.CONFLICT,
}


class StoringMessagingProvider(MessagingProvider):
    _logs: list[tuple[LogLevel, str, str]]

    def __init__(self):
        self._logs = []

    def log(self, source: str, message: str):
        self._logs.append((LogLevel.INFO, source, message))

    def ok(self, source: str, message: str):
        self._logs.append((LogLevel.OK, source, message))

    def warn(self, source: str, message: str):
        self._logs.append((LogLevel.WARNING, source, message))

    def error(self, source: str, message: str):
        self._logs.append((LogLevel.ERROR, source, message))

    def collect_logs(self) -> list[tuple[LogLevel, str, str]]:
        logs = self._logs
        self._logs = []
        return logs


class SimulationEngine:
    _tick: int
    provider: StoringMessagingProvider
    motherboard: Motherboard
    cpu: CPU
    interface: Interface

    def __init__(self, cpu: CPU, rom: bytes):
        self._tick = 0
        self.provider = StoringMessagingProvider()
        for component in cpu.components.values():
            component.set_messaging_provider(self.provider)
        for network in cpu.networks.values():
            network.set_messaging_provider(self.provider)
        self.motherboard = Motherboard(cpu)
        self.motherboard.set_messaging_provider(self.provider)
        self.motherboard.set_rom(rom)
        self.cpu = cpu
        self.interface = cpu.interface

    @classmethod
    def load(
        cls, modules_path: str, tables_path: str, rom: bytes
    ) -> "SimulationEngine":
        cpu = load(modules_path, tables_path)
        return cls(cpu, rom)

    def get_component_pins(self) -> dict[str, dict[str, str]]:
        result = {}
        for component in self.cpu.components.values():
            aliases = component.get_pin_aliases()
            aliases_map = {}
            for pin, alias in aliases:
                if pin in aliases_map:
                    raise ValueError(
                        f"Multiple aliases for pin {pin} of component {component.name}"
                    )
                aliases_map[pin] = alias

            pin_map = {}
            for pin, network in component.pins.items():
                alias = aliases_map.get(pin, pin)
                if alias in pin_map and pin_map[alias] != network.name:
                    raise ValueError(
                        f"Alias {alias} of component {component.name} maps to multiple networks"
                    )

                pin_map[alias] = network.name

            result[component.name] = pin_map

        return result

    def set_component_variable(self, component_name: str, var: str, value: int) -> bool:
        component = self.cpu.components.get(component_name)
        if component is None:
            return False

        return component.set_variable(var, value)

    def set_power(self, state: bool):
        if state:
            self.cpu.backplane.power_on()
        else:
            self.cpu.backplane.power_off()

    def tick(self) -> WaveformChunk:
        self.motherboard.propagate()

        network_drivers = {}
        network_states = {}
        for network in self.cpu.networks.values():
            network_drivers[network.name] = list(network.drivers)
            network_states[network.name] = STATE_MAPPING[network.state]

        variables = {}
        for component in self.cpu.components.values():
            variables[component.name] = {}
            for name, value in component.get_variables().items():
                variables[component.name][name] = value

        logs = self.provider.collect_logs()
        chunk = WaveformChunk(
            network_drivers=network_drivers,
            network_states=network_states,
            logs=logs,
            tick=self._tick,
            variables=variables,
        )
        self._tick += 1
        return chunk
