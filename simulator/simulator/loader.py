from simulator.entities.base import Component, Network
from simulator.entities.busconnector import Backplane, BusConnector
from simulator.entities.cpu import CPU
from simulator.entities.eeprom import EEPROM
from simulator.entities.interface import Interface
from simulator.parser import parse


def load_components(
    modules: list[tuple[str, str]]
) -> tuple[dict[str, Component], dict[str, Network], Interface, Backplane]:
    backplane = Backplane("BP")
    all_components = {}
    all_networks = {}
    interface = None

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


def load(modules: list[tuple[str, str]], tables_path: str) -> CPU:
    components, networks, interface, backplane = load_components(modules)
    tables_data = load_data(tables_path)
    setup_tables(components, tables_data)

    return CPU(components, networks, interface, backplane)
