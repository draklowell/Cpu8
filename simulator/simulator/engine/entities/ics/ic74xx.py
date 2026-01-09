from simulator.engine.entities.base import Component


class IC7400(Component):
    VCC = "14"
    GND = "7"

    B4 = "13"
    A4 = "12"
    Y4 = "11"
    B3 = "10"
    A3 = "9"
    Y3 = "8"
    Y2 = "6"
    B2 = "5"
    A2 = "4"
    Y1 = "3"
    B1 = "2"
    A1 = "1"

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        a1 = self.get(self.A2)
        b1 = self.get(self.B2)
        self.set(self.Y2, not (a1 and b1))

        a2 = self.get(self.A3)
        b2 = self.get(self.B3)
        self.set(self.Y3, not (a2 and b2))

        a3 = self.get(self.A4)
        b3 = self.get(self.B4)
        self.set(self.Y4, not (a3 and b3))

        a4 = self.get(self.B1)
        b4 = self.get(self.A1)
        self.set(self.Y1, not (a4 and b4))


class IC7402(Component):
    VCC = "14"
    GND = "7"

    A4 = "11"
    B4 = "12"
    Y4 = "13"
    A3 = "8"
    B3 = "9"
    Y3 = "10"
    Y2 = "4"
    A2 = "5"
    B2 = "6"
    Y1 = "1"
    A1 = "2"
    B1 = "3"

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        a1 = self.get(self.B2)
        b1 = self.get(self.A2)
        self.set(self.Y2, not (a1 or b1))

        a2 = self.get(self.B3)
        b2 = self.get(self.A3)
        self.set(self.Y3, not (a2 or b2))
        a3 = self.get(self.B4)
        b3 = self.get(self.A4)
        self.set(self.Y4, not (a3 or b3))

        a4 = self.get(self.A1)
        b4 = self.get(self.B1)
        self.set(self.Y1, not (a4 or b4))


class IC7404(Component):
    VCC = "14"
    GND = "7"

    A6 = "13"
    Y6 = "12"
    A5 = "11"
    Y5 = "10"
    A4 = "9"
    Y4 = "8"
    Y3 = "6"
    A3 = "5"
    Y2 = "4"
    A2 = "3"
    Y1 = "2"
    A1 = "1"

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
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

    N_R1 = "1"
    N_S1 = "5"
    CLK1 = "4"
    J1 = "2"
    N_K1 = "3"
    Q1 = "6"
    N_Q1 = "7"

    N_R2 = "15"
    N_S2 = "11"
    CLK2 = "12"
    J2 = "14"
    N_K2 = "13"
    Q2 = "10"
    N_Q2 = "9"

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
            self.N_R1, self.N_S1, self.CLK1, self.J1, self.N_K1, self.Q1, self.N_Q1, 1
        )
        self._process_flipflop(
            self.N_R2, self.N_S2, self.CLK2, self.J2, self.N_K2, self.Q2, self.N_Q2, 2
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
                nk = self.get(nk_pin)

                if not j and nk:
                    next_q = current_q
                elif not j and not nk:
                    next_q = False
                elif j and nk:
                    next_q = True
                elif j and not nk:
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
