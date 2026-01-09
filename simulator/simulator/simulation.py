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
        self._logs.clear()
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

    def get_component_pin_networks(self) -> dict[str, dict[str, str]]:
        result = {}
        for component in self.cpu.components.values():
            pin_map = {}
            for pin_name, network in component.pins.items():
                pin_map[pin_name] = network.name
            result[component.name] = pin_map
        return result

    def get_component_pin_aliases(self) -> dict[str, list[tuple[str, str]]]:
        result = {}
        for component in self.cpu.components.values():
            result[component.name] = component.get_pin_aliases()
        return result

    def set_clock(self, state: bool):
        self.interface.set_clock(state)

    def set_wait(self, state: bool):
        self.interface.set_wait(state)

    def set_reset(self, state: bool):
        self.interface.set_reset(state)

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

        chunk = WaveformChunk(
            network_drivers=network_drivers,
            network_states=network_states,
            logs=self.provider.collect_logs(),
            tick=self._tick,
            clock=self.interface.get_clock(),
            wait=self.interface.get_wait(),
            reset=self.interface.get_reset(),
            halt=self.interface.get_halt(),
        )
        self._tick += 1
        return chunk
