"""
Tests for the DebuggerCLI class - the main GDB-style interface.
This tests command parsing, aliases, and output formatting.
"""

import io
import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDebuggerCLIAliases:
    """Tests for command aliases."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore, patch(
            "debugger.SimulationEngine"
        ):

            # Create mock state
            mock_state = MagicMock()
            mock_state.pc = 0x100
            mock_state.sp = 0x1FF
            mock_state.cycle = 0
            mock_state.halted = False
            mock_state.mnemonic = "NOP"
            mock_state.instruction = 0x00
            mock_state.xh = 0
            mock_state.xl = 0
            mock_state.yh = 0
            mock_state.yl = 0
            mock_state.zh = 0
            mock_state.zl = 0
            mock_state.flags = 0

            # Mock disassembler
            mock_disasm = MagicMock()
            mock_disasm.disassemble_at.return_value = ("NOP", 1, bytes([0x00]))
            mock_disasm.disassemble_range.return_value = []

            # Setup mock core
            mock_core = MagicMock()
            mock_core.state = mock_state
            mock_core.disasm = mock_disasm
            mock_core.initialized = True
            mock_core.rom = bytes([0x00] * 256)
            mock_core.rom_path = "/test/rom.bin"
            mock_core.period = 800
            mock_core.breakpoints = MagicMock()
            mock_core.breakpoints.list_all.return_value = []
            mock_core.breakpoints._address_index = {}
            mock_core.watches = MagicMock()
            mock_core.watches.list_all.return_value = []
            mock_core.instruction_history = []

            MockCore.return_value = mock_core

            # Create temporary ROM file
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

    def test_alias_n_to_nexti(self, mock_cli):
        """Test 'n' is aliased to 'nexti'."""
        result = mock_cli.precmd("n")
        assert result == "nexti"

    def test_alias_ni_to_nexti(self, mock_cli):
        """Test 'ni' is aliased to 'nexti'."""
        result = mock_cli.precmd("ni")
        assert result == "nexti"

    def test_alias_c_to_continue(self, mock_cli):
        """Test 'c' is aliased to 'continue'."""
        result = mock_cli.precmd("c")
        assert result == "continue"

    def test_alias_r_to_run(self, mock_cli):
        """Test 'r' is aliased to 'run'."""
        result = mock_cli.precmd("r")
        assert result == "run"

    def test_alias_q_to_quit(self, mock_cli):
        """Test 'q' is aliased to 'quit'."""
        result = mock_cli.precmd("q")
        assert result == "quit"

    def test_alias_p_to_print(self, mock_cli):
        """Test 'p' is aliased to 'print'."""
        result = mock_cli.precmd("p pc")
        assert result == "print pc"

    def test_alias_x_to_examine(self, mock_cli):
        """Test 'x' is aliased to 'examine'."""
        result = mock_cli.precmd("x 0x100")
        assert result == "examine 0x100"

    def test_alias_i_to_info(self, mock_cli):
        """Test 'i' is aliased to 'info'."""
        result = mock_cli.precmd("i registers")
        assert result == "info registers"

    def test_alias_b_to_break(self, mock_cli):
        """Test 'b' is aliased to 'break'."""
        result = mock_cli.precmd("b 0x100")
        assert result == "break 0x100"

    def test_alias_d_to_delete(self, mock_cli):
        """Test 'd' is aliased to 'delete'."""
        result = mock_cli.precmd("d 1")
        assert result == "delete 1"

    def test_alias_bt_to_backtrace(self, mock_cli):
        """Test 'bt' is aliased to 'backtrace'."""
        result = mock_cli.precmd("bt")
        assert result == "backtrace"

    def test_alias_l_to_list(self, mock_cli):
        """Test 'l' is aliased to 'list'."""
        result = mock_cli.precmd("l")
        assert result == "list"

    def test_alias_dis_to_disassemble(self, mock_cli):
        """Test 'dis' is aliased to 'disassemble'."""
        result = mock_cli.precmd("dis 0x100")
        assert result == "disassemble 0x100"

    def test_alias_t_to_tick(self, mock_cli):
        """Test 't' is aliased to 'tick'."""
        result = mock_cli.precmd("t 100")
        assert result == "tick 100"

    def test_alias_s_to_step(self, mock_cli):
        """Test 's' is aliased to 'step'."""
        result = mock_cli.precmd("s")
        assert result == "step"

    def test_alias_si_to_stepi(self, mock_cli):
        """Test 'si' is aliased to 'stepi'."""
        result = mock_cli.precmd("si")
        assert result == "stepi"

    def test_no_alias_passthrough(self, mock_cli):
        """Test commands without aliases pass through."""
        result = mock_cli.precmd("reset")
        assert result == "reset"

    def test_alias_with_format_specifier(self, mock_cli):
        """Test alias with GDB-style format specifier."""
        result = mock_cli.precmd("x/16b 0x100")
        assert result == "examine/16b 0x100"

    def test_empty_line(self, mock_cli):
        """Test empty line handling."""
        result = mock_cli.precmd("")
        assert result == ""


class TestDebuggerCLIBreakCommand:
    """Tests for break command."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore:
            mock_core = MagicMock()
            mock_core.breakpoints = MagicMock()
            mock_bp = MagicMock()
            mock_bp.id = 1
            mock_core.breakpoints.add.return_value = mock_bp

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

    def test_break_hex_address(self, mock_cli, capsys):
        """Test setting breakpoint with hex address."""
        mock_cli.do_break("0x100")
        mock_cli.debugger.breakpoints.add.assert_called_once_with(0x100)

    def test_break_decimal_address(self, mock_cli, capsys):
        """Test setting breakpoint with decimal address."""
        mock_cli.do_break("256")
        mock_cli.debugger.breakpoints.add.assert_called_once_with(256)

    def test_break_no_address(self, mock_cli, capsys):
        """Test break command without address shows usage."""
        mock_cli.do_break("")
        captured = capsys.readouterr()
        assert "Usage" in captured.out or "break" in captured.out.lower()

    def test_break_invalid_address(self, mock_cli, capsys):
        """Test break command with invalid address."""
        mock_cli.do_break("invalid")
        captured = capsys.readouterr()
        assert "Invalid" in captured.out or "Error" in captured.out


