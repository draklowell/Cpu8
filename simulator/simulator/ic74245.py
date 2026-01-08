from simulator.base import Component


class IC74245(Component):
    VCC = "20"
    OE = "19"
    B = ["18", "17", "16", "15", "14", "13", "12", "11"]
    GND = "10"
    A = ["9", "8", "7", "6", "5", "4", "3", "2"]
    DIR = "1"

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        if self.get(self.OE):
            return

        direction = self.get(self.DIR)
        for a_pin, b_pin in zip(self.A, self.B):
            if direction:  # A to B
                value = self.get(a_pin)
                self.set(b_pin, value)
            else:  # B to A
                value = self.get(b_pin)
                self.set(a_pin, value)
