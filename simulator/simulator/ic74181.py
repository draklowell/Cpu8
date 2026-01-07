from simulator.base import Component

class IC74181(Component):
    VCC = "24"
    GND = "12"

    # active HIGH inputs
    A0="2"
    A1="23"
    A2="21"
    A3="19"
    B0="1"
    B1="22"
    B2="20"
    B3="18"
    
    # selection
    S0="6" 
    S1="5"
    S2="4"
    S3="3"
    M="8"   # Mode: H=Logic, L=Arithmetic
    CN="7"  # Carry In (Active LOW)

    # outputs
    F0="9" 
    F1="10" 
    F2="11"
    F3="13"
    AEQB="14" # A=B
    P="15"    # Carry Propagate 
    G="17"    # Carry Generate
    CN4="16"  # Carry Out (Active LOW)

    def _get_input_A(self):
        val = 0
        if self.get(self.A0): 
            val |= 1
        if self.get(self.A1): 
            val |= 2
        if self.get(self.A2): 
            val |= 4
        if self.get(self.A3): 
            val |= 8
        return val

    def _get_input_B(self):
        val = 0
        if self.get(self.B0): 
            val |= 1
        if self.get(self.B1): 
            val |= 2
        if self.get(self.B2): 
            val |= 4
        if self.get(self.B3): 
            val |= 8
        return val

    def _get_select(self):
        val = 0
        if self.get(self.S0): 
            val |= 1
        if self.get(self.S1): 
            val |= 2
        if self.get(self.S2): 
            val |= 4
        if self.get(self.S3): 
            val |= 8
        return val

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            self.log("Not powered")
            return

        a = self._get_input_A()
        b = self._get_input_B()
        s = self._get_select()
        m = self.get(self.M)   # High = Logic, Low = Arithmetic

        c_in = 1 if not self.get(self.CN) else 0

        result = 0
        carry_out = False

        if m:
            # logic mode
            # no carry in this mode
            carry_out = False 

            # тут ніхуя не перевіряв, мені чатік таке дав
            logic_ops = [
                lambda: ~a,              # S=0:  NOT A
                lambda: ~(a | b),        # S=1:  NOR
                lambda: (~a) & b,        # S=2:  (NOT A) AND B
                lambda: 0,               # S=3:  Logic 0
                lambda: ~(a & b),        # S=4:  NAND
                lambda: ~b,              # S=5:  NOT B
                lambda: a ^ b,           # S=6:  XOR
                lambda: a & (~b),        # S=7:  A AND (NOT B)
                lambda: (~a) | b,        # S=8:  (NOT A) OR B
                lambda: ~(a ^ b),        # S=9:  XNOR
                lambda: b,               # S=10: B
                lambda: a & b,           # S=11: AND
                lambda: 0xF,             # S=12: Logic 1 (All High)
                lambda: a | (~b),        # S=13: A OR (NOT B)
                lambda: a | b,           # S=14: OR
                lambda: a                # S=15: A
            ]
            result = logic_ops[s]() & 0xF

        else:
            # arithmetic mode
            ab_and = a & b
            ab_or = a | b
            ab_not_b = a & (~b)

            arith_ops = [
                lambda: a,                     # S=0:  A
                lambda: ab_or,                 # S=1:  A + B (Logical OR sum)
                lambda: a | (~b),              # S=2:  A + (NOT B)
                lambda: -1,                    # S=3:  Minus 1 (0xFF..F)
                lambda: a + (a & (~b)),        # S=4:  A plus (A AND NOT B)
                lambda: (a | b) + (a & (~b)),  # S=5:  (A OR B) plus (A AND NOT B)
                lambda: a - b - 1,             # S=6:  A minus B minus 1 (SUB)
                lambda: (a & (~b)) - 1,        # S=7:  (A AND NOT B) minus 1
                lambda: a + ab_and,            # S=8:  A plus (A AND B)
                lambda: a + b,                 # S=9:  A plus B (ADD)
                lambda: (a | (~b)) + ab_and,   # S=10: (A OR NOT B) plus (A AND B)
                lambda: ab_and - 1,            # S=11: (A AND B) minus 1
                lambda: a + a,                 # S=12: A plus A (SHIFT LEFT)
                lambda: (a | b) + a,           # S=13: (A OR B) plus A
                lambda: (a | (~b)) + a,        # S=14: (A OR NOT B) plus A
                lambda: a - 1                  # S=15: A minus 1
            ]

            val = arith_ops[s]() + c_in

            if val > 15 or val < 0:
                carry_out = True
            
            result = val & 0xF

        # result F0-F3
        self.set(self.F0, bool(result & 1))
        self.set(self.F1, bool((result >> 1) & 1))
        self.set(self.F2, bool((result >> 2) & 1))
        self.set(self.F3, bool((result >> 3) & 1))

        # if carry_out=True -> pin Low
        self.set(self.CN4, not carry_out)


        # A=B. тут ситуація наступна
        # згідно даташіту: A=B високий, тільки якщо всі виходи F=1
        # це працює як компаратор рівності A=B тільки в режимі віднімання (S=6) з Open Collector логікою,
        # але фізично пін просто перевіряє, чи F == 15 (0xF).
        self.set(self.AEQB, result == 0xF)

        self.set(self.G, True) 
        self.set(self.P, True)