class TestDebuggerCLIPrintCommand:
    """Tests for print command."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore:
            mock_core = MagicMock()
            mock_core.get_register_value.return_value = 0x1234

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

    def test_print_register(self, mock_cli, capsys):
        """Test printing a register value."""
        mock_cli.do_print("pc")
        mock_cli.debugger.get_register_value.assert_called_once_with("pc")
        captured = capsys.readouterr()
        assert "0x1234" in captured.out

    def test_print_register_with_dollar(self, mock_cli, capsys):
        """Test printing register with $ prefix."""
        mock_cli.do_print("$sp")
        mock_cli.debugger.get_register_value.assert_called_once_with("sp")

    def test_print_no_argument(self, mock_cli, capsys):
        """Test print with no argument shows usage."""
        mock_cli.do_print("")
        captured = capsys.readouterr()
        assert "Usage" in captured.out or "print" in captured.out.lower()

    def test_print_unknown_register(self, mock_cli, capsys):
        """Test printing unknown register shows error."""
        mock_cli.debugger.get_register_value.return_value = None
        mock_cli.do_print("unknown")
        captured = capsys.readouterr()
        assert "Unknown" in captured.out or "Error" in captured.out


class TestDebuggerCLIExamineCommand:
    """Tests for examine command."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore:
            mock_core = MagicMock()
            mock_core.read_memory.return_value = bytes([0x00] * 16)
            mock_core.disasm = MagicMock()
            mock_core.disasm.disassemble_range.return_value = [
                (0x100, "NOP", 1, bytes([0x00]))
            ]
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

    def test_examine_hex_address(self, mock_cli, capsys):
        """Test examining memory at hex address."""
        mock_cli.do_examine("0x100")
        mock_cli.debugger.read_memory.assert_called()

    def test_examine_with_format_bytes(self, mock_cli, capsys):
        """Test examine with byte format."""
        mock_cli.do_examine("/16b 0x100")
        mock_cli.debugger.read_memory.assert_called()

    def test_examine_with_format_instructions(self, mock_cli, capsys):
        """Test examine with instruction format."""
        mock_cli.do_examine("/8i 0x100")
        mock_cli.debugger.disasm.disassemble_range.assert_called()

    def test_examine_register_as_address(self, mock_cli, capsys):
        """Test examining memory at register value."""
        mock_cli.debugger.get_register_value.return_value = 0x200
        mock_cli.do_examine("pc")
        mock_cli.debugger.get_register_value.assert_called_with("pc")

    def test_examine_no_argument(self, mock_cli, capsys):
        """Test examine with no argument shows usage."""
        mock_cli.do_examine("")
        captured = capsys.readouterr()
        assert "Usage" in captured.out or "examine" in captured.out.lower()


