from simulator.engine.entities.base import Component


class IC74574(Component):
    VCC = "20"
    GND = "10"

    N_OE = "1"  # Active LOW
    CLK = "11"  # Rising Edge

    D0 = "2"
    D1 = "3"
    D2 = "4"
    D3 = "5"
    D4 = "6"
    D5 = "7"
    D6 = "8"
    D7 = "9"

    Q0 = "19"
    Q1 = "18"
    Q2 = "17"
    Q3 = "16"
    Q4 = "15"
    Q5 = "14"
    Q6 = "13"
    Q7 = "12"

    internal_state: int
    prev_clk: bool

    def _init(self):
        self.internal_state = 0
        self.prev_clk = False

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

        clk = self.get(self.CLK)

        # Low -> High edge detection
        if clk and not self.prev_clk:
            new_val = 0
            if self.get(self.D0):
                new_val |= 1 << 0
            if self.get(self.D1):
                new_val |= 1 << 1
            if self.get(self.D2):
                new_val |= 1 << 2
            if self.get(self.D3):
                new_val |= 1 << 3
            if self.get(self.D4):
                new_val |= 1 << 4
            if self.get(self.D5):
                new_val |= 1 << 5
            if self.get(self.D6):
                new_val |= 1 << 6
            if self.get(self.D7):
                new_val |= 1 << 7
            self.internal_state = new_val

        self.prev_clk = clk

        # OE Low -> output. if High -> High-Z do nothing
        if self.get(self.N_OE):
            return

        outputs = [
            self.Q0,
            self.Q1,
            self.Q2,
            self.Q3,
            self.Q4,
            self.Q5,
            self.Q6,
            self.Q7,
        ]
        for i, pin in enumerate(outputs):
            bit_val = (self.internal_state >> i) & 1
            self.set(pin, bool(bit_val))
