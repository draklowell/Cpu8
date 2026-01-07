from typing import Iterator

from simulator.base import Component, Network


class Motherboard:
    networks: dict[str, Network]

    def __init__(self):
        self.networks = {}

        for i in range(1, 83):
            self.networks[f"B{i}"] = Network()
            self.networks[f"A{i}"] = Network()

    def get_networks(self) -> Iterator[tuple[str, Network]]:
        return self.networks.items()


class BusConnector(Component):
    motherboard: Motherboard | None

    def _init(self):
        self.motherboard = None

    def set_motherboard(self, motherboard: Motherboard):
        self.motherboard = motherboard

    def propagate(self):
        if self.motherboard is None:
            return

        for pin, network in self.motherboard.get_networks():
            if pin not in self.pins:
                continue

            if self.is_floating(pin) and network.is_floating():
                continue

            if self.is_floating(pin):
                # Read from motherboard
                value = network.get()
                self.set(pin, value)
            else:
                # Write to motherboard
                value = self.pins[pin].get()
                network.set(value)
