from collections import deque

from simulator.engine.entities.base import Component


class IC28C256(Component):
    VCC = "28"
    GND = "14"

    A14 = "1"
    A12 = "2"
    A7 = "3"
    A6 = "4"
    A5 = "5"
    A4 = "6"
    A3 = "7"
    A2 = "8"
    A1 = "9"
    A0 = "10"
    A10 = "21"
    A11 = "23"
    A9 = "24"
    A8 = "25"
    A13 = "26"

    D0 = "11"
    D1 = "12"
    D2 = "13"
    D3 = "15"
    D4 = "16"
    D5 = "17"
    D6 = "18"
    D7 = "19"

    # Active LOW
    N_CS = "20"
    N_OE = "22"
    N_WE = "27"

    memory: bytearray

    # Used for pseudo-delay in reading
    # Since 74ls04 has abous 10-15ns delay, we say that one tick is 15ns
    # Thus 150ns delay requires 10 ticks
    # and we will keep history of last 10 values
    # and compute output based on value from 10 ticks ago
    # yet still if OE or CS go high, we tri-state outputs in 3 ticks
    history: deque[int]
    _SIZE = 32768

    def _init(self):
        self.memory = bytearray([0] * self._SIZE)
        self.history = deque(maxlen=10)

    def load_data(self, data: bytes | list[int], offset: int = 0):
        if offset < 0 or offset >= self._SIZE:
            raise ValueError(f"Offset {offset} is out of bounds")

        length = len(data)
        if offset + length > self._SIZE:
            raise ValueError(
                f"Data too long: {length} bytes at offset {offset} exceeds memory size"
            )

        self.memory[offset : offset + length] = data
        self.log(
            f"Loaded {length} bytes. Range: 0x{offset:04X} - 0x{offset+length-1:04X}"
        )

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        if self.get(self.N_CS):
            self.history.append(-1)
            self._process()
            return

        if not self.get(self.N_WE):
            self.error("Write operation is not supported")

            return

        if self.get(self.N_OE):
            self.history.append(-1)
            self._process()
            return

        address = 0
        if self.get(self.A0):
            address |= 1 << 0
        if self.get(self.A1):
            address |= 1 << 1
        if self.get(self.A2):
            address |= 1 << 2
        if self.get(self.A3):
            address |= 1 << 3
        if self.get(self.A4):
            address |= 1 << 4
        if self.get(self.A5):
            address |= 1 << 5
        if self.get(self.A6):
            address |= 1 << 6
        if self.get(self.A7):
            address |= 1 << 7
        if self.get(self.A8):
            address |= 1 << 8
        if self.get(self.A9):
            address |= 1 << 9
        if self.get(self.A10):
            address |= 1 << 10
        if self.get(self.A11):
            address |= 1 << 11
        if self.get(self.A12):
            address |= 1 << 12
        if self.get(self.A13):
            address |= 1 << 13
        if self.get(self.A14):
            address |= 1 << 14

        self.history.append(self.memory[address])
        self._process()

    def _process(self):
        for i in range(len(self.history) - 3):
            if self.history[i] == -1:
                return

        data = self.history[0]

        self.set(self.D0, bool((data >> 0) & 1))
        self.set(self.D1, bool((data >> 1) & 1))
        self.set(self.D2, bool((data >> 2) & 1))
        self.set(self.D3, bool((data >> 3) & 1))
        self.set(self.D4, bool((data >> 4) & 1))
        self.set(self.D5, bool((data >> 5) & 1))
        self.set(self.D6, bool((data >> 6) & 1))
        self.set(self.D7, bool((data >> 7) & 1))
