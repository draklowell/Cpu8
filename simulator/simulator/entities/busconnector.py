from collections import deque

from simulator.entities.base import Component, Network, NetworkState, Propagatable


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
    networks: dict[str, list[Network]]
    power: bool = False

    def __init__(self, name: str):
        self.name = name
        self.networks = {}
        self.power = False

        for i in range(1, 83):
            self.networks[f"B{i}"] = []
            self.networks[f"A{i}"] = []

    def propagate(self):
        for pin in self.VCC:
            networks = self.networks[pin]
            for network in networks:
                network.set(self.name, self.power)

        for pin in self.GND:
            networks = self.networks[pin]
            for network in networks:
                network.set(self.name, not self.power)

        # Naive synchronization
        for pin, networks in self.networks.items():
            state = NetworkState.FLOATING
            drivers = set()
            for network in networks:
                drivers |= set(network.new_drivers)
                if state == NetworkState.CONFLICT:
                    continue

                if network.new_state == NetworkState.CONFLICT:
                    state = NetworkState.CONFLICT
                elif (
                    network.new_state != NetworkState.FLOATING
                    and state == NetworkState.FLOATING
                ):
                    state = network.new_state
                elif network.new_state == state and len(drivers) == 1:
                    continue
                elif network.new_state != NetworkState.FLOATING:
                    state = NetworkState.CONFLICT

            for network in networks:
                network.new_state = state
                network.new_drivers = deque(drivers)

    def power_on(self):
        self.power = True

    def power_off(self):
        self.power = False


class BusConnector(Component):
    backplane: Backplane | None

    def _init(self):
        self.backplane = None

    def set_backplane(self, backplane: Backplane):
        if self.backplane is not None:
            for pin, network in self.pins.items():
                self.backplane.networks[pin].remove(network)

        self.backplane = backplane
        for pin, network in self.pins.items():
            backplane.networks[pin].append(network)

    def propagate(self):
        pass
