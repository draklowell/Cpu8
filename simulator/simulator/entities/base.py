from abc import ABC, abstractmethod
from collections import deque
from enum import StrEnum


class Propagatable(ABC):
    @abstractmethod
    def propagate(self):
        pass


class Messaging:
    name: str

    def log(self, message: str):
        print(f"[{self.name}] {message}")

    def ok(self, message: str):
        print(f"\033[32m[{self.name}] {message}\033[0m")

    def warn(self, message: str):
        print(f"\033[33m[{self.name}] {message}\033[0m")

    def error(self, message: str):
        print(f"\033[31m[{self.name}] {message}\033[0m")


class NetworkState(StrEnum):
    FLOATING = "FLOATING"
    DRIVEN_HIGH = "DRIVEN_HIGH"
    DRIVEN_LOW = "DRIVEN_LOW"
    CONFLICT = "CONFLICT"


class Network(Propagatable, Messaging):
    name: str

    state: NetworkState
    drivers: deque[str]
    new_state: NetworkState
    new_drivers: deque[str]

    def __init__(self, name: str):
        self.name = name + "!"

        self.state = NetworkState.FLOATING
        self.drivers = deque()
        self.new_state = NetworkState.FLOATING
        self.new_drivers = deque()

    def propagate(self):
        self.drivers = self.new_drivers.copy()
        self.state = self.new_state
        self.new_state = NetworkState.FLOATING
        self.new_drivers.clear()

    def is_floating(self) -> bool:
        return self.state == NetworkState.FLOATING

    def set(self, component: str, value: bool):
        if component in self.new_drivers:
            return

        if self.new_state != NetworkState.FLOATING:
            self.new_state = NetworkState.CONFLICT
            self.new_drivers.append(component)
            return

        self.new_state = NetworkState.DRIVEN_HIGH if value else NetworkState.DRIVEN_LOW
        self.new_drivers.append(component)

    def get(self):
        # Return True if last state was DRIVEN_HIGH
        # False if DRIVEN_LOW, CONFLICT or FLOATING
        return self.state == NetworkState.DRIVEN_HIGH

    def __repr__(self):
        return f"<Network {self.name}: {self.state} driven by {list(self.drivers)}>"


class Component(Propagatable, Messaging):
    name: str
    pins: dict[str, Network]

    def __init__(self, name: str, pins: dict[str, Network]):
        self.name = name
        self.pins = pins

        self._init()

    def _init(self):
        pass

    def is_floating(self, pin: str) -> bool:
        if pin not in self.pins:
            return True

        return self.pins[pin].is_floating()

    def set(self, pin: str, value: bool):
        if pin not in self.pins:
            return

        self.pins[pin].set(self.name, value)

    def get(self, pin: str) -> bool:
        if pin not in self.pins:
            return False

        return self.pins[pin].get()

    @abstractmethod
    def propagate(self):
        pass

    def __repr__(self):
        return f"<Component {self.name} with pins {list(self.pins.keys())}>"
