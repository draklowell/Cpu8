import warnings
from abc import ABC, abstractmethod


class Propagatable(ABC):
    @abstractmethod
    def propagate(self):
        pass


class Network(Propagatable):
    name: str
    value: bool | None
    new_value: bool | None

    def __init__(self, name: str):
        self.name = name
        self.value = None
        self.new_value = None

    def propagate(self):
        self.value = self.new_value
        self.new_value = None

    def is_floating(self) -> bool:
        return self.value is None

    def set(self, value: bool):
        if self.new_value is not None and self.new_value != value:
            raise ValueError(
                f"Network conflict ({self.name}): trying to drive different values"
            )

        self.new_value = value

    def get(self):
        if self.value is None:
            warnings.warn(
                f"Reading from undriven network ({self.name}), returning False"
            )
            return False

        return self.value

    def __repr__(self):
        return f"<Network {self.name}: {self.value}>"


class Component(Propagatable):
    name: str
    pins: dict[str, Network]

    def __init__(self, name: str, pins: dict[str, Network]):
        self.name = name
        self.pins = pins
        self._init()

    def _init(self):
        pass

    def log(self, message: str):
        print(f"[{self.name}] {message}")

    def is_floating(self, pin: str) -> bool:
        if pin not in self.pins:
            warnings.warn(
                f"[{self.name}] Checking floating state of non-existent pin {pin}, returning True"
            )
            return True

        return self.pins[pin].is_floating()

    def set(self, pin: str, value: bool):
        if pin not in self.pins:
            warnings.warn(f"[{self.name}] Writing to non-existent pin {pin}, ignoring")
            return

        self.pins[pin].set(value)

    def get(self, pin: str) -> bool:
        if pin not in self.pins:
            warnings.warn(
                f"[{self.name}] Reading from non-existent pin {pin}, returning False"
            )
            return False

        return self.pins[pin].get()

    @abstractmethod
    def propagate(self):
        pass

    def __repr__(self):
        return f"<Component {self.name} with pins {list(self.pins.keys())}>"
