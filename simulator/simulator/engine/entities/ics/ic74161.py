from simulator.engine.entities.base import Component


class IC74161(Component):
    VCC = "16"
    GND = "8"

    CLK = "2"
    N_MR = "1"  # Active Low
    N_PE = "9"  # Active Low
    CET = "10"
    CEP = "7"
    TC = "15"

    D0 = "3"
    D1 = "4"
    D2 = "5"
    D3 = "6"

    Q0 = "14"
    Q1 = "13"
    Q2 = "12"
    Q3 = "11"

    count: int
    prev_clk: bool

    def _init(self):
        self.count = 0
        self.prev_clk = False

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        if not self.get(self.N_MR):
            self.count = 0
            self._update_outputs()
            return

        clk = self.get(self.CLK)

        if clk and not self.prev_clk:
            if not self.get(self.N_PE):
                val = 0
                if self.get(self.D0):
                    val |= 1
                if self.get(self.D1):
                    val |= 2
                if self.get(self.D2):
                    val |= 4
                if self.get(self.D3):
                    val |= 8
                self.count = val
            elif self.get(self.CEP) and self.get(self.CET):
                self.count = (self.count + 1) & 0xF

        self._update_outputs()

        # High when Count=15 AND CET=High
        tc = (self.count == 15) and self.get(self.CET)
        self.set(self.TC, tc)

        self.prev_clk = clk

    def _update_outputs(self):
        self.set(self.Q0, bool(self.count & 1))
        self.set(self.Q1, bool(self.count & 2))
        self.set(self.Q2, bool(self.count & 4))
        self.set(self.Q3, bool(self.count & 8))
