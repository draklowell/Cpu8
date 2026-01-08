from simulator.base import Component


class IC74273(Component):
    VCC = "20"
    GND = "10"
    CLK = "11"
    CLR = "1"

    D1 = "3"
    D2 = "4"
    D3 = "7"
    D4 = "8"
    D5 = "13"
    D6 = "14"
    D7 = "17"
    D8 = "18"

    Q1 = "2"
    Q2 = "5"
    Q3 = "6"
    Q4 = "9"
    Q5 = "12"
    Q6 = "15"
    Q7 = "16"
    Q8 = "19"

    state: int
    prev_clk: bool

    def _init(self):
        self.state = 0
        self.prev_clk = False

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        if not self.get(self.CLR):
            self.state = 0
            self._update_outputs()
            self.prev_clk = self.get(self.CLK)
            return

        clk = self.get(self.CLK)

        if clk and not self.prev_clk:
            new_val = 0
            if self.get(self.D1):
                new_val |= 1
            if self.get(self.D2):
                new_val |= 2
            if self.get(self.D3):
                new_val |= 4
            if self.get(self.D4):
                new_val |= 8
            if self.get(self.D5):
                new_val |= 16
            if self.get(self.D6):
                new_val |= 32
            if self.get(self.D7):
                new_val |= 64
            if self.get(self.D8):
                new_val |= 128
            self.state = new_val

        self._update_outputs()
        self.prev_clk = clk

    def _update_outputs(self):
        self.set(self.Q1, bool(self.state & 1))
        self.set(self.Q2, bool(self.state & 2))
        self.set(self.Q3, bool(self.state & 4))
        self.set(self.Q4, bool(self.state & 8))
        self.set(self.Q5, bool(self.state & 16))
        self.set(self.Q6, bool(self.state & 32))
        self.set(self.Q7, bool(self.state & 64))
        self.set(self.Q8, bool(self.state & 128))
