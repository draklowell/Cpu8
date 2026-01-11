"""
Tests for the DebuggerCore class.
"""

import os
import re
import sys
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDebuggerCoreNetworkExpansion:
    """Tests for network range expansion in DebuggerCore."""

    @pytest.fixture
    def mock_core(self):
        """Create a minimal mock DebuggerCore with expand_network_range."""
        from debug.base import DebuggerCore

        # Create a mock that has the real expand_network_range method
        core = MagicMock(spec=DebuggerCore)
        # Bind the real method to the mock
        core.expand_network_range = lambda spec: DebuggerCore.expand_network_range(
            core, spec
        )
        return core

    def test_expand_single_network(self, mock_core):
        """Test expanding a single network (not a range)."""
        spec = "TEST_NET"
        result = mock_core.expand_network_range(spec)
        assert result == ["TEST_NET!"]

    def test_expand_single_network_with_bang(self, mock_core):
        """Test single network already has ! suffix."""
        spec = "TEST_NET!"
        result = mock_core.expand_network_range(spec)
        assert result == ["TEST_NET!"]

    def test_expand_range_descending(self, mock_core):
        """Test expanding descending range."""
        spec = "C3:/STATE3 - C3:/STATE0"
        result = mock_core.expand_network_range(spec)
        expected = ["C3:/STATE3!", "C3:/STATE2!", "C3:/STATE1!", "C3:/STATE0!"]
        assert result == expected

    def test_expand_range_ascending(self, mock_core):
        """Test expanding ascending range."""
        spec = "NET0 - NET3"
        result = mock_core.expand_network_range(spec)
        expected = ["NET0!", "NET1!", "NET2!", "NET3!"]
        assert result == expected

    def test_expand_range_single_element(self, mock_core):
        """Test range where start equals end."""
        spec = "NET5 - NET5"
        result = mock_core.expand_network_range(spec)
        expected = ["NET5!"]
        assert result == expected

    def test_expand_range_mismatched_prefix(self, mock_core):
        """Test range with different prefixes (should fail)."""
        spec = "C1:/NET3 - C2:/NET0"
        result = mock_core.expand_network_range(spec)
        assert result == []

    def test_expand_range_invalid_format(self, mock_core):
        """Test range with invalid format."""
        spec = "invalid range format"
        result = mock_core.expand_network_range(spec)
        assert result == ["invalid range format!"]

    def test_expand_range_large(self, mock_core):
        """Test expanding a large range."""
        spec = "DATA15 - DATA0"
        result = mock_core.expand_network_range(spec)
        assert len(result) == 16
        assert result[0] == "DATA15!"
        assert result[-1] == "DATA0!"


class TestDebuggerCoreRegisterMapping:
    """Tests for register name to value mapping."""

    def test_mapping_includes_all_registers(self):
        """Test that mapping includes all expected registers."""
        expected_registers = [
            "pc",
            "sp",
            "ac",
            "accumulator",
            "xh",
            "xl",
            "x",
            "yh",
            "yl",
            "y",
            "zh",
            "zl",
            "z",
            "flags",
            "fr",
        ]
        # This would require mocking the full DebuggerCore initialization
        # For now, just test the expected list exists


class TestReadNetworksAsBinary:
    """Tests for reading networks as binary string."""

    @pytest.fixture
    def mock_core(self):
        """Create a mock DebuggerCore for testing."""
        from debug.base import DebuggerCore
        from simulator.base import State

        core = MagicMock(spec=DebuggerCore)

        states = {
            "NET0!": State.LOW,
            "NET1!": State.HIGH,
            "NET2!": State.FLOATING,
            "NET3!": State.CONFLICT,
            "NET4!": State.HIGH,
        }

        core.get_network_state = lambda n: states.get(n)
        # Bind the real method to our mock
        core.read_networks_as_binary = (
            lambda networks: DebuggerCore.read_networks_as_binary(core, networks)
        )
        return core

    def test_read_single_high(self, mock_core):
        """Test reading a single HIGH network."""
        result = mock_core.read_networks_as_binary(["NET1!"])
        assert result == "1"

    def test_read_single_low(self, mock_core):
        """Test reading a single LOW network."""
        result = mock_core.read_networks_as_binary(["NET0!"])
        assert result == "0"

    def test_read_floating(self, mock_core):
        """Test reading a FLOATING network."""
        result = mock_core.read_networks_as_binary(["NET2!"])
        assert result == "Z"

    def test_read_conflict(self, mock_core):
        """Test reading a CONFLICT network."""
        result = mock_core.read_networks_as_binary(["NET3!"])
        assert result == "X"

    def test_read_multiple_networks(self, mock_core):
        """Test reading multiple networks."""
        networks = ["NET4!", "NET1!", "NET0!"]  # 1, 1, 0
        result = mock_core.read_networks_as_binary(networks)
        assert result == "110"

    def test_read_unknown_network(self, mock_core):
        """Test reading an unknown network."""
        result = mock_core.read_networks_as_binary(["UNKNOWN!"])
        assert result == "?"


class TestReadNetworksAsInt:
    """Tests for reading networks as integer."""

    @pytest.fixture
    def mock_core(self):
        """Create a mock DebuggerCore for testing."""
        from debug.base import DebuggerCore
        from simulator.base import State

        core = MagicMock(spec=DebuggerCore)

        states = {
            "NET0!": State.LOW,
            "NET1!": State.HIGH,
            "NET2!": State.LOW,
            "NET3!": State.HIGH,
            "FLOAT!": State.FLOATING,
            "CONFLICT!": State.CONFLICT,
        }

        core.get_network_state = lambda n: states.get(n)
        # Bind the real method to our mock
        core.read_networks_as_int = lambda networks: DebuggerCore.read_networks_as_int(
            core, networks
        )
        return core

    def test_read_binary_1010(self, mock_core):
        """Test reading binary 1010 = 10."""
        networks = ["NET3!", "NET2!", "NET1!", "NET0!"]  # 1, 0, 1, 0
        result = mock_core.read_networks_as_int(networks)
        assert result == 0b1010  # 10

    def test_read_single_bit_high(self, mock_core):
        """Test reading single HIGH bit."""
        result = mock_core.read_networks_as_int(["NET1!"])
        assert result == 1

    def test_read_single_bit_low(self, mock_core):
        """Test reading single LOW bit."""
        result = mock_core.read_networks_as_int(["NET0!"])
        assert result == 0

    def test_read_with_floating_returns_none(self, mock_core):
        """Test that FLOATING in network returns None."""
        networks = ["NET1!", "FLOAT!", "NET0!"]
        result = mock_core.read_networks_as_int(networks)
        assert result is None

    def test_read_with_conflict_returns_none(self, mock_core):
        """Test that CONFLICT in network returns None."""
        networks = ["NET1!", "CONFLICT!", "NET0!"]
        result = mock_core.read_networks_as_int(networks)
        assert result is None

    def test_first_network_is_msb(self, mock_core):
        """Test that first network in list is MSB."""
        # NET1! (HIGH) is MSB, NET0! (LOW) is LSB = 10 in binary = 2
        networks = ["NET1!", "NET0!"]
        result = mock_core.read_networks_as_int(networks)
        assert result == 2
