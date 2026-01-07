from simulator.base import Component, Network
from simulator.busconnector import BusConnector
from simulator.eeprom import EEPROM
from simulator.ic74xx import IC7400, IC7404, IC74109
from simulator.ic74138 import IC74138
from simulator.ic74154 import IC74154
from simulator.ic74161 import IC74161
from simulator.ic74181 import IC74181
from simulator.ic74193 import IC74193
from simulator.ic74245 import IC74245
from simulator.ic74273 import IC74273
from simulator.ic74574 import IC74574
from simulator.interface import Interface

FOOTPRINTS_FILTERED_OUT = {
    "TestPoint:TestPoint_Pad_D1.0mm",
    "Capacitor_THT:C_Radial_D6.3mm_H5.0mm_P2.50mm",
    "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
}

MAPPING = {
    "74LS00": IC7400,
    "74LS04": IC7404,
    "74LS109": IC74109,
    "74LS138": IC74138,
    "74LS154": IC74154,
    "74LS161": IC74161,
    "74LS181": IC74181,
    "74LS193": IC74193,
    "74LS245": IC74245,
    "74LS273": IC74273,
    "74LS574": IC74574,
    "74HC00": IC7400,
    "74HC04": IC7404,
    "74HC109": IC74109,
    "74HC138": IC74138,
    "74HC154": IC74154,
    "74HC161": IC74161,
    "74HC181": IC74181,
    "74HC193": IC74193,
    "74HC245": IC74245,
    "74HC273": IC74273,
    "74HC574": IC74574,
    "28C256": EEPROM,
    "BusConnector": BusConnector,
    "Conn_02x19_Counter_Clockwise": Interface,
}


def _parse(
    data: str,
) -> tuple[dict[str, tuple[str, str]], dict[str, list[tuple[str, str]]]]:
    lines = [line.strip() for line in data.splitlines() if line.strip()]

    last_net = None

    components = {}
    networks = {}

    for line in lines:
        if line.startswith(".ADD_COM"):
            line = line.removeprefix(".ADD_COM").strip()
            uuid, type_, footprint = line.split("     ")

            if uuid in components:
                raise ValueError(f"Component {uuid} defined multiple times")

            components[uuid] = (type_[1:-1], footprint[1:-1])  # Remove quotes
        elif line.startswith(".ADD_TER"):
            line = line.removeprefix(".ADD_TER").strip()

            data, net_name = line.split("     ")
            net_name = net_name[1:-1]  # Remove quotes
            component_uuid, pin_name = data.split("   ")

            if net_name in networks:
                raise ValueError(f"Network {net_name} defined multiple times")

            if component_uuid not in components:
                raise ValueError(f"Component {component_uuid} not defined")

            networks[net_name] = [(component_uuid, pin_name)]
            last_net = net_name
        elif line.startswith(".TER") or not line.startswith("."):
            line = line.removeprefix(".TER").strip()

            component_uuid, pin_name = line.split("   ")

            if last_net is None:
                raise ValueError(".TER found before any .ADD_TER")

            if component_uuid not in components:
                raise ValueError(f"Component {component_uuid} not defined")

            networks[last_net].append((component_uuid, pin_name))
        elif line.startswith("."):
            continue  # Ignore other directives

    return components, networks


def parse(data: str) -> tuple[list[Component], list[Network]]:
    components_data, networks_data = _parse(data)

    pinouts: dict[str, dict[str, str]] = {}

    components = []
    networks = []

    for name, terminals in networks_data.items():
        network = Network(name)
        networks.append(network)
        for component_name, pin in terminals:
            if component_name not in pinouts:
                pinouts[component_name] = {}

            pinouts[component_name][pin] = network

    for uuid, (type_name, footprint) in components_data.items():
        if footprint in FOOTPRINTS_FILTERED_OUT:
            continue

        if type_name not in MAPPING:
            raise ValueError(f"Unknown component type {type_name}")

        component_class = MAPPING[type_name]
        component = component_class(name=uuid, pins=pinouts.get(uuid, {}))
        components.append(component)

    return components, networks
