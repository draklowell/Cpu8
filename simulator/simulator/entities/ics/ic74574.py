from simulator.entities.base import Component


class IC74574(Component):
    VCC = "20"
    GND = "10"
    OE = "1"  # Active LOW
    CLK = "11"  # Rising Edge

    D1 = "2"
    D2 = "3"
    D3 = "4"
    D4 = "5"
    D5 = "6"
    D6 = "7"
    D7 = "8"
    D8 = "9"

    Q1 = "19"
    Q2 = "18"
    Q3 = "17"
    Q4 = "16"
    Q5 = "15"
    Q6 = "14"
    Q7 = "13"
    Q8 = "12"

    internal_state: int
    prev_clk: bool

    def _init(self):
        self.internal_state = 0
        self.prev_clk = False

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        clk = self.get(self.CLK)

        # Low -> High edge detection
        if clk and not self.prev_clk:
            new_val = 0
            if self.get(self.D1):
                new_val |= 1 << 0
            if self.get(self.D2):
                new_val |= 1 << 1
            if self.get(self.D3):
                new_val |= 1 << 2
            if self.get(self.D4):
                new_val |= 1 << 3
            if self.get(self.D5):
                new_val |= 1 << 4
            if self.get(self.D6):
                new_val |= 1 << 5
            if self.get(self.D7):
                new_val |= 1 << 6
            if self.get(self.D8):
                new_val |= 1 << 7
            self.internal_state = new_val

        self.prev_clk = clk

        # OE Low -> output. if High -> High-Z do nothing
        if self.get(self.OE):
            return

        outputs = [
            self.Q1,
            self.Q2,
            self.Q3,
            self.Q4,
            self.Q5,
            self.Q6,
            self.Q7,
            self.Q8,
        ]
        for i, pin in enumerate(outputs):
            bit_val = (self.internal_state >> i) & 1
            self.set(pin, bool(bit_val))
