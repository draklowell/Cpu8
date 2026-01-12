"""
Integration tests for the debugger.
These tests require actual simulation infrastructure.
"""

import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestUIStrings:
    """Tests for the UI strings module."""

    def test_ui_strings_import(self):
        """Test that UI strings can be imported."""
        from debug.ui import DebuggerStrings

        strings = DebuggerStrings()
        assert strings is not None

    def test_banner_exists(self):
        """Test that banner string exists and is not empty."""
        from debug.ui import DebuggerStrings

        strings = DebuggerStrings()
        assert strings.ui.BANNER
        assert len(strings.ui.BANNER) > 0

    def test_prompt_exists(self):
        """Test that prompt string exists."""
        from debug.ui import DebuggerStrings

        strings = DebuggerStrings()
        assert strings.ui.PROMPT
        assert "gdb-dragonfly" in strings.ui.PROMPT

    def test_execution_strings(self):
        """Test execution-related strings."""
        from debug.ui import DebuggerStrings

        strings = DebuggerStrings()
        assert strings.execution.STARTING_PROGRAM
        assert strings.execution.CONTINUING
        assert strings.execution.PROGRAM_HALTED

    def test_breakpoint_strings(self):
        """Test breakpoint-related strings."""
        from debug.ui import DebuggerStrings

        strings = DebuggerStrings()
        assert "{id}" in strings.breakpoints.BREAKPOINT_SET
        assert "{address" in strings.breakpoints.BREAKPOINT_SET

    def test_error_strings(self):
        """Test error strings."""
        from debug.ui import DebuggerStrings

        strings = DebuggerStrings()
        assert strings.errors.INVALID_COUNT
        assert "{address}" in strings.errors.INVALID_ADDRESS

    def test_usage_strings(self):
        """Test usage strings."""
        from debug.ui import DebuggerStrings

        strings = DebuggerStrings()
        assert strings.usage.USAGE_EXAMINE
        assert strings.usage.USAGE_INFO
        assert strings.usage.USAGE_BREAK


class TestDebuggerCLIDocstrings:
    """Tests to ensure all commands have proper docstrings."""

    def test_all_do_methods_have_docstrings(self):
        """Test that all do_* methods have docstrings."""
        from debugger import DebuggerCLI

        missing_docstrings = []
        for name in dir(DebuggerCLI):
            if name.startswith("do_") and callable(getattr(DebuggerCLI, name)):
                method = getattr(DebuggerCLI, name)
                if not method.__doc__:
                    missing_docstrings.append(name)

        assert (
            not missing_docstrings
        ), f"Methods without docstrings: {missing_docstrings}"

    def test_docstrings_contain_usage(self):
        """Test that command docstrings contain usage information."""
        from debugger import DebuggerCLI

        # Commands that should have Usage: in docstring
        commands_needing_usage = [
            "do_run",
            "do_nexti",
            "do_continue",
            "do_print",
            "do_examine",
            "do_break",
            "do_delete",
            "do_info",
            "do_rn",
            "do_rc",
            "do_pins",
            "do_components",
            "do_tick",
            "do_period",
            "do_set",
            "do_quit",
        ]

        missing_usage = []
        for cmd_name in commands_needing_usage:
            if hasattr(DebuggerCLI, cmd_name):
                method = getattr(DebuggerCLI, cmd_name)
                if method.__doc__ and "Usage:" not in method.__doc__:
                    missing_usage.append(cmd_name)

        assert not missing_usage, f"Commands without Usage: {missing_usage}"

    def test_docstrings_contain_examples(self):
        """Test that major command docstrings contain examples."""
        from debugger import DebuggerCLI

        # Commands that should have Examples: in docstring
        commands_needing_examples = [
            "do_run",
            "do_nexti",
            "do_continue",
            "do_print",
            "do_examine",
            "do_break",
            "do_rn",
            "do_rc",
        ]

        missing_examples = []
        for cmd_name in commands_needing_examples:
            if hasattr(DebuggerCLI, cmd_name):
                method = getattr(DebuggerCLI, cmd_name)
                if method.__doc__ and "Examples:" not in method.__doc__:
                    missing_examples.append(cmd_name)

        assert not missing_examples, f"Commands without Examples: {missing_examples}"


