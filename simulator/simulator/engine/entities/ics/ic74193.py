from simulator.engine.entities.base import Component


class IC74193(Component):
    VCC = "16"
    GND = "8"

    P0 = "15"
    MR = "14"
    N_TCD = "13"
    N_TCU = "12"
    N_PL = "11"
    P2 = "10"
    P3 = "9"
    Q3 = "7"
    Q2 = "6"
    CPU = "5"
    CPD = "4"
    Q0 = "3"
    Q1 = "2"
    P1 = "1"

    value: int
    prev_up: bool
    prev_down: bool

    def _init(self):
        self.value = 0
        self.new_value = 0
        self.prev_up = False
        self.prev_down = False

    def get_value(self) -> int:
        d0 = self.get(self.P0)
        d1 = self.get(self.P1)
        d2 = self.get(self.P2)
        d3 = self.get(self.P3)
        return (d3 << 3) | (d2 << 2) | (d1 << 1) | d0

    def set_value(self, value: int):
        self.value = value & 0x0F  # 4 bits
        d0 = (self.value >> 0) & 1
        d1 = (self.value >> 1) & 1
        d2 = (self.value >> 2) & 1
        d3 = (self.value >> 3) & 1
        self.set(self.Q0, bool(d0))
        self.set(self.Q1, bool(d1))
        self.set(self.Q2, bool(d2))
        self.set(self.Q3, bool(d3))

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        if self.get(self.MR):  # Clear
            self.set_value(0)
            return

        if not self.get(self.N_PL):  # Load
            self.set_value(self.get_value())
            return

        up = self.get(self.CPU)
        down = self.get(self.CPD)

        value = self.value
        if up and not self.prev_up:
            # Rising edge on UP
            value += 1
        if down and not self.prev_down:
            # Rising edge on DOWN
            value -= 1

        if value > 15:
            self.set(self.N_TCU, False)
        else:
            self.set(self.N_TCU, True)

        if value < 0:
            self.set(self.N_TCD, False)
        else:
            self.set(self.N_TCD, True)

        self.set_value(value)
        self.prev_up = up
        self.prev_down = down
