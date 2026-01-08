from simulator.entities.base import Messaging
from simulator.entities.cpu import CPU


class Motherboard(Messaging):
    name: str = "Motherboard"

    def __init__(self, cpu: CPU):
        self.cpu = cpu
        self.cpu.interface.set_read_callback(self._cb_read)
        self.cpu.interface.set_write_callback(self._cb_write)
        self._rom = bytes(10240)
        self._rw = bytearray(6144)
        self._stack = bytearray(1024)

    # def export(self) -> str:
    #     results = {}

    #     hashes = {}
    #     seq = 1
    #     def _hash(name: str) -> str:
    #         nonlocal seq

    #         if name in hashes:
    #             return hashes[name]

    #         hashes[name] = str(seq)
    #         seq += 1
    #         return hashes[name]

    #     def _color(network: Network) -> str:
    #         if network.state == NetworkState.DRIVEN_HIGH:
    #             return "red"
    #         elif network.state == NetworkState.DRIVEN_LOW:
    #             return "blue"
    #         elif network.state == NetworkState.CONFLICT:
    #             return "orange"
    #         else:
    #             return "gray"

    #     modules = {}
    #     for component in self.cpu.components.values():
    #         if component.name == "BP":
    #             module = "BP"
    #             component_name = "Backplane"
    #         else:
    #             if ":" not in component.name:
    #                 raise ValueError(f"Component name {component.name} is invalid")

    #             module, component_name = component.name.split(":", 1)

    #         if module not in modules:
    #             modules[module] = {
    #                 "components": {},
    #                 "networks": {},
    #             }

    #         modules[module]["components"][component_name] = component

    #     for network in self.cpu.networks.values():
    #         if ":"  not in network.name:
    #             raise ValueError(f"Network name {network.name} is invalid")

    #         module, network_name = network.name.split(":", 1)
    #         if module not in modules:
    #             modules[module] = {
    #                 "components": {},
    #                 "networks": {},
    #             }

    #         modules[module]["networks"][network_name] = network

    #     for module, content in modules.items():
    #         components = content["components"]
    #         networks = content["networks"]

    #         dot = Digraph(engine="dot")
    #         dot.attr(rankdir="LR")

    #         for network_name, network in networks.items():
    #             dot.node(
    #                 _hash(network.name),
    #                 network_name,
    #                 shape="diamond",
    #                 color=_color(network),
    #                 fontcolor=_color(network),
    #             )

    #         for component_name, component in components.items():
    #             with dot.subgraph(name="cluster_" + _hash(component.name)) as c:
    #                 c.attr(label=component_name)
    #                 c.attr(style="dotted")

    #                 for pin, network in component.pins.items():
    #                     pin_name = f"{component.name}:{pin}"
    #                     c.node(
    #                         _hash(pin_name), pin, shape="ellipse"
    #                     )
    #                     dot.edge(
    #                         _hash(pin_name),
    #                         _hash(component.pins[pin].name),
    #                         color=_color(component.pins[pin]),
    #                     )

    #         modules[module] = dot.source

    #     return modules

    def set_rom(self, data: bytes):
        if len(data) < 10240:
            self.warn(
                f"ROM data is smaller than 10KB ({len(data)} bytes), padding with zeros"
            )
            data += bytes(10240 - len(data))
        elif len(data) > 10240:
            self.warn(f"ROM data is larger than 10KB ({len(data)} bytes), truncating")
            data = data[:10240]

        self._rom = data

    def _cb_read(self, address: int) -> int:
        self.log(f"Read request at address: 0x{address:04X}")

        if address <= 0x2800:
            return self._rom[address]

        if 0x4000 <= address <= 0x5800:
            return self._rw[address - 0x4000]

        if 0xFBFF <= address <= 0xFFFF:
            return self._stack[address - 0xFBFF]

        raise RuntimeError(f"Invalid read address: 0x{address:04X}")

    def _cb_write(self, address: int, value: int) -> None:
        self.log(f"Write request at address: 0x{address:04X} with value 0x{value:02X}")

        if address <= 0x2800:
            return

        if 0x4000 <= address <= 0x5800:
            self._rw[address - 0x4000] = value
            return

        if 0xFBFF <= address <= 0xFFFF:
            self._stack[address - 0xFBFF] = value
            return

        raise RuntimeError(f"Invalid write address: 0x{address:04X}")

    def propagate(self):
        self.cpu.propagate()
