from simulator.engine.entities.base import Component


class IC74193(Component):
    VCC = "16"
    GND = "8"

    D0 = "15"
    CLR = "14"
    N_BO = "13"
    N_CO = "12"
    N_LOAD = "11"
    D2 = "10"
    D3 = "9"
    Q3 = "7"
    Q2 = "6"
    N_UP = "5"
    N_DOWN = "4"
    Q0 = "3"
    Q1 = "2"
    D1 = "1"

    value: int
    prev_up: bool
    prev_down: bool

    def _init(self):
        self.value = 0
        self.new_value = 0
        self.prev_up = False
        self.prev_down = False

    def get_variable_sizes(self):
        return {
            "Q": 4,
        }

    def get_variables(self) -> dict[str, int]:
        return {
            "Q": self.value,
        }

    def set_variable(self, var: str, value: int) -> bool:
        if var == "Q":
            value &= 0x0F
            self.log(f"Setting Q to {value} ({value:01X})")
            self.value = value
        else:
            return False

        return True

    def get_value(self) -> int:
        d0 = self.get(self.D0)
        d1 = self.get(self.D1)
        d2 = self.get(self.D2)
        d3 = self.get(self.D3)
        return (d3 << 3) | (d2 << 2) | (d1 << 1) | d0

    def set_value(self, value: int):
        if value > 15:
            self.set(self.N_CO, False)
        else:
            self.set(self.N_CO, True)

        if value < 0:
            self.set(self.N_BO, False)
        else:
            self.set(self.N_BO, True)

        self.value = value & 0x0F  # 4 bits

        d0 = (self.value >> 0) & 1
        d1 = (self.value >> 1) & 1
        d2 = (self.value >> 2) & 1
        d3 = (self.value >> 3) & 1
        self.set(self.Q0, bool(d0))
        self.set(self.Q1, bool(d1))
        self.set(self.Q2, bool(d2))
        self.set(self.Q3, bool(d3))

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        if self.get(self.CLR):  # Clear
            self.set_value(0)
            return

        if not self.get(self.N_LOAD):  # Load
            self.set_value(self.get_value())
            return

        up = self.get(self.N_UP)
        down = self.get(self.N_DOWN)

        value = self.value
        if up and not self.prev_up:
            # Rising edge on UP
            value += 1
        if down and not self.prev_down:
            # Rising edge on DOWN
            value -= 1

        self.set_value(value)
        self.prev_up = up
        self.prev_down = down
