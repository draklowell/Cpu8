from base import Component


class IC7400(Component):
    VCC = "14"
    B3 = "13"
    A3 = "12"
    Y3 = "11"
    B2 = "10"
    A2 = "9"
    Y2 = "8"
    GND = "7"
    Y1 = "6"
    A1 = "5"
    B1 = "4"
    Y0 = "3"
    A0 = "2"
    B0 = "1"

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            # IC is not powered, outputs float
            self.log("Not powered, outputs float")
            return

        a1 = self.get(self.B1)
        b1 = self.get(self.A1)
        self.set(self.Y1, not (a1 and b1))

        a2 = self.get(self.A2)
        b2 = self.get(self.B2)
        self.set(self.Y2, not (a2 and b2))

        a3 = self.get(self.A3)
        b3 = self.get(self.B3)
        self.set(self.Y3, not (a3 and b3))

        a4 = self.get(self.A0)
        b4 = self.get(self.B0)
        self.set(self.Y0, not (a4 and b4))


class IC7402(Component):
    VCC = "14"
    B3 = "11"
    A3 = "12"
    Y3 = "13"
    B2 = "8"
    A2 = "9"
    Y2 = "10"
    GND = "7"
    Y1 = "4"
    A1 = "5"
    B1 = "6"
    Y0 = "1"
    A0 = "2"
    B0 = "3"

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            # IC is not powered, outputs float
            self.log("Not powered, outputs float")
            return

        a1 = self.get(self.B1)
        b1 = self.get(self.A1)
        self.set(self.Y1, not (a1 or b1))

        a2 = self.get(self.A2)
        b2 = self.get(self.B2)
        self.set(self.Y2, not (a2 or b2))
        a3 = self.get(self.A3)
        b3 = self.get(self.B3)
        self.set(self.Y3, not (a3 or b3))

        a4 = self.get(self.A0)
        b4 = self.get(self.B0)
        self.set(self.Y0, not (a4 or b4))


class IC7404(Component):
    VCC = "14"
    A6 = "13"
    Y6 = "12"
    A5 = "11"
    Y5 = "10"
    A4 = "9"
    Y4 = "8"
    GND = "7"
    Y3 = "6"
    A3 = "5"
    Y2 = "4"
    A2 = "3"
    Y1 = "2"
    A1 = "1"

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            self.log("Not powered")
            return

        self.set(self.Y1, not self.get(self.A1))
        self.set(self.Y2, not self.get(self.A2))
        self.set(self.Y3, not self.get(self.A3))
        self.set(self.Y4, not self.get(self.A4))
        self.set(self.Y5, not self.get(self.A5))
        self.set(self.Y6, not self.get(self.A6))


class IC74109(Component):
    VCC = "16"
    GND = "8"

    CLR1 = "15"  # Active Low
    PRE1 = "4"  # Active Low
    CLK1 = "12"
    J1 = "14"
    nK1 = "13"
    Q1 = "10"
    nQ1 = "11"

    CLR2 = "1"
    PRE2 = "5"
    CLK2 = "6"
    J2 = "2"
    nK2 = "3"
    Q2 = "7"
    nQ2 = "9"

    state1: bool
    state2: bool
    prev_clk1: bool
    prev_clk2: bool

    def _init(self):
        self.state1 = False
        self.state2 = False
        self.prev_clk1 = False
        self.prev_clk2 = False

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        self._process_flipflop(
            self.CLR1, self.PRE1, self.CLK1, self.J1, self.nK1, self.Q1, self.nQ1, 1
        )
        self._process_flipflop(
            self.CLR2, self.PRE2, self.CLK2, self.J2, self.nK2, self.Q2, self.nQ2, 2
        )

    def _process_flipflop(
        self, clr_pin, pre_pin, clk_pin, j_pin, nk_pin, q_pin, nq_pin, idx
    ):
        clr = self.get(clr_pin)
        pre = self.get(pre_pin)

        current_q = self.state1 if idx == 1 else self.state2

        next_q = current_q

        if not clr and pre:
            next_q = False
        elif clr and not pre:
            next_q = True
        elif not clr and not pre:
            next_q = True  # or False, undefined in real IC

        else:
            clk = self.get(clk_pin)
            prev_clk = self.prev_clk1 if idx == 1 else self.prev_clk2

            if clk and not prev_clk:
                j = self.get(j_pin)
                k = not self.get(nk_pin)

                if not j and not k:
                    next_q = current_q
                elif not j and k:
                    next_q = False
                elif j and not k:
                    next_q = True
                elif j and k:
                    next_q = not current_q

            if idx == 1:
                self.prev_clk1 = clk
            else:
                self.prev_clk2 = clk

        if idx == 1:
            self.state1 = next_q
        else:
            self.state2 = next_q

        self.set(q_pin, next_q)
        self.set(nq_pin, not next_q)
