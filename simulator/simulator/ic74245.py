from base import Component


class IC74245(Component):
    VCC = "20"
<<<<<<< HEAD
    OE = "19"  # inverted
    B1 = "18"
    B2 = "17"
    B3 = "16"
    B4 = "15"
    B5 = "14"
    B6 = "13"
    B7 = "12"
    B8 = "11"
    GND = "10"
    A8 = "9"
    A7 = "8"
    A6 = "7"
    A5 = "6"
    A4 = "5"
    A3 = "4"
    A2 = "3"
    A1 = "2"
=======
    E = "19"
    B = ["18", "17", "16", "15", "14", "13", "12", "11"]
    GND = "10"
    A = ["9", "8", "7", "6", "5", "4", "3", "2"]
>>>>>>> eab687aae74ba02dbbd1c17bab97b44a373973d6
    DIR = "1"

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            # IC is not powered, outputs float
            self.log("Not powered, outputs float")
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
