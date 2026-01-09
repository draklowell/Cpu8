from simulator.engine.entities.base import Component


class IC74138(Component):
    VCC = "16"
    GND = "8"

    A = "1"
    B = "2"
    C = "3"
    G2A = "4"  # active LOW
    G2B = "5"  # active LOW
    G1 = "6"  # active HIGH
    Y0 = "15"
    Y1 = "14"
    Y2 = "13"
    Y3 = "12"
    Y4 = "11"
    Y5 = "10"
    Y6 = "9"
    Y7 = "7"

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        enabled = (
            self.get(self.G1) and (not self.get(self.G2A)) and (not self.get(self.G2B))
        )

        outputs = [
            self.Y0,
            self.Y1,
            self.Y2,
            self.Y3,
            self.Y4,
            self.Y5,
            self.Y6,
            self.Y7,
        ]

        if not enabled:
            # Disable all outputs (set to HIGH)
            for out in outputs:
                self.set(out, True)
            return

        # Determine which output to enable
        idx = 0
        if self.get(self.C):
            idx += 4
        if self.get(self.B):
            idx += 2
        if self.get(self.A):
            idx += 1

        for i, pin in enumerate(outputs):
            if i == idx:
                self.set(pin, False)  # Active LOW
            else:
                self.set(pin, True)
