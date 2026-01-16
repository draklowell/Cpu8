from simulator.engine.entities.base import Component


class IC74573(Component):
    VCC = "20"
    GND = "10"

    N_OE = "1"  # Active LOW
    LE = "11"

    D = [
        "3",
        "4",
        "7",
        "8",
        "13",
        "14",
        "17",
        "18",
    ]
    Q = ["2", "5", "6", "9", "12", "15", "16", "19"]

    internal_state: int

    def _init(self):
        self.internal_state = 0

    def get_variable_sizes(self):
        return {
            "Q": 8,
        }

    def get_variables(self) -> dict[str, int]:
        return {
            "Q": self.internal_state,
        }

    def set_variable(self, var: str, value: int) -> bool:
        if var == "Q":
            value &= 0xFF
            self.log(f"Setting Q to {value} ({value:02X})")
            self.internal_state = value
        else:
            return False

        return True

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        if self.get(self.LE):
            new_val = 0
            for i, pin in enumerate(self.D):
                new_val |= (1 << i) if self.get(pin) else 0
            self.internal_state = new_val

        # OE Low -> output. if High -> High-Z do nothing
        if self.get(self.N_OE):
            return

        for i, pin in enumerate(self.Q):
            bit_val = (self.internal_state >> i) & 1
            self.set(pin, bool(bit_val))
