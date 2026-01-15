"""
Tests for the WatchManager class.
"""

import pytest

from debug.watch import Watch, WatchManager


class TestWatch:
    """Tests for the Watch dataclass."""

    def test_watch_creation(self):
        """Test basic watch creation."""
        watch = Watch(id=1, expression="pc")
        assert watch.id == 1
        assert watch.expression == "pc"
        assert watch.last_value is None

    def test_watch_with_last_value(self):
        """Test watch with a stored last value."""
        watch = Watch(id=2, expression="sp", last_value=0x1FF)
        assert watch.last_value == 0x1FF

    def test_watch_complex_expression(self):
        """Test watch with complex expression."""
        watch = Watch(id=3, expression="(xh << 8) | xl")
        assert watch.expression == "(xh << 8) | xl"


class TestWatchManager:
    """Tests for the WatchManager class."""

    def test_add_watch(self, watch_manager):
        """Test adding a watch expression."""
        watch = watch_manager.add("pc")
        assert watch.id == 1
        assert watch.expression == "pc"

    def test_add_multiple_watches_unique_ids(self, watch_manager):
        """Test that each watch gets a unique ID."""
        w1 = watch_manager.add("pc")
        w2 = watch_manager.add("sp")
        w3 = watch_manager.add("x")

        assert w1.id == 1
        assert w2.id == 2
        assert w3.id == 3

    def test_add_duplicate_expression(self, watch_manager):
        """Test adding the same expression twice creates separate watches."""
        w1 = watch_manager.add("pc")
        w2 = watch_manager.add("pc")

        assert w1.id != w2.id
        assert len(watch_manager.list_all()) == 2

    def test_remove_watch(self, watch_manager):
        """Test removing a watch."""
        watch = watch_manager.add("pc")
        result = watch_manager.remove(watch.id)
        assert result is True
        assert watch_manager.list_all() == []

    def test_remove_nonexistent_watch(self, watch_manager):
        """Test removing a watch that doesn't exist."""
        result = watch_manager.remove(999)
        assert result is False

    def test_remove_one_of_many(self, watch_manager):
        """Test removing one watch from many."""
        w1 = watch_manager.add("pc")
        w2 = watch_manager.add("sp")
        w3 = watch_manager.add("x")

        watch_manager.remove(w2.id)

        remaining = watch_manager.list_all()
        assert len(remaining) == 2
        assert w1 in remaining
        assert w3 in remaining
        assert w2 not in remaining

    def test_list_all_watches(self, watch_manager):
        """Test listing all watches."""
        w1 = watch_manager.add("pc")
        w2 = watch_manager.add("sp")
        w3 = watch_manager.add("flags")

        all_watches = watch_manager.list_all()
        assert len(all_watches) == 3
        assert w1 in all_watches
        assert w2 in all_watches
        assert w3 in all_watches

    def test_list_all_empty(self, watch_manager):
        """Test listing when no watches exist."""
        assert watch_manager.list_all() == []

    def test_id_counter_persistence_after_remove(self, watch_manager):
        """Test that ID counter doesn't reset after removing watches."""
        w1 = watch_manager.add("pc")
        w2 = watch_manager.add("sp")
        watch_manager.remove(w1.id)
        watch_manager.remove(w2.id)

        w3 = watch_manager.add("x")
        assert w3.id == 3  # Should be 3, not 1

    def test_various_expression_types(self, watch_manager):
        """Test various expression formats."""
        expressions = [
            "pc",
            "sp",
            "x",
            "y",
            "z",
            "$pc",
            "flags",
            "xh",
            "xl",
            "accumulator",
        ]

        for expr in expressions:
            watch = watch_manager.add(expr)
            assert watch.expression == expr