class TestDebuggerCLIInfoCommand:
    """Tests for info command."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore:
            mock_state = MagicMock()
            mock_state.pc = 0x100
            mock_state.sp = 0x1FF
            mock_state.xh = 0
            mock_state.xl = 0
            mock_state.yh = 0
            mock_state.yl = 0
            mock_state.zh = 0
            mock_state.zl = 0
            mock_state.flags = 0
            mock_state.cycle = 0
            mock_state.halted = False
            mock_state.instruction = 0
            mock_state.mnemonic = "NOP"

            mock_core = MagicMock()
            mock_core.state = mock_state
            mock_core.rom_path = "/test.bin"
            mock_core.rom = bytes([0x00] * 256)
            mock_core.initialized = True
            mock_core.period = 800
            mock_core.breakpoints = MagicMock()
            mock_core.breakpoints.list_all.return_value = []
            mock_core.watches = MagicMock()
            mock_core.watches.list_all.return_value = []
            mock_core.list_components.return_value = ["C1:DECODER1"]

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

    def test_info_registers(self, mock_cli, capsys):
        """Test info registers command."""
        mock_cli.do_info("registers")
        captured = capsys.readouterr()
        assert "PC" in captured.out or "Registers" in captured.out

    def test_info_reg_shorthand(self, mock_cli, capsys):
        """Test info reg shorthand."""
        mock_cli.do_info("reg")
        captured = capsys.readouterr()
        assert "PC" in captured.out or "Registers" in captured.out

    def test_info_breakpoints(self, mock_cli, capsys):
        """Test info breakpoints command."""
        mock_cli.do_info("breakpoints")
        captured = capsys.readouterr()
        assert "Breakpoints" in captured.out or "No breakpoints" in captured.out

    def test_info_watches(self, mock_cli, capsys):
        """Test info watches command."""
        mock_cli.do_info("watches")
        captured = capsys.readouterr()
        assert "Watches" in captured.out or "No watches" in captured.out

    def test_info_program(self, mock_cli, capsys):
        """Test info program command."""
        mock_cli.do_info("program")
        captured = capsys.readouterr()
        assert "Program" in captured.out or "ROM" in captured.out

    def test_info_cpu(self, mock_cli, capsys):
        """Test info cpu command."""
        mock_cli.do_info("cpu")
        captured = capsys.readouterr()
        assert "CPU" in captured.out or "Cycle" in captured.out

    def test_info_no_argument(self, mock_cli, capsys):
        """Test info with no argument shows usage."""
        mock_cli.do_info("")
        captured = capsys.readouterr()
        assert "Usage" in captured.out or "info" in captured.out.lower()

    def test_info_unknown_subcommand(self, mock_cli, capsys):
        """Test info with unknown subcommand."""
        mock_cli.do_info("unknown")
        captured = capsys.readouterr()
        assert "Unknown" in captured.out


class TestDebuggerCLISetCommand:
    """Tests for set command."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore:
            mock_core = MagicMock()
            mock_core.set_period.return_value = None
            mock_core.set_variable.return_value = True

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

    def test_set_disasm_on(self, mock_cli, capsys):
        """Test set disasm on."""
        mock_cli.do_set("disasm on")
        assert mock_cli.show_disasm_on_step is True

    def test_set_disasm_off(self, mock_cli, capsys):
        """Test set disasm off."""
        mock_cli.do_set("disasm off")
        assert mock_cli.show_disasm_on_step is False

    def test_set_context(self, mock_cli, capsys):
        """Test set context."""
        mock_cli.do_set("context 10")
        assert mock_cli.disasm_context == 10

    def test_set_period(self, mock_cli, capsys):
        """Test set period."""
        mock_cli.do_set("period 400")
        mock_cli.debugger.set_period.assert_called_once_with(400)

    def test_set_period_too_small(self, mock_cli, capsys):
        """Test set period with value too small."""
        mock_cli.do_set("period 1")
        captured = capsys.readouterr()
        assert "must be at least" in captured.out

    def test_set_var(self, mock_cli, capsys):
        """Test set var command."""
        mock_cli.do_set("var I:PAD2 CLOCK 1")
        mock_cli.debugger.set_variable.assert_called_once_with("I:PAD2", "CLOCK", 1)

    def test_set_var_missing_args(self, mock_cli, capsys):
        """Test set var with missing arguments."""
        mock_cli.do_set("var I:PAD2")
        captured = capsys.readouterr()
        assert "Usage" in captured.out or "var" in captured.out

    def test_set_no_argument(self, mock_cli, capsys):
        """Test set with no argument shows usage."""
        mock_cli.do_set("")
        captured = capsys.readouterr()
        assert "Usage" in captured.out


