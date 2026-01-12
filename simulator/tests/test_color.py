"""
Tests for the color module.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from debug.color import Color, colored, print_header, print_separator


class TestColor:
    """Tests for the Color class."""

    def test_color_constants_exist(self):
        """Test that all expected color constants exist."""
        assert hasattr(Color, "RED")
        assert hasattr(Color, "GREEN")
        assert hasattr(Color, "YELLOW")
        assert hasattr(Color, "BLUE")
        assert hasattr(Color, "MAGENTA")
        assert hasattr(Color, "CYAN")
        assert hasattr(Color, "WHITE")
        assert hasattr(Color, "GRAY")
        assert hasattr(Color, "BOLD")
        assert hasattr(Color, "RESET")

    def test_color_values_are_strings(self):
        """Test that color values are strings (ANSI codes)."""
        assert isinstance(Color.RED, str)
        assert isinstance(Color.GREEN, str)
        assert isinstance(Color.RESET, str)

    def test_color_values_start_with_escape(self):
        """Test that color values are ANSI escape sequences."""
        assert Color.RED.startswith("\033[") or Color.RED.startswith("\x1b[")
        assert Color.GREEN.startswith("\033[") or Color.GREEN.startswith("\x1b[")

    def test_bright_colors_exist(self):
        """Test that bright color variants exist."""
        assert hasattr(Color, "BRIGHT_RED")
        assert hasattr(Color, "BRIGHT_GREEN")
        assert hasattr(Color, "BRIGHT_CYAN")
        assert hasattr(Color, "BRIGHT_YELLOW")


class TestColoredFunction:
    """Tests for the colored() function."""

    def test_colored_basic(self):
        """Test basic coloring."""
        result = colored("test", Color.RED)
        assert "test" in result
        assert Color.RED in result
        assert Color.RESET in result

    def test_colored_with_bold(self):
        """Test coloring with bold modifier."""
        result = colored("test", Color.GREEN, Color.BOLD)
        assert "test" in result
        assert Color.GREEN in result
        assert Color.BOLD in result
        assert Color.RESET in result

    def test_colored_empty_string(self):
        """Test coloring empty string."""
        result = colored("", Color.RED)
        assert Color.RED in result
        assert Color.RESET in result

    def test_colored_preserves_content(self):
        """Test that colored doesn't alter the text content."""
        original = "Hello, World! 123"
        result = colored(original, Color.BLUE)
        # Strip ANSI codes and verify content
        assert original in result

    def test_colored_multiline(self):
        """Test coloring multiline text."""
        text = "line1\nline2\nline3"
        result = colored(text, Color.YELLOW)
        assert "line1" in result
        assert "line2" in result
        assert "line3" in result

    def test_colored_special_chars(self):
        """Test coloring text with special characters."""
        text = "0x{value:04X} → [test]"
        result = colored(text, Color.CYAN)
        assert text in result


class TestPrintFunctions:
    """Tests for print_header and print_separator functions."""

    def test_print_header_includes_text(self, capsys):
        """Test that print_header includes the header text."""
        print_header("Test Header")
        captured = capsys.readouterr()
        assert "Test Header" in captured.out

    def test_print_header_adds_decoration(self, capsys):
        """Test that print_header adds some decoration."""
        print_header("Test")
        captured = capsys.readouterr()
        # Should have some decoration (═ or similar)
        assert len(captured.out) > len("Test")

    def test_print_separator(self, capsys):
        """Test that print_separator outputs something."""
        print_separator()
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_print_header_empty_string(self, capsys):
        """Test print_header with empty string."""
        print_header("")
        captured = capsys.readouterr()
        # Should still print something (the decoration)
        assert len(captured.out) > 0

    def test_print_header_long_text(self, capsys):
        """Test print_header with very long text."""
        long_text = "A" * 200
        print_header(long_text)
        captured = capsys.readouterr()
        assert long_text in captured.out
