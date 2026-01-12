from simulator.engine.entities.base import Component


class IC74154(Component):
    VCC = "24"
    GND = "12"

    A0 = "23"
    A1 = "22"
    A2 = "21"
    A3 = "20"

    # both Active LOW
    N_E0 = "18"
    N_E1 = "19"

    # Active LOW
    Y0 = "1"
    Y1 = "2"
    Y2 = "3"
    Y3 = "4"
    Y4 = "5"
    Y5 = "6"
    Y6 = "7"
    Y7 = "8"
    Y8 = "9"
    Y9 = "10"
    Y10 = "11"
    Y11 = "13"
    Y12 = "14"
    Y13 = "15"
    Y14 = "16"
    Y15 = "17"

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        # Enable Logic: G1=Low AND G2=Low
        enabled = (not self.get(self.N_E0)) and (not self.get(self.N_E1))

        outputs = [
            self.Y0,
            self.Y1,
            self.Y2,
            self.Y3,
            self.Y4,
            self.Y5,
            self.Y6,
            self.Y7,
            self.Y8,
            self.Y9,
            self.Y10,
            self.Y11,
            self.Y12,
            self.Y13,
            self.Y14,
            self.Y15,
        ]

        if not enabled:
            for out in outputs:
                self.set(out, True)  # All HIGH
            return

        idx = 0
        if self.get(self.A3):
            idx += 8
        if self.get(self.A2):
            idx += 4
        if self.get(self.A1):
            idx += 2
        if self.get(self.A0):
            idx += 1

        for i, pin in enumerate(outputs):
            self.set(pin, i != idx)  # Selected is False (LOW), others True