class TestDebuggerCLINetworkCommands:
    """Tests for network reading commands (rn, rc, pins, components)."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore:
            mock_core = MagicMock()
            mock_core.initialized = True
            mock_core.expand_network_range.return_value = ["NET0!", "NET1!"]
            mock_core.read_networks_as_binary.return_value = "10"
            mock_core.read_networks_as_int.return_value = 2
            mock_core.get_component_pin.return_value = ("CLOCK!", MagicMock())
            mock_core.get_component_pins.return_value = {"CLOCK": "CLOCK!"}
            mock_core.get_network_state.return_value = MagicMock()
            mock_core.list_components.return_value = ["I:PAD2", "C1:DECODER1"]

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

    def test_rn_single_network(self, mock_cli, capsys):
        """Test rn command with single network."""
        mock_cli.do_rn("TEST!")
        captured = capsys.readouterr()
        assert "Binary" in captured.out or "Network" in captured.out

    def test_rn_range(self, mock_cli, capsys):
        """Test rn command with range."""
        mock_cli.do_rn("NET3 - NET0")
        mock_cli.debugger.expand_network_range.assert_called()

    def test_rn_no_argument(self, mock_cli, capsys):
        """Test rn with no argument shows usage."""
        mock_cli.do_rn("")
        captured = capsys.readouterr()
        assert "Usage" in captured.out

    def test_rc_command(self, mock_cli, capsys):
        """Test rc command."""
        mock_cli.do_rc("I:PAD2 CLOCK")
        mock_cli.debugger.get_component_pin.assert_called_once_with("I:PAD2", "CLOCK")

    def test_rc_no_argument(self, mock_cli, capsys):
        """Test rc with missing arguments."""
        mock_cli.do_rc("")
        captured = capsys.readouterr()
        assert "Usage" in captured.out

    def test_pins_command(self, mock_cli, capsys):
        """Test pins command."""
        mock_cli.do_pins("I:PAD2")
        mock_cli.debugger.get_component_pins.assert_called_once_with("I:PAD2")

    def test_pins_no_argument(self, mock_cli, capsys):
        """Test pins with no argument."""
        mock_cli.do_pins("")
        captured = capsys.readouterr()
        assert "Usage" in captured.out

    def test_components_command(self, mock_cli, capsys):
        """Test components command."""
        mock_cli.do_components("")
        mock_cli.debugger.list_components.assert_called()

    def test_components_with_filter(self, mock_cli, capsys):
        """Test components command with filter."""
        mock_cli.do_components("C1")
        mock_cli.debugger.list_components.assert_called()


class TestDebuggerCLITickAndPeriod:
    """Tests for tick and period commands."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore:
            mock_core = MagicMock()
            mock_core.initialized = True
            mock_core.period = 800
            mock_core.tick_simulator.return_value = MagicMock(logs=[])

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

    def test_tick_default(self, mock_cli, capsys):
        """Test tick with no count."""
        mock_cli.do_tick("")
        mock_cli.debugger.tick_simulator.assert_called_once()

    def test_tick_with_count(self, mock_cli, capsys):
        """Test tick with count."""
        mock_cli.do_tick("10")
        assert mock_cli.debugger.tick_simulator.call_count == 10

    def test_tick_invalid_count(self, mock_cli, capsys):
        """Test tick with invalid count."""
        mock_cli.do_tick("invalid")
        captured = capsys.readouterr()
        assert "Invalid" in captured.out

    def test_period_show(self, mock_cli, capsys):
        """Test period command shows current value."""
        mock_cli.do_period("")
        captured = capsys.readouterr()
        assert "800" in captured.out

    def test_period_set(self, mock_cli, capsys):
        """Test period command sets value."""
        mock_cli.do_period("400")
        mock_cli.debugger.set_period.assert_called_once_with(400)

    def test_period_set_invalid(self, mock_cli, capsys):
        """Test period with invalid value."""
        mock_cli.do_period("invalid")
        captured = capsys.readouterr()
        assert "Invalid" in captured.out


