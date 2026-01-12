"""
Tests for the Disassembler class.
"""

import pytest
from debug.disassembler import Disassembler


class TestDisassembler:
    """Tests for the Disassembler class."""

    def test_disassemble_simple_instruction(self, disassembler):
        """Test disassembling a simple 1-byte instruction."""
        mnemonic, size, raw_bytes = disassembler.disassemble_at(0)
        assert mnemonic == "NOP"
        assert size == 1
        assert raw_bytes == bytes([0x00])

    def test_disassemble_instruction_with_byte_operand(self, disassembler):
        """Test disassembling instruction with [byte] operand."""
        # At offset 3, we have: 0x10, 0x20 -> "LD A, 0x20"
        mnemonic, size, raw_bytes = disassembler.disassemble_at(3)
        assert size == 2
        assert "0x20" in mnemonic
        assert raw_bytes == bytes([0x10, 0x20])

    def test_disassemble_instruction_with_word_operand(self, disassembler):
        """Test disassembling instruction with [word] operand."""
        # At offset 5, we have: 0x20, 0x30, 0x40 -> "JMP 0x3040" (big-endian: high byte first)
        mnemonic, size, raw_bytes = disassembler.disassemble_at(5)
        assert size == 3
        assert "0x3040" in mnemonic  # Big-endian: 0x30 << 8 | 0x40
        assert raw_bytes == bytes([0x20, 0x30, 0x40])

    def test_disassemble_unknown_opcode(self, sample_rom):
        """Test disassembling an unknown opcode."""
        microcode = {0x00: "NOP"}
        disasm = Disassembler(sample_rom, microcode)

        # Opcode 0x01 is not in microcode
        mnemonic, size, raw_bytes = disasm.disassemble_at(1)
        assert "db 0x01" in mnemonic
        assert size == 1

    def test_disassemble_past_rom_end(self, sample_rom, sample_microcode):
        """Test disassembling beyond ROM end."""
        disasm = Disassembler(sample_rom, sample_microcode)

        mnemonic, size, raw_bytes = disasm.disassemble_at(9999)
        assert mnemonic == "???"
        assert size == 1
        assert raw_bytes == b""

    def test_disassemble_range(self, disassembler):
        """Test disassembling a range of instructions."""
        instructions = disassembler.disassemble_range(0, 3)

        assert len(instructions) == 3

        # Check first instruction
        addr, mnemonic, size, raw = instructions[0]
        assert addr == 0
        assert mnemonic == "NOP"

        # Check second instruction
        addr, mnemonic, size, raw = instructions[1]
        assert addr == 1

    def test_disassemble_range_with_variable_sizes(self, disassembler):
        """Test that range handles variable instruction sizes."""
        # Start at 3 where we have 2-byte instruction
        instructions = disassembler.disassemble_range(3, 2)

        # First: 2-byte instruction at 3
        # Second: 3-byte instruction at 5
        assert len(instructions) == 2
        assert instructions[0][0] == 3  # Address
        assert instructions[1][0] == 5  # Address (3 + 2)

    def test_disassemble_range_stops_at_rom_end(self, sample_rom, sample_microcode):
        """Test that range stops when reaching ROM end."""
        disasm = Disassembler(sample_rom, sample_microcode)

        # Try to disassemble 1000 instructions starting near end
        instructions = disasm.disassemble_range(250, 1000)

        # Should stop at ROM end
        assert len(instructions) < 1000

    def test_disassemble_range_empty(self, sample_rom, sample_microcode):
        """Test disassembling zero instructions."""
        disasm = Disassembler(sample_rom, sample_microcode)
        instructions = disasm.disassemble_range(0, 0)
        assert instructions == []

    def test_halt_instruction(self, disassembler):
        """Test disassembling HALT instruction."""
        mnemonic, size, raw_bytes = disassembler.disassemble_at(8)
        assert mnemonic == "HALT"
        assert size == 1


class TestDisassemblerEdgeCases:
    """Edge case tests for Disassembler."""

    def test_empty_rom(self, sample_microcode):
        """Test with empty ROM."""
        disasm = Disassembler(b"", sample_microcode)
        mnemonic, size, raw = disasm.disassemble_at(0)
        assert mnemonic == "???"

    def test_single_byte_rom(self, sample_microcode):
        """Test with single-byte ROM."""
        disasm = Disassembler(bytes([0x00]), sample_microcode)
        mnemonic, size, raw = disasm.disassemble_at(0)
        assert mnemonic == "NOP"

    def test_truncated_word_operand(self):
        """Test instruction with [word] at ROM boundary."""
        # ROM ends before we can read full word operand
        rom = bytes([0x20, 0x30])  # JMP but only 2 bytes
        microcode = {0x20: "JMP [word]"}
        disasm = Disassembler(rom, microcode)

        # Should still return something, even if incomplete
        mnemonic, size, raw = disasm.disassemble_at(0)
        assert size == 3  # Expected size

    def test_truncated_byte_operand(self):
        """Test instruction with [byte] at ROM boundary."""
        rom = bytes([0x10])  # LD A, [byte] but no operand
        microcode = {0x10: "LD A, [byte]"}
        disasm = Disassembler(rom, microcode)

        mnemonic, size, raw = disasm.disassemble_at(0)
        assert size == 2  # Expected size

    def test_empty_microcode(self, sample_rom):
        """Test with empty microcode dictionary."""
        disasm = Disassembler(sample_rom, {})
        mnemonic, size, raw = disasm.disassemble_at(0)
        assert "db 0x00" in mnemonic

    def test_all_opcodes_representable(self, sample_microcode):
        """Test that all 256 possible opcodes can be handled."""
        rom = bytes(range(256))
        disasm = Disassembler(rom, sample_microcode)

        for i in range(256):
            mnemonic, size, raw = disasm.disassemble_at(i)
            assert mnemonic is not None
            assert size >= 1
