from simulator.engine.entities.base import Component


class IC74245(Component):
    VCC = "20"
    GND = "10"

    N_CE = "19"
    B = ["18", "17", "16", "15", "14", "13", "12", "11"]
    A = ["2", "3", "4", "5", "6", "7", "8", "9"]
    DIR = "1"

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        if self.get(self.N_CE):
            return

        direction = self.get(self.DIR)
        for a_pin, b_pin in zip(self.A, self.B):
            if direction:  # A to B
                value = self.get(a_pin)
                self.set(b_pin, value)
            else:  # B to A
                value = self.get(b_pin)
                self.set(a_pin, value)