class TestDebuggerCLIQuit:
    """Tests for quit command."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore:
            mock_core = MagicMock()
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

    def test_quit_returns_true(self, mock_cli, capsys):
        """Test quit command returns True to exit."""
        result = mock_cli.do_quit("")
        assert result is True

    def test_eof_returns_true(self, mock_cli, capsys):
        """Test EOF (Ctrl+D) returns True to exit."""
        result = mock_cli.do_EOF("")
        assert result is True


class TestDebuggerCLIEmptyLine:
    """Tests for empty line behavior (repeat last command)."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore:
            mock_state = MagicMock()
            mock_state.pc = 0x100
            mock_state.halted = False
            mock_state.mnemonic = "NOP"
            mock_state.instruction = 0x00
            mock_state.xh = 0
            mock_state.xl = 0
            mock_state.yh = 0
            mock_state.yl = 0
            mock_state.zh = 0
            mock_state.zl = 0
            mock_state.sp = 0x1FF
            mock_state.flags = 0
            mock_state.cycle = 0

            mock_disasm = MagicMock()
            mock_disasm.disassemble_at.return_value = ("NOP", 1, bytes([0x00]))
            mock_disasm.disassemble_range.return_value = []

            mock_core = MagicMock()
            mock_core.state = mock_state
            mock_core.disasm = mock_disasm
            mock_core.initialized = True
            mock_core.step_instruction.return_value = mock_state
            mock_core.breakpoints = MagicMock()
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
                cli.show_disasm_on_step = False  # Suppress output
                yield cli
            finally:
                os.unlink(temp_rom)

    def test_empty_line_repeats_last(self, mock_cli):
        """Test that empty line repeats the last command."""
        mock_cli.lastcmd = "nexti"
        mock_cli.emptyline()
        mock_cli.debugger.step_instruction.assert_called()

    def test_empty_line_no_previous(self, mock_cli):
        """Test empty line with no previous command."""
        mock_cli.lastcmd = ""
        result = mock_cli.emptyline()
        assert result is False
