from parser import parse

from simulator.base import Component, Network
from simulator.busconnector import Backplane, BusConnector
from simulator.cpu import CPU
from simulator.eeprom import EEPROM
from simulator.interface import Interface

MODULES = [
    ("netlists/alu_hub.frp", "ALU"),
    ("netlists/core_1.frp", "C1"),
    ("netlists/core_2.frp", "C2"),
    ("netlists/core_3.frp", "C3"),
    ("netlists/interface.frp", "I"),
    ("netlists/program_counter.frp", "PC"),
    ("netlists/register_file_accum.frp", "REG"),
    ("netlists/stack_pointer.frp", "SP"),
]

TABLES_PATH = "../microcode/bin"


def load_components(
    modules: list[tuple[str, str]]
) -> tuple[dict[str, Component], dict[str, Network], Interface, Backplane]:
    backplane = Backplane("BP")
    all_components = {"BP": backplane}
    all_networks = {}
    interface = None

    for _, network in backplane.get_networks():
        network.name = f"BP:{network.name}"
        all_networks[network.name] = network

    for filename, module in modules:
        if module == "BP":
            raise ValueError("Module name 'BP' is reserved for Backplane")

        with open(filename, "r") as f:
            data = f.read()

        components, networks = parse(data)

        for component in components:
            if isinstance(component, Interface):
                if interface is not None:
                    raise ValueError("Multiple interfaces found!")

                interface = component

            if isinstance(component, BusConnector):
                component.set_backplane(backplane)

            if ":" in component.name:
                raise ValueError(f"Component name {component.name} cannot contain ':'")

            component.name = f"{module}:{component.name}"
            all_components[component.name] = component

        for network in networks:
            if ":" in network.name:
                raise ValueError(f"Network name {network.name} cannot contain ':'")

            network.name = f"{module}:{network.name}"
            all_networks[network.name] = network

    if interface is None:
        raise ValueError("No interface found!")

    return all_components, all_networks, interface, backplane


def load_data(path: str) -> list[bytes]:
    result = []
    for i in range(8):
        with open(f"{path}/table{i}.bin", "rb") as f:
            data = f.read()
            if len(data) != 32768:
                raise ValueError(f"table{i}.bin has incorrect size: {len(data)} bytes")

            result.append(data)

    return result


def setup_tables(components: dict[str, Component], data: list[bytes]):
    set_ = set()
    for component in components.values():
        if not isinstance(component, EEPROM):
            continue

        _, name = component.name.split(":", 1)

        if not name.startswith("TABLE"):
            continue

        component.load_data(data[int(name.removeprefix("TABLE")) - 1])
        set_.add(int(name.removeprefix("TABLE")) - 1)

    if set_ != {0, 1, 2, 3, 4, 5, 6, 7}:
        missing = sorted(set(range(8)) - set_)
        raise ValueError(f"Missing EEPROM tables: {missing}")


def load() -> CPU:
    components, networks, interface, backplane = load_components(MODULES)
    tables_data = load_data(TABLES_PATH)
    setup_tables(components, tables_data)

    return CPU(components, networks, interface, backplane)
