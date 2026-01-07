from simulator.base import Component


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
