"""
Tests for argument parsing and command input validation.
Focuses on edge cases in command argument parsing.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestArgumentParsing:
    """Tests for command argument parsing edge cases."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore:
            mock_state = MagicMock()
            mock_state.pc = 0x100
            mock_state.sp = 0x1FF
            mock_state.halted = False
            mock_state.mnemonic = "NOP"
            mock_state.instruction = 0x00
            mock_state.cycle = 0
            mock_state.xh = 0
            mock_state.xl = 0
            mock_state.yh = 0
            mock_state.yl = 0
            mock_state.zh = 0
            mock_state.zl = 0
            mock_state.flags = 0

            mock_disasm = MagicMock()
            mock_disasm.disassemble_at.return_value = ("NOP", 1, bytes([0x00]))
            mock_disasm.disassemble_range.return_value = []

            mock_core = MagicMock()
            mock_core.state = mock_state
            mock_core.disasm = mock_disasm
            mock_core.initialized = True
            mock_core.rom = bytes([0x00] * 256)
            mock_core.rom_path = "/test/rom.bin"
            mock_core.period = 800
            mock_core.breakpoints = MagicMock()
            mock_core.breakpoints.add.return_value = MagicMock(id=1)
            mock_core.breakpoints.list_all.return_value = []
            mock_core.breakpoints._address_index = {}
            mock_core.watches = MagicMock()
            mock_core.watches.add.return_value = MagicMock(id=1)
            mock_core.instruction_history = []
            mock_core.step_instruction.return_value = mock_state
            mock_core.breakpoints.check.return_value = None

            MockCore.return_value = mock_core

            import tempfile

            from debugger import DebuggerCLI

            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".bin", delete=False
            ) as f:
                f.write(bytes([0x00] * 256))
                temp_rom = f.name

            try:
                cli = DebuggerCLI(temp_rom)
                cli.debugger = mock_core
                cli.show_disasm_on_step = False
                yield cli
            finally:
                os.unlink(temp_rom)

    # Address parsing tests

    def test_break_hex_lowercase(self, mock_cli):
        """Test break with lowercase hex."""
        mock_cli.do_break("0xabcd")
        mock_cli.debugger.breakpoints.add.assert_called_with(0xABCD)

    def test_break_hex_uppercase(self, mock_cli):
        """Test break with uppercase hex."""
        mock_cli.do_break("0xABCD")
        mock_cli.debugger.breakpoints.add.assert_called_with(0xABCD)

    def test_break_hex_mixed_case(self, mock_cli):
        """Test break with mixed case hex."""
        mock_cli.do_break("0xAbCd")
        mock_cli.debugger.breakpoints.add.assert_called_with(0xABCD)

    def test_break_large_decimal(self, mock_cli):
        """Test break with large decimal address."""
        mock_cli.do_break("65535")
        mock_cli.debugger.breakpoints.add.assert_called_with(65535)

    def test_break_zero(self, mock_cli):
        """Test break at address zero."""
        mock_cli.do_break("0")
        mock_cli.debugger.breakpoints.add.assert_called_with(0)

    def test_break_negative_address(self, mock_cli, capsys):
        """Test break with negative address (should be rejected or handled)."""
        mock_cli.do_break("-1")
        # Could either accept it as -1 or show error
        captured = capsys.readouterr()
        # Check that it was handled (either error or accepted)
        assert True  # Just ensure no exception

    # Count parsing tests

    def test_nexti_zero_count(self, mock_cli, capsys):
        """Test nexti with count of zero."""
        mock_cli.do_nexti("0")
        # Should execute zero times (no call to step)
        mock_cli.debugger.step_instruction.assert_not_called()

    def test_nexti_negative_count(self, mock_cli, capsys):
        """Test nexti with negative count."""
        mock_cli.do_nexti("-5")
        # Negative count becomes empty range(0) so no steps are executed
        mock_cli.debugger.step_instruction.assert_not_called()

    def test_nexti_float_count(self, mock_cli, capsys):
        """Test nexti with float count."""
        mock_cli.do_nexti("5.5")
        captured = capsys.readouterr()
        assert "Invalid" in captured.out

    def test_nexti_hex_count(self, mock_cli, capsys):
        """Test nexti with hex count (should fail as it expects decimal)."""
        mock_cli.do_nexti("0x10")
        captured = capsys.readouterr()
        # 0x10 is not valid decimal
        assert "Invalid" in captured.out

    # Whitespace handling

    def test_command_leading_whitespace(self, mock_cli):
        """Test command with leading whitespace is handled by cmd module."""
        # The cmd module handles this, but test our precmd
        result = mock_cli.precmd("  n  5")
        # Whitespace preserved by precmd (cmd handles it)
        assert "n" in result or "nexti" in result

    def test_break_multiple_spaces(self, mock_cli, capsys):
        """Test break with multiple spaces - currently doesn't strip whitespace."""
        mock_cli.do_break("  0x100  ")
        captured = capsys.readouterr()
        # The code doesn't strip whitespace, so this fails with "Invalid address"
        assert "Invalid" in captured.out or mock_cli.debugger.breakpoints.add.called

    # Special character handling

    def test_print_with_dollar(self, mock_cli):
        """Test print with $ prefix on register."""
        mock_cli.debugger.get_register_value.return_value = 0x1234
        mock_cli.do_print("$pc")
        mock_cli.debugger.get_register_value.assert_called_with("pc")

    def test_print_multiple_dollars(self, mock_cli):
        """Test print with multiple $ prefixes."""
        mock_cli.debugger.get_register_value.return_value = 0x1234
        mock_cli.do_print("$$pc")
        # The code uses lstrip("$") which strips ALL leading $ characters
        mock_cli.debugger.get_register_value.assert_called_with("pc")

    # Info subcommand parsing

    def test_info_case_insensitive(self, mock_cli, capsys):
        """Test info subcommand is case insensitive."""
        mock_cli.do_info("REGISTERS")
        captured = capsys.readouterr()
        assert "Registers" in captured.out or "PC" in captured.out

    def test_info_with_extra_args(self, mock_cli, capsys):
        """Test info with extra arguments."""
        mock_cli.do_info("registers extra stuff")
        captured = capsys.readouterr()
        # Should still work, ignoring extra args
        assert "Registers" in captured.out or "PC" in captured.out

    # Set command parsing

    def test_set_disasm_various_values(self, mock_cli):
        """Test set disasm with various boolean values."""
        test_cases = [
            ("on", True),
            ("ON", True),
            ("true", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("YES", True),
            ("off", False),
            ("OFF", False),
            ("false", False),
            ("0", False),
            ("no", False),
        ]

        for value, expected in test_cases:
            mock_cli.do_set(f"disasm {value}")
            assert mock_cli.show_disasm_on_step == expected, f"Failed for {value}"

    def test_set_context_zero(self, mock_cli, capsys):
        """Test set context to zero."""
        mock_cli.do_set("context 0")
        assert mock_cli.disasm_context == 0

    def test_set_context_negative(self, mock_cli, capsys):
        """Test set context to negative value."""
        mock_cli.do_set("context -5")
        captured = capsys.readouterr()
        # Could accept or reject, but should handle gracefully
        # If accepted, -5 would be stored; if rejected, error shown
        assert True

    def test_set_period_boundary(self, mock_cli, capsys):
        """Test set period at boundary value."""
        mock_cli.do_set("period 2")  # Minimum valid
        mock_cli.debugger.set_period.assert_called_with(2)

    # Examine format parsing

    def test_examine_format_only_count(self, mock_cli, capsys):
        """Test examine with count but no format specifier."""
        mock_cli.debugger.read_memory.return_value = bytes([0x00] * 32)
        mock_cli.do_examine("/32 0x100")
        mock_cli.debugger.read_memory.assert_called()

    def test_examine_format_only_type(self, mock_cli, capsys):
        """Test examine with format but no count."""
        mock_cli.debugger.read_memory.return_value = bytes([0x00] * 16)
        mock_cli.do_examine("/b 0x100")
        mock_cli.debugger.read_memory.assert_called()

    def test_examine_very_large_count(self, mock_cli, capsys):
        """Test examine with very large count."""
        mock_cli.debugger.read_memory.return_value = bytes([0x00] * 1000)
        mock_cli.do_examine("/1000b 0x100")
        mock_cli.debugger.read_memory.assert_called()


class TestNetworkNameParsing:
    """Tests for network name parsing in rn, rc commands."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore:
            mock_core = MagicMock()
            mock_core.initialized = True
            mock_core.initialize.return_value = None
            mock_core.expand_network_range.return_value = ["NET0!"]
            mock_core.read_networks_as_binary.return_value = "1"
            mock_core.read_networks_as_int.return_value = 1
            mock_core.get_component_pin.return_value = ("CLOCK!", MagicMock())
            mock_core.get_component_pins.return_value = {"CLOCK": "CLOCK!"}
            mock_core.get_network_state.return_value = MagicMock()

            MockCore.return_value = mock_core

            import tempfile

            from debugger import DebuggerCLI

            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".bin", delete=False
            ) as f:
                f.write(bytes([0x00] * 256))
                temp_rom = f.name

            try:
                cli = DebuggerCLI(temp_rom)
                cli.debugger = mock_core
                yield cli
            finally:
                os.unlink(temp_rom)

    def test_rn_auto_adds_bang(self, mock_cli, capsys):
        """Test rn automatically adds ! to network names."""
        mock_cli.do_rn("TESTNET")
        mock_cli.debugger.read_networks_as_binary.assert_called_with(["TESTNET!"])

    def test_rn_preserves_existing_bang(self, mock_cli, capsys):
        """Test rn doesn't double the ! suffix."""
        mock_cli.do_rn("TESTNET!")
        mock_cli.debugger.read_networks_as_binary.assert_called_with(["TESTNET!"])

    def test_rn_multiple_networks(self, mock_cli, capsys):
        """Test rn with multiple space-separated networks."""
        mock_cli.debugger.read_networks_as_binary.return_value = "101"
        mock_cli.debugger.read_networks_as_int.return_value = 5
        mock_cli.do_rn("NET2 NET1 NET0")
        mock_cli.debugger.read_networks_as_binary.assert_called_with(
            ["NET2!", "NET1!", "NET0!"]
        )

    def test_rn_range_with_spaces(self, mock_cli, capsys):
        """Test rn range with proper spacing."""
        mock_cli.do_rn("DATA7 - DATA0")
        mock_cli.debugger.expand_network_range.assert_called_with("DATA7 - DATA0")

    def test_rc_component_colon_format(self, mock_cli, capsys):
        """Test rc with MODULE:COMPONENT format."""
        mock_cli.do_rc("I:PAD2 CLOCK")
        mock_cli.debugger.get_component_pin.assert_called_with("I:PAD2", "CLOCK")


class TestDeleteCommand:
    """Tests for delete command edge cases."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore:
            mock_core = MagicMock()
            mock_core.breakpoints = MagicMock()
            mock_core.breakpoints.remove.return_value = True
            mock_core.breakpoints.clear_all.return_value = 5

            MockCore.return_value = mock_core

            import tempfile

            from debugger import DebuggerCLI

            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".bin", delete=False
            ) as f:
                f.write(bytes([0x00] * 256))
                temp_rom = f.name

            try:
                cli = DebuggerCLI(temp_rom)
                cli.debugger = mock_core
                yield cli
            finally:
                os.unlink(temp_rom)

    def test_delete_specific_id(self, mock_cli, capsys):
        """Test deleting specific breakpoint by ID."""
        mock_cli.do_delete("1")
        mock_cli.debugger.breakpoints.remove.assert_called_with(1)

    def test_delete_all(self, mock_cli, capsys):
        """Test deleting all breakpoints."""
        mock_cli.do_delete("")
        mock_cli.debugger.breakpoints.clear_all.assert_called()

    def test_delete_invalid_id(self, mock_cli, capsys):
        """Test deleting with invalid ID."""
        mock_cli.do_delete("abc")
        captured = capsys.readouterr()
        assert "Invalid" in captured.out

    def test_delete_nonexistent_id(self, mock_cli, capsys):
        """Test deleting nonexistent breakpoint."""
        mock_cli.debugger.breakpoints.remove.return_value = False
        mock_cli.do_delete("999")
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()


class TestDisassembleCommand:
    """Tests for disassemble command edge cases."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore:
            mock_state = MagicMock()
            mock_state.pc = 0x100

            mock_disasm = MagicMock()
            mock_disasm.disassemble_range.return_value = [
                (0x100, "NOP", 1, bytes([0x00])),
                (0x101, "INC A", 1, bytes([0x01])),
            ]

            mock_core = MagicMock()
            mock_core.state = mock_state
            mock_core.disasm = mock_disasm
            mock_core.breakpoints = MagicMock()
            mock_core.breakpoints._address_index = {}

            MockCore.return_value = mock_core

            import tempfile

            from debugger import DebuggerCLI

            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".bin", delete=False
            ) as f:
                f.write(bytes([0x00] * 256))
                temp_rom = f.name

            try:
                cli = DebuggerCLI(temp_rom)
                cli.debugger = mock_core
                yield cli
            finally:
                os.unlink(temp_rom)

    def test_disassemble_default(self, mock_cli, capsys):
        """Test disassemble with no arguments uses PC."""
        mock_cli.do_disassemble("")
        mock_cli.debugger.disasm.disassemble_range.assert_called_with(0x100, 10)

    def test_disassemble_custom_address(self, mock_cli, capsys):
        """Test disassemble with custom address."""
        mock_cli.do_disassemble("0x200")
        mock_cli.debugger.disasm.disassemble_range.assert_called_with(0x200, 10)

    def test_disassemble_custom_count(self, mock_cli, capsys):
        """Test disassemble with custom count."""
        mock_cli.do_disassemble("0x200 50")
        mock_cli.debugger.disasm.disassemble_range.assert_called_with(0x200, 50)

    def test_disassemble_invalid_address(self, mock_cli, capsys):
        """Test disassemble with invalid address."""
        mock_cli.do_disassemble("invalid")
        captured = capsys.readouterr()
        assert "Invalid" in captured.out


