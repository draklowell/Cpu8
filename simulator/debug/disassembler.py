"""
Disassembler for ROM instructions
"""


class Disassembler:
    """
    Disassembles ROM into assembly instructions
    """

    def __init__(self, rom: bytes, microcode: dict[int, str]) -> None:
        self.rom = rom
        self.microcode = microcode
        self._cache: dict[int, tuple[str, int, bytes]] = (
            {}
        )  # addr -> (mnemonic, size, bytes)

    def disassemble_at(self, address: int) -> tuple[str, int, bytes]:
        """
        Dissasm the opcode into mnemonic

        Args:
            address (int): The address to disassemble at

        Returns:
            tuple[str, int, bytes]: The mnemonic, size of instruction, and raw bytes
        """
        if address >= len(self.rom):
            return "???", 1, b""

        opcode = self.rom[address]
        mnemonic = self.microcode.get(opcode, f"db 0x{opcode:02X}")

        size = 1
        operand_bytes = bytes([opcode])

        if "[byte]" in mnemonic:
            size = 2
            if address + 1 < len(self.rom):
                operand_bytes = self.rom[address : address + 2]
                byte_val = self.rom[address + 1]
                mnemonic = mnemonic.replace("[byte]", f"0x{byte_val:02X}")
        elif "[word]" in mnemonic:
            size = 3
            if address + 2 < len(self.rom):
                operand_bytes = self.rom[address : address + 3]
                # Big-endian: high byte first, then low byte
                word_val = (self.rom[address + 1] << 8) | self.rom[address + 2]
                mnemonic = mnemonic.replace("[word]", f"0x{word_val:04X}")

        return mnemonic, size, operand_bytes

    def disassemble_range(
        self, start: int, count: int
    ) -> list[tuple[int, str, int, bytes]]:
        """
        Dissasm the range

        Args:
            start (int): The starting address to disassemble
            count (int): The number of instructions to disassemble

        Returns:
            list[tuple[int, str, int, bytes]]: A list of tuples containing the address, mnemonic, size, and raw bytes of each instruction
        """
        result = []
        addr = start
        for _ in range(count):
            if addr >= len(self.rom):
                break
            mnemonic, size, raw_bytes = self.disassemble_at(addr)
            result.append((addr, mnemonic, size, raw_bytes))

            addr += size
        return result
