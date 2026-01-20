from simulator.engine.entities.base import Component


class IC74273(Component):
    VCC = "20"
    GND = "10"

    CLK = "11"
    N_MR = "1"

    D0 = "3"
    D1 = "4"
    D2 = "7"
    D3 = "8"
    D4 = "13"
    D5 = "14"
    D6 = "17"
    D7 = "18"

    Q0 = "2"
    Q1 = "5"
    Q2 = "6"
    Q3 = "9"
    Q4 = "12"
    Q5 = "15"
    Q6 = "16"
    Q7 = "19"

    state: int
    prev_clk: bool

    def _init(self):
        self.state = 0
        self.prev_clk = False

    def get_variable_sizes(self):
        return {
            "Q": 8,
        }

    def get_variables(self) -> dict[str, int]:
        return {
            "Q": self.state,
        }

    def set_variable(self, var: str, value: int) -> bool:
        if var == "Q":
            value &= 0xFF
            self.log(f"Setting Q to {value} ({value:02X})")
            self.state = value
        else:
            return False

        return True

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        if not self.get(self.N_MR):
            self.state = 0
            self._update_outputs()
            self.prev_clk = self.get(self.CLK)
            return

        clk = self.get(self.CLK)

        if clk and not self.prev_clk:
            new_val = 0
            if self.get(self.D0):
                new_val |= 1
            if self.get(self.D1):
                new_val |= 2
            if self.get(self.D2):
                new_val |= 4
            if self.get(self.D3):
                new_val |= 8
            if self.get(self.D4):
                new_val |= 16
            if self.get(self.D5):
                new_val |= 32
            if self.get(self.D6):
                new_val |= 64
            if self.get(self.D7):
                new_val |= 128
            self.state = new_val

        self._update_outputs()
        self.prev_clk = clk

    def _update_outputs(self):
        self.set(self.Q0, bool(self.state & 1))
        self.set(self.Q1, bool(self.state & 2))
        self.set(self.Q2, bool(self.state & 4))
        self.set(self.Q3, bool(self.state & 8))
        self.set(self.Q4, bool(self.state & 16))
        self.set(self.Q5, bool(self.state & 32))
        self.set(self.Q6, bool(self.state & 64))
        self.set(self.Q7, bool(self.state & 128))
