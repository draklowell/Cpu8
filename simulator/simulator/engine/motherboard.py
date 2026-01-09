from simulator.engine.entities.base import Messaging
from simulator.engine.entities.cpu import CPU


class Motherboard(Messaging):
    name: str = "Motherboard"
    _rom: bytes
    _rw: bytearray
    _stack: bytearray

    def __init__(self, cpu: CPU):
        self.cpu = cpu
        self.cpu.interface.set_read_callback(self._cb_read)
        self.cpu.interface.set_write_callback(self._cb_write)

        self._rom = bytes(10240)
        self._rw = bytearray(6144)
        self._stack = bytearray(1024)

    def set_rom(self, data: bytes):
        if len(data) < 10240:
            self.warn(
                f"ROM data is smaller than 10KB ({len(data)} bytes), padding with zeros"
            )
            data += bytes(10240 - len(data))
        elif len(data) > 10240:
            self.warn(f"ROM data is larger than 10KB ({len(data)} bytes), truncating")
            data = data[:10240]

        self._rom = data

    def _cb_read(self, address: int) -> int:
        self.log(f"Read from address 0x{address:04X}")

        if address <= 0x2800:
            return self._rom[address]

        if 0x4000 <= address <= 0x5800:
            return self._rw[address - 0x4000]

        if 0xFBFF <= address <= 0xFFFF:
            return self._stack[address - 0xFBFF]

        raise RuntimeError(f"Invalid read address: 0x{address:04X}")

    def _cb_write(self, address: int, value: int) -> None:
        self.log(f"Write to address 0x{address:04X} with value 0x{value:02X}")

        if address <= 0x2800:
            return

        if 0x4000 <= address <= 0x5800:
            self._rw[address - 0x4000] = value
            return

        if 0xFBFF <= address <= 0xFFFF:
            self._stack[address - 0xFBFF] = value
            return

        raise RuntimeError(f"Invalid write address: 0x{address:04X}")

    def propagate(self):
        self.cpu.propagate()
