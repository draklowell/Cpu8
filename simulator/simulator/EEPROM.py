from base import Component

class EEPROM(Component):
    VCC = "28"
    GND = "14"

    A14 = "1"
    A12 = "2" 
    A7  = "3"  
    A6  = "4"
    A5  = "5"
    A4  = "6" 
    A3  = "7"
    A2  = "8"
    A1  = "9" 
    A0  = "10" 
    A10 = "21"
    A11 = "23"
    A9  = "24"
    A8  = "25"
    A13 = "26"

    IO0 = "11"
    IO1 = "12"
    IO2 = "13" 
    IO3 = "15"
    IO4 = "16"
    IO5 = "17" 
    IO6 = "18" 
    IO7 = "19"
    
    # Active LOW
    CE = "20"
    OE = "22"
    WE = "27"
    
    memory: bytearray
    SIZE = 32768

    def _init(self):
        self.memory = bytearray([0] * self.SIZE)

    def load_data(self, data: bytes | list[int], offset: int = 0):
        if offset < 0 or offset >= self.SIZE:
            raise ValueError(f"Offset {offset} is out of bounds")
        
        length = len(data)
        if offset + length > self.SIZE:
            raise ValueError(f"Data too long: {length} bytes at offset {offset} exceeds memory size")

        self.memory[offset:offset+length] = data
        self.log(f"Loaded {length} bytes. Range: 0x{offset:04X} - 0x{offset+length-1:04X}")

    def propagate(self):
        if not self.get(self.VCC) or self.get(self.GND):
            return

        if self.get(self.CE):
            return

        if not self.get(self.WE):
             raise RuntimeError(f"[{self.name}] хуй замість запису")

        if not self.get(self.OE):
            address = 0
            if self.get(self.A0):  address |= (1 << 0)
            if self.get(self.A1):  address |= (1 << 1)
            if self.get(self.A2):  address |= (1 << 2)
            if self.get(self.A3):  address |= (1 << 3)
            if self.get(self.A4):  address |= (1 << 4)
            if self.get(self.A5):  address |= (1 << 5)
            if self.get(self.A6):  address |= (1 << 6)
            if self.get(self.A7):  address |= (1 << 7)
            if self.get(self.A8):  address |= (1 << 8)
            if self.get(self.A9):  address |= (1 << 9)
            if self.get(self.A10): address |= (1 << 10)
            if self.get(self.A11): address |= (1 << 11)
            if self.get(self.A12): address |= (1 << 12)
            if self.get(self.A13): address |= (1 << 13)
            if self.get(self.A14): address |= (1 << 14)

            data = self.memory[address]

            self.set(self.IO0, bool((data >> 0) & 1))
            self.set(self.IO1, bool((data >> 1) & 1))
            self.set(self.IO2, bool((data >> 2) & 1))
            self.set(self.IO3, bool((data >> 3) & 1))
            self.set(self.IO4, bool((data >> 4) & 1))
            self.set(self.IO5, bool((data >> 5) & 1))
            self.set(self.IO6, bool((data >> 6) & 1))
            self.set(self.IO7, bool((data >> 7) & 1))