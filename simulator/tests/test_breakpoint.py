"""
Tests for the BreakpointManager class.
"""

import pytest

from debug.breakpoint import Breakpoint, BreakpointManager


class TestBreakpoint:
    """Tests for the Breakpoint dataclass."""

    def test_breakpoint_creation(self):
        """Test basic breakpoint creation."""
        bp = Breakpoint(id=1, address=0x100)
        assert bp.id == 1
        assert bp.address == 0x100
        assert bp.enabled is True
        assert bp.hit_count == 0
        assert bp.condition is None

    def test_breakpoint_with_condition(self):
        """Test breakpoint with conditional expression."""
        bp = Breakpoint(id=2, address=0x200, condition="x > 10")
        assert bp.condition == "x > 10"

    def test_breakpoint_string_representation_enabled(self):
        """Test string output for enabled breakpoint."""
        bp = Breakpoint(id=1, address=0x100, enabled=True, hit_count=5)
        str_repr = str(bp)
        assert "#1" in str_repr
        assert "0x0100" in str_repr
        assert "hits: 5" in str_repr

    def test_breakpoint_string_representation_disabled(self):
        """Test string output for disabled breakpoint."""
        bp = Breakpoint(id=1, address=0x100, enabled=False)
        str_repr = str(bp)
        assert "#1" in str_repr
        # Should contain gray circle marker for disabled
        assert "0x0100" in str_repr

    def test_breakpoint_string_with_condition(self):
        """Test string output includes condition."""
        bp = Breakpoint(id=3, address=0x300, condition="pc == 0x100")
        str_repr = str(bp)
        assert "if pc == 0x100" in str_repr


class TestBreakpointManager:
    """Tests for the BreakpointManager class."""

    def test_add_breakpoint(self, breakpoint_manager):
        """Test adding a breakpoint."""
        bp = breakpoint_manager.add(0x100)
        assert bp.id == 1
        assert bp.address == 0x100
        assert bp.enabled is True

    def test_add_multiple_breakpoints_unique_ids(self, breakpoint_manager):
        """Test that each breakpoint gets a unique ID."""
        bp1 = breakpoint_manager.add(0x100)
        bp2 = breakpoint_manager.add(0x200)
        bp3 = breakpoint_manager.add(0x300)

        assert bp1.id == 1
        assert bp2.id == 2
        assert bp3.id == 3

    def test_add_breakpoint_with_condition(self, breakpoint_manager):
        """Test adding a conditional breakpoint."""
        bp = breakpoint_manager.add(0x100, condition="x > 5")
        assert bp.condition == "x > 5"

    def test_remove_breakpoint(self, breakpoint_manager):
        """Test removing a breakpoint."""
        bp = breakpoint_manager.add(0x100)
        result = breakpoint_manager.remove(bp.id)
        assert result is True
        assert breakpoint_manager.list_all() == []

    def test_remove_nonexistent_breakpoint(self, breakpoint_manager):
        """Test removing a breakpoint that doesn't exist."""
        result = breakpoint_manager.remove(999)
        assert result is False

    def test_enable_breakpoint(self, breakpoint_manager):
        """Test enabling a breakpoint."""
        bp = breakpoint_manager.add(0x100)
        breakpoint_manager.disable(bp.id)
        assert bp.enabled is False

        result = breakpoint_manager.enable(bp.id)
        assert result is True
        assert bp.enabled is True

    def test_enable_nonexistent_breakpoint(self, breakpoint_manager):
        """Test enabling a nonexistent breakpoint."""
        result = breakpoint_manager.enable(999)
        assert result is False

    def test_disable_breakpoint(self, breakpoint_manager):
        """Test disabling a breakpoint."""
        bp = breakpoint_manager.add(0x100)
        result = breakpoint_manager.disable(bp.id)
        assert result is True
        assert bp.enabled is False

    def test_disable_nonexistent_breakpoint(self, breakpoint_manager):
        """Test disabling a nonexistent breakpoint."""
        result = breakpoint_manager.disable(999)
        assert result is False

    def test_check_breakpoint_hit(self, breakpoint_manager):
        """Test checking if a breakpoint is hit."""
        bp = breakpoint_manager.add(0x100)

        result = breakpoint_manager.check(0x100)
        assert result is not None
        assert result.id == bp.id
        assert result.hit_count == 1

    def test_check_breakpoint_hit_increments_count(self, breakpoint_manager):
        """Test that hit count increments on each check."""
        bp = breakpoint_manager.add(0x100)

        breakpoint_manager.check(0x100)
        breakpoint_manager.check(0x100)
        breakpoint_manager.check(0x100)

        assert bp.hit_count == 3

    def test_check_breakpoint_miss(self, breakpoint_manager):
        """Test checking an address without a breakpoint."""
        breakpoint_manager.add(0x100)
        result = breakpoint_manager.check(0x200)
        assert result is None

    def test_check_disabled_breakpoint_not_hit(self, breakpoint_manager):
        """Test that disabled breakpoints are not triggered."""
        bp = breakpoint_manager.add(0x100)
        breakpoint_manager.disable(bp.id)

        result = breakpoint_manager.check(0x100)
        assert result is None

    def test_list_all_breakpoints(self, breakpoint_manager):
        """Test listing all breakpoints."""
        bp1 = breakpoint_manager.add(0x100)
        bp2 = breakpoint_manager.add(0x200)
        bp3 = breakpoint_manager.add(0x300)

        all_bps = breakpoint_manager.list_all()
        assert len(all_bps) == 3
        assert bp1 in all_bps
        assert bp2 in all_bps
        assert bp3 in all_bps

    def test_list_all_empty(self, breakpoint_manager):
        """Test listing when no breakpoints exist."""
        assert breakpoint_manager.list_all() == []

    def test_clear_all_breakpoints(self, breakpoint_manager):
        """Test clearing all breakpoints."""
        breakpoint_manager.add(0x100)
        breakpoint_manager.add(0x200)
        breakpoint_manager.add(0x300)

        count = breakpoint_manager.clear_all()
        assert count == 3
        assert breakpoint_manager.list_all() == []

    def test_clear_all_empty(self, breakpoint_manager):
        """Test clearing when no breakpoints exist."""
        count = breakpoint_manager.clear_all()
        assert count == 0

    def test_address_index_updated_on_add(self, breakpoint_manager):
        """Test that address index is updated when adding."""
        bp = breakpoint_manager.add(0x100)
        assert breakpoint_manager._address_index.get(0x100) == bp.id

    def test_address_index_updated_on_remove(self, breakpoint_manager):
        """Test that address index is updated when removing."""
        bp = breakpoint_manager.add(0x100)
        breakpoint_manager.remove(bp.id)
        assert 0x100 not in breakpoint_manager._address_index

    def test_add_breakpoint_same_address_overwrites(self, breakpoint_manager):
        """Test adding breakpoint at same address behavior."""
        bp1 = breakpoint_manager.add(0x100)
        bp2 = breakpoint_manager.add(0x100)

        # Both breakpoints should exist (different IDs)
        assert bp1.id != bp2.id
        # But address index should point to latest
        assert breakpoint_manager._address_index.get(0x100) == bp2.id

    def test_id_counter_persistence_after_remove(self, breakpoint_manager):
        """Test that ID counter doesn't reset after removing breakpoints."""
        bp1 = breakpoint_manager.add(0x100)
        bp2 = breakpoint_manager.add(0x200)
        breakpoint_manager.remove(bp1.id)
        breakpoint_manager.remove(bp2.id)

        bp3 = breakpoint_manager.add(0x300)
        assert bp3.id == 3  # Should be 3, not 1
