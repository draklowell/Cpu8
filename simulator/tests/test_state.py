"""
Tests for the CPUState class.
"""

import pytest

from debug.state import CPUState


class TestCPUState:
    """Tests for the CPUState dataclass."""

    def test_default_state(self):
        """Test that default state has all zeros."""
        state = CPUState()
        assert state.cycle == 0
        assert state.pc == 0
        assert state.sp == 0
        assert state.instruction == 0
        assert state.mnemonic == "???"
        assert state.ac == 0
        assert state.xh == 0
        assert state.xl == 0
        assert state.yh == 0
        assert state.yl == 0
        assert state.zh == 0
        assert state.zl == 0
        assert state.flags == 0
        assert state.halted is False
        assert state.address_bus == 0
        assert state.data_bus == 0

    def test_custom_state(self, cpu_state):
        """Test state with custom values."""
        assert cpu_state.cycle == 100
        assert cpu_state.pc == 0x0100
        assert cpu_state.sp == 0x01FF
        assert cpu_state.instruction == 0x42
        assert cpu_state.mnemonic == "TEST"
        assert cpu_state.ac == 0x12
        assert cpu_state.xh == 0x34
        assert cpu_state.xl == 0x56
        assert cpu_state.yh == 0x78
        assert cpu_state.yl == 0x9A
        assert cpu_state.zh == 0xBC
        assert cpu_state.zl == 0xDE
        assert cpu_state.flags == 0b10101010
        assert cpu_state.halted is False
        assert cpu_state.address_bus == 0x1234
        assert cpu_state.data_bus == 0xAB

    def test_x_register_combination(self, cpu_state):
        """Test combining XH and XL into 16-bit X register."""
        x = (cpu_state.xh << 8) | cpu_state.xl
        assert x == 0x3456

    def test_y_register_combination(self, cpu_state):
        """Test combining YH and YL into 16-bit Y register."""
        y = (cpu_state.yh << 8) | cpu_state.yl
        assert y == 0x789A

    def test_z_register_combination(self, cpu_state):
        """Test combining ZH and ZL into 16-bit Z register."""
        z = (cpu_state.zh << 8) | cpu_state.zl
        assert z == 0xBCDE

    def test_halted_state(self):
        """Test halted flag."""
        state = CPUState(halted=True)
        assert state.halted is True

    def test_state_is_mutable(self):
        """Test that state can be modified."""
        state = CPUState()
        state.pc = 0x1234
        state.sp = 0x5678
        state.halted = True

        assert state.pc == 0x1234
        assert state.sp == 0x5678
        assert state.halted is True

    def test_copy_state_with_vars(self):
        """Test copying state using vars()."""
        original = CPUState(pc=0x100, sp=0x200, cycle=50)
        copy = CPUState(**vars(original))

        assert copy.pc == original.pc
        assert copy.sp == original.sp
        assert copy.cycle == original.cycle

        # Modify copy, original should be unchanged
        copy.pc = 0x999
        assert original.pc == 0x100

    def test_flags_individual_bits(self):
        """Test accessing individual flag bits."""
        state = CPUState(flags=0b10101010)

        # Check individual bits
        assert (state.flags & 0x01) == 0  # Bit 0
        assert (state.flags & 0x02) != 0  # Bit 1
        assert (state.flags & 0x04) == 0  # Bit 2
        assert (state.flags & 0x08) != 0  # Bit 3
        assert (state.flags & 0x80) != 0  # Bit 7

    def test_max_values(self):
        """Test state with maximum values."""
        state = CPUState(
            pc=0xFFFF,
            sp=0xFFFF,
            instruction=0xFF,
            ac=0xFF,
            xh=0xFF,
            xl=0xFF,
            yh=0xFF,
            yl=0xFF,
            zh=0xFF,
            zl=0xFF,
            flags=0xFF,
            address_bus=0xFFFF,
            data_bus=0xFF,
        )

        assert state.pc == 0xFFFF
        assert state.sp == 0xFFFF
        assert state.instruction == 0xFF
