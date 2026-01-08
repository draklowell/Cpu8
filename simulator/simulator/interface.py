from typing import Callable

from simulator.base import Component

INTREQ = 0x1
RESET = 0x2
WAIT = 0x4

HALT = 0x1
INTACK = 0x2
MEMREAD = 0x4
MEMWRITE = 0x8


class Interface(Component):
    ADDRESS = [
        "22",
        "23",
        "24",
        "25",
        "26",
        "27",
        "28",
        "29",
        "30",
        "31",
        "32",
        "33",
        "34",
        "35",
        "36",
        "37",
    ]
    DATA = [
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
    ]
    INTREQ = "16"
    RESET = "18"
    N_CLK = "2"
    N_HALT = "14"
    N_INTACK = "17"
    N_MEMREAD = "13"
    N_MEMWRITE = "12"
    N_WAIT = "15"
    GND = ["1", "3", "19", "20", "21", "38"]  # Not used, driven by backplane

    reset: bool
    wait: bool
    clock: bool
    clock_new: bool

    read_callback: Callable[[int], int]
    write_callback: Callable[[int, int], None]

    def _init(self):
        self.reset = False
        self.wait = False
        self.clock = False
        self.clock_new = False
        self.read_callback = lambda address: None
        self.write_callback = lambda address, value: None

    def set_read_callback(self, callback: Callable[[int], int]):
        self.log("Setting read callback")
        self.read_callback = callback

    def set_write_callback(self, callback: Callable[[int, int], None]):
        self.log("Setting write callback")
        self.write_callback = callback

    def set_clock(self, value: bool):
        self.log(f"Setting clock to {'HIGH' if value else 'LOW'}")
        self.clock_new = value

    def set_wait(self, value: bool):
        self.log(f"Setting wait to {'ACTIVE' if value else 'INACTIVE'}")
        self.wait = value

    def set_reset(self, value: bool):
        self.log(f"Setting reset to {'ACTIVE' if value else 'INACTIVE'}")
        self.reset = value

    def get_halt(self) -> bool:
        return not self.get(self.N_HALT)

    def propagate(self):
        # Falling edge: update memory
        if not self.get(self.clock_new) and self.clock:
            address = 0
            for i, pin in enumerate(self.ADDRESS):
                if self.get(pin):
                    address |= 1 << i

            if not self.get(self.N_MEMREAD) and not self.get(self.N_MEMWRITE):
                self.warn("Both MEMREAD and MEMWRITE are active, ignoring")

            if not self.get(self.N_MEMWRITE):
                # Write
                value = 0
                for i, pin in enumerate(self.DATA):
                    if self.get(pin):
                        value |= 1 << i
                self.write_callback(address, value)
            elif not self.get(self.N_MEMREAD):
                # Read
                value = self.read_callback(address)
                if value is None:
                    self.error(f"Illegal memory read at address {address:04X}")

                for i, pin in enumerate(self.DATA):
                    bit = (value >> i) & 1
                    self.set(pin, bool(bit))

        # Temporary
        self.set(self.INTREQ, False)

        self.set(self.RESET, self.reset)
        self.set(self.N_WAIT, not self.wait)
        self.set(self.N_CLK, not self.clock_new)
        self.clock = self.clock_new
