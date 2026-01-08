from simulator.base import Component, Network, Propagatable
from simulator.busconnector import Backplane
from simulator.interface import Interface


class CPU(Propagatable):
    def __init__(
        self,
        components: dict[str, Component],
        networks: dict[str, Network],
        interface: Interface,
        backplane: Backplane,
    ):
        self.components = components
        self.networks = networks
        self.interface = interface
        self.backplane = backplane

    def propagate(self):
        for component in self.components.values():
            component.propagate()

        for network in self.networks.values():
            network.propagate()