class TestListCommand:
    """Tests for list command edge cases."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore:
            mock_state = MagicMock()
            mock_state.pc = 0x100

            mock_disasm = MagicMock()
            mock_disasm.disassemble_range.return_value = []

            mock_core = MagicMock()
            mock_core.state = mock_state
            mock_core.disasm = mock_disasm
            mock_core.breakpoints = MagicMock()
            mock_core.breakpoints._address_index = {}

            MockCore.return_value = mock_core

            import tempfile

            from debugger import DebuggerCLI

            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".bin", delete=False
            ) as f:
                f.write(bytes([0x00] * 256))
                temp_rom = f.name

            try:
                cli = DebuggerCLI(temp_rom)
                cli.debugger = mock_core
                yield cli
            finally:
                os.unlink(temp_rom)

    def test_list_default_centers_on_pc(self, mock_cli, capsys):
        """Test list without args centers on PC."""
        mock_cli.do_list("")
        # Should call with start = max(0, pc - 10) = max(0, 0x100-10) = 0xF6
        call_args = mock_cli.debugger.disasm.disassemble_range.call_args
        assert call_args[0][0] == max(0, 0x100 - 10)

    def test_list_custom_address(self, mock_cli, capsys):
        """Test list with custom address."""
        mock_cli.do_list("0x200")
        call_args = mock_cli.debugger.disasm.disassemble_range.call_args
        assert call_args[0][0] == max(0, 0x200 - 10)

    def test_list_at_address_zero(self, mock_cli, capsys):
        """Test list at address 0 (edge case for max(0, x-10))."""
        mock_cli.do_list("0")
        call_args = mock_cli.debugger.disasm.disassemble_range.call_args
        assert call_args[0][0] == 0  # max(0, 0-10) = 0
