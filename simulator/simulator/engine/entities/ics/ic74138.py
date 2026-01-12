from simulator.engine.entities.base import Component


class IC74138(Component):
    VCC = "16"
    GND = "8"

    A0 = "1"
    A1 = "2"
    A2 = "3"
    N_E0 = "4"
    N_E1 = "5"
    E2 = "6"
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
            self.get(self.E2)
            and (not self.get(self.N_E0))
            and (not self.get(self.N_E1))
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
        if self.get(self.A2):
            idx += 4
        if self.get(self.A1):
            idx += 2
        if self.get(self.A0):
            idx += 1

        for i, pin in enumerate(outputs):
            if i == idx:
                self.set(pin, False)
            else:
                self.set(pin, True)
