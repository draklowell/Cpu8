from simulator.engine.entities.base import Component, Network, Propagatable
from simulator.engine.entities.busconnector import Backplane
from simulator.engine.entities.interface import Interface


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

        self.backplane.propagate()

        for network in self.networks.values():
            network.propagate()