class TestEdgeCases:
    """Edge case and boundary tests."""

    def test_breakpoint_at_zero_address(self):
        """Test breakpoint at address 0."""
        from debug.breakpoint import BreakpointManager

        bm = BreakpointManager()
        bp = bm.add(0)
        assert bp.address == 0

        hit = bm.check(0)
        assert hit is not None

    def test_breakpoint_at_max_address(self):
        """Test breakpoint at maximum address."""
        from debug.breakpoint import BreakpointManager

        bm = BreakpointManager()
        bp = bm.add(0xFFFF)
        assert bp.address == 0xFFFF

    def test_watch_empty_expression(self):
        """Test watch with empty expression."""
        from debug.watch import WatchManager

        wm = WatchManager()
        # Empty expression should still be storable
        watch = wm.add("")
        assert watch.expression == ""

    def test_watch_special_characters(self):
        """Test watch with special characters in expression."""
        from debug.watch import WatchManager

        wm = WatchManager()
        expressions = [
            "$pc",
            "(xh << 8) | xl",
            "mem[0x100]",
            "flag & 0x01",
        ]

        for expr in expressions:
            watch = wm.add(expr)
            assert watch.expression == expr

    def test_cpu_state_zero_values(self):
        """Test CPU state with all zero values."""
        from debug.state import CPUState

        state = CPUState()
        assert state.pc == 0
        assert state.sp == 0
        assert not state.halted

    def test_disassembler_boundary(self):
        """Test disassembler at ROM boundary."""
        from debug.disassembler import Disassembler

        rom = bytes([0x00] * 10)
        microcode = {0x00: "NOP"}
        disasm = Disassembler(rom, microcode)

        # At boundary
        mnemonic, size, raw = disasm.disassemble_at(9)
        assert mnemonic == "NOP"

        # Past boundary
        mnemonic, size, raw = disasm.disassemble_at(10)
        assert mnemonic == "???"


class TestBugDetection:
    """Tests specifically designed to detect potential bugs."""

    def test_breakpoint_double_remove(self):
        """Test removing the same breakpoint twice."""
        from debug.breakpoint import BreakpointManager

        bm = BreakpointManager()
        bp = bm.add(0x100)

        result1 = bm.remove(bp.id)
        assert result1 is True

        result2 = bm.remove(bp.id)
        assert result2 is False

    def test_breakpoint_enable_disable_cycle(self):
        """Test enable/disable cycle doesn't corrupt state."""
        from debug.breakpoint import BreakpointManager

        bm = BreakpointManager()
        bp = bm.add(0x100)

        for _ in range(10):
            bm.disable(bp.id)
            assert bp.enabled is False
            bm.enable(bp.id)
            assert bp.enabled is True

    def test_watch_remove_middle(self):
        """Test removing watch from middle of list."""
        from debug.watch import WatchManager

        wm = WatchManager()
        w1 = wm.add("pc")
        w2 = wm.add("sp")
        w3 = wm.add("x")

        wm.remove(w2.id)

        remaining = wm.list_all()
        assert len(remaining) == 2
        ids = [w.id for w in remaining]
        assert w1.id in ids
        assert w3.id in ids
        assert w2.id not in ids

    def test_breakpoint_address_collision(self):
        """Test multiple breakpoints at same address."""
        from debug.breakpoint import BreakpointManager

        bm = BreakpointManager()
        bp1 = bm.add(0x100)
        bp2 = bm.add(0x100)  # Same address

        # Both should exist
        all_bps = bm.list_all()
        assert len(all_bps) == 2

        # But check should only return one (the latest)
        hit = bm.check(0x100)
        assert hit is not None
        assert hit.id == bp2.id

    def test_breakpoint_hit_count_accumulation(self):
        """Test hit count accumulates correctly."""
        from debug.breakpoint import BreakpointManager

        bm = BreakpointManager()
        bp = bm.add(0x100)

        for i in range(1, 11):
            hit = bm.check(0x100)
            assert hit.hit_count == i

    def test_disassembler_overlapping_instructions(self):
        """Test disassembly doesn't corrupt on overlapping reads."""
        from debug.disassembler import Disassembler

        rom = bytes([0x20, 0x00, 0x01, 0x00, 0x00])  # JMP [word] then NOPs
        microcode = {0x20: "JMP [word]", 0x00: "NOP", 0x01: "INC"}
        disasm = Disassembler(rom, microcode)

        # Disassemble from 0 (3-byte instruction)
        m1, s1, r1 = disasm.disassemble_at(0)
        assert s1 == 3

        # Disassemble from 1 (middle of previous instruction)
        m2, s2, r2 = disasm.disassemble_at(1)
        # Should still work (it's just NOP at that byte)
        assert m2 is not None

    def test_cpu_state_modification_isolation(self):
        """Test that modifying copied state doesn't affect original."""
        from debug.state import CPUState

        original = CPUState(pc=0x100, sp=0x200)
        copy = CPUState(**vars(original))

        copy.pc = 0x999
        copy.sp = 0x888

        assert original.pc == 0x100
        assert original.sp == 0x200


