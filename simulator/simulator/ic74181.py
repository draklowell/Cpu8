from simulator.base import Component


class IC74181(Component):
    VCC = "24"
    GND = "12"

    A = ["2", "23", "21", "19"]
    B = ["1", "22", "20", "18"]
    S = ["6", "5", "4", "3"]
    F = ["9", "10", "11", "13"]
    M = "8"  # Mode: H=Logic, L=Arithmetic
    CN = "7"  # Carry In (Active LOW)

    AEQB = "14"  # A=B not used
    P = "15"  # Carry Propagate not used
    G = "17"  # Carry Generate not used
    CN4 = "16"  # Carry Out (Active LOW)

    def _get(self, pin_list: list[str]) -> int:
        val = 0
        for i, pin in enumerate(pin_list):
            if self.get(pin):
                val |= 1 << i

        return val

    def _get_input_a(self):
        return self._get(self.A)

    def _get_input_b(self):
        return self._get(self.B)

    def _get_select(self):
        return self._get(self.S)

    def _set_output(self, value: int):
        for i, pin in enumerate(self.F):
            self.set(pin, bool(value & (1 << i)))

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        a = self._get_input_a()
        b = self._get_input_b()
        s = self._get_select()
        m = self.get(self.M)

        carry_in = 1 if not self.get(self.CN) else 0

        result = 0
        carry_out = 0

        if m:
            # logic mode
            # no carry in this mode
            carry_out = 0

            logic_ops = [
                lambda: ~a,  # S=0:  NOT A
                lambda: ~(a | b),  # S=1:  NOR
                lambda: (~a) & b,  # S=2:  (NOT A) AND B
                lambda: 0,  # S=3:  Logic 0
                lambda: ~(a & b),  # S=4:  NAND
                lambda: ~b,  # S=5:  NOT B
                lambda: a ^ b,  # S=6:  XOR
                lambda: a & (~b),  # S=7:  A AND (NOT B)
                lambda: (~a) | b,  # S=8:  (NOT A) OR B
                lambda: ~(a ^ b),  # S=9:  XNOR
                lambda: b,  # S=10: B
                lambda: a & b,  # S=11: AND
                lambda: 0xF,  # S=12: Logic 1 (All High)
                lambda: a | (~b),  # S=13: A OR (NOT B)
                lambda: a | b,  # S=14: OR
                lambda: a,  # S=15: A
            ]
            result = logic_ops[s]() & 0xF

        else:
            # arithmetic mode
            ab_and = a & b
            ab_or = a | b

            arith_ops = [
                lambda: a,  # S=0:  A
                lambda: ab_or,  # S=1:  A + B (Logical OR sum)
                lambda: a | (~b),  # S=2:  A + (NOT B)
                lambda: -1,  # S=3:  Minus 1 (0x0F)
                lambda: a + (a & (~b)),  # S=4:  A plus (A AND NOT B)
                lambda: (a | b) + (a & (~b)),  # S=5:  (A OR B) plus (A AND NOT B)
                lambda: a - b - 1,  # S=6:  A minus B minus 1 (SUB)
                lambda: (a & (~b)) - 1,  # S=7:  (A AND NOT B) minus 1
                lambda: a + ab_and,  # S=8:  A plus (A AND B)
                lambda: a + b,  # S=9:  A plus B (ADD)
                lambda: (a | (~b)) + ab_and,  # S=10: (A OR NOT B) plus (A AND B)
                lambda: ab_and - 1,  # S=11: (A AND B) minus 1
                lambda: a + a,  # S=12: A plus A (SHIFT LEFT)
                lambda: (a | b) + a,  # S=13: (A OR B) plus A
                lambda: (a | (~b)) + a,  # S=14: (A OR NOT B) plus A
                lambda: a - 1,  # S=15: A minus 1
            ]

            val = arith_ops[s]() + carry_in

            if val > 15 or val < 0:
                carry_out = 1

            result = val & 0xF

        self._set_output(result)
        self.set(self.CN4, not carry_out)
