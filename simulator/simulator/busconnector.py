from typing import Iterator

from simulator.base import Component, Network, Propagatable


class Backplane(Propagatable):
    VCC = ["A1", "A2", "A3", "A4", "A5", "B1", "B2", "B3", "B4", "B5"]
    GND = [
        "A12",
        "A13",
        "A23",
        "A32",
        "A41",
        "A50",
        "A59",
        "A63",
        "A64",
        "A65",
        "A66",
        "A70",
        "A71",
        "A72",
        "A73",
        "A74",
        "A75",
        "A76",
        "B12",
        "B13",
        "B23",
        "B32",
        "B41",
        "B50",
        "B59",
        "B62",
        "B63",
        "B64",
        "B65",
        "B66",
        "B67",
        "B68",
        "B69",
        "B70",
        "B71",
        "B72",
        "B75",
        "B76",
    ]

    name: str
    pins: dict[str, Network]
    power: bool = False

    def __init__(self, name: str):
        self.name = name
        self.pins = {}
        self.power = False

        for i in range(1, 83):
            self.pins[f"B{i}"] = Network(f"B{i}")
            self.pins[f"A{i}"] = Network(f"A{i}")

    def propagate(self):
        for pin in self.VCC:
            network = self.pins[pin]
            network.set(self.name, self.power)

        for pin in self.GND:
            network = self.pins[pin]
            network.set(self.name, not self.power)

    def power_on(self):
        self.power = True

    def power_off(self):
        self.power = False

    def get_networks(self) -> Iterator[tuple[str, Network]]:
        return self.pins.items()


class BusConnector(Component):
    backplane: Backplane | None

    def _init(self):
        self.backplane = None

    def set_backplane(self, backplane: Backplane):
        self.backplane = backplane

    def propagate(self):
        if self.backplane is None:
            return

        for pin, network in self.backplane.get_networks():
            if pin not in self.pins:
                continue

            if not self.is_floating(pin):
                value = network.get()
                self.set(pin, value)
            if not network.is_floating():
                value = self.pins[pin].get()
                network.set(self.name, value)