class TestFormatStateMethod:
    """Tests for the _format_state method in DebuggerCLI."""

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

    def test_format_high_state(self, mock_cli):
        """Test formatting HIGH state."""
        from simulator.base import State

        result = mock_cli._format_state(State.HIGH)
        assert "HIGH" in result or "1" in result

    def test_format_low_state(self, mock_cli):
        """Test formatting LOW state."""
        from simulator.base import State

        result = mock_cli._format_state(State.LOW)
        assert "LOW" in result or "0" in result

    def test_format_floating_state(self, mock_cli):
        """Test formatting FLOATING state."""
        from simulator.base import State

        result = mock_cli._format_state(State.FLOATING)
        assert "FLOATING" in result or "Z" in result

    def test_format_conflict_state(self, mock_cli):
        """Test formatting CONFLICT state."""
        from simulator.base import State

        result = mock_cli._format_state(State.CONFLICT)
        assert "CONFLICT" in result or "X" in result

    def test_format_none_state(self, mock_cli):
        """Test formatting None state."""
        result = mock_cli._format_state(None)
        assert "UNKNOWN" in result or "?" in result


class TestExamineMemoryFormats:
    """Tests for examine memory format parsing."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore:
            mock_core = MagicMock()
            mock_core.read_memory.return_value = bytes([0xAB, 0xCD] * 16)
            mock_core.get_register_value.return_value = 0x100
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

    def test_examine_default_format(self, mock_cli, capsys):
        """Test examine with default format."""
        mock_cli.do_examine("0x100")
        mock_cli.debugger.read_memory.assert_called()

    def test_examine_byte_format(self, mock_cli, capsys):
        """Test examine with /b format."""
        mock_cli.do_examine("/8b 0x100")
        mock_cli.debugger.read_memory.assert_called_with(0x100, 8)

    def test_examine_halfword_format(self, mock_cli, capsys):
        """Test examine with /h format."""
        mock_cli.do_examine("/4h 0x100")
        mock_cli.debugger.read_memory.assert_called()

    def test_examine_word_format(self, mock_cli, capsys):
        """Test examine with /w format."""
        mock_cli.do_examine("/2w 0x100")
        mock_cli.debugger.read_memory.assert_called()

    def test_examine_instruction_format(self, mock_cli, capsys):
        """Test examine with /i format."""
        mock_cli.do_examine("/10i 0x100")
        mock_cli.debugger.disasm.disassemble_range.assert_called_with(0x100, 10)

    def test_examine_register_address(self, mock_cli, capsys):
        """Test examine using register as address."""
        mock_cli.do_examine("/16b pc")
        mock_cli.debugger.get_register_value.assert_called_with("pc")


class TestCommandHistory:
    """Tests for command history and execution."""

    @pytest.fixture
    def mock_cli(self):
        """Create a DebuggerCLI with mocked dependencies."""
        with patch("debugger.DebuggerCore") as MockCore:
            mock_state = MagicMock()
            mock_state.pc = 0
            mock_state.halted = False
            mock_state.mnemonic = "NOP"
            mock_state.instruction = 0
            mock_state.cycle = 0
            mock_state.sp = 0
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
            mock_core.instruction_history = [
                MagicMock(cycle=1, pc=0, mnemonic="NOP"),
                MagicMock(cycle=2, pc=1, mnemonic="INC"),
                MagicMock(cycle=3, pc=2, mnemonic="DEC"),
            ]

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

    def test_backtrace_shows_history(self, mock_cli, capsys):
        """Test backtrace command shows history."""
        mock_cli.do_backtrace("")
        captured = capsys.readouterr()
        assert "History" in captured.out or "cycle" in captured.out

    def test_backtrace_with_count(self, mock_cli, capsys):
        """Test backtrace with count argument."""
        mock_cli.do_backtrace("2")
        captured = capsys.readouterr()
        # Should show limited history
        assert "History" in captured.out or "cycle" in captured.out
