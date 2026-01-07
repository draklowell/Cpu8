from base import Component

class IC74161(Component):
    VCC = "16"
    GND = "8"
    CLK = "2"
    CLR = "1"  # Active Low
    LOAD = "9" # Active Low
    ENT = "10"
    ENP = "7"
    RCO = "15"


    A="3" 
    B="4" 
    C="5"
    D="6"

    QA="14"
    QB="13"
    QC="12"
    QD="11"

    count: int
    prev_clk: bool

    def _init(self):
        self.count = 0
        self.prev_clk = False

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND): return

        if not self.get(self.CLR):
            self.count = 0
            self._update_outputs()
            return

        clk = self.get(self.CLK)

        if clk and not self.prev_clk:
            if not self.get(self.LOAD):
                val = 0
                if self.get(self.A): val |= 1
                if self.get(self.B): val |= 2
                if self.get(self.C): val |= 4
                if self.get(self.D): val |= 8
                self.count = val
            elif self.get(self.ENP) and self.get(self.ENT):
                self.count = (self.count + 1) & 0xF
            
            self._update_outputs()

        # High when Count=15 AND ENT=High
        rco = (self.count == 15) and self.get(self.ENT)
        self.set(self.RCO, rco)

        self.prev_clk = clk

    def _update_outputs(self):
        self.set(self.QA, bool(self.count & 1))
        self.set(self.QB, bool(self.count & 2))
        self.set(self.QC, bool(self.count & 4))
        self.set(self.QD, bool(self.count & 8))