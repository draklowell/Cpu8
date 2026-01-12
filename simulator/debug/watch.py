"""
Watch expressions for the debugger
"""

from dataclasses import dataclass


@dataclass
class Watch:
    """
    Represents a watch expression
    """

    id: int
    expression: str
    last_value: int | None = None


@dataclass
class WatchChange:
    """
    Represents a change in a watch value
    """

    watch: Watch
    old_value: int | None
    new_value: int | None


class WatchManager:
    """
    Manages watch expressions
    """

    def __init__(self) -> None:
        self._watches: dict[int, Watch] = {}
        self._next_id = 1

    def add(self, expression: str) -> Watch:
        """
        Add a watch expression
        """
        watch_curr_id = self._next_id
        self._next_id += 1
        watch = Watch(id=watch_curr_id, expression=expression)
        self._watches[watch_curr_id] = watch
        return watch

    def remove(self, watch_id: int) -> bool:
        """
        Remove a watch expression by ID
        """
        if watch_id in self._watches:
            del self._watches[watch_id]
            return True
        return False

    def list_all(self) -> list[Watch]:
        """
        List all watch expressions
        """
        return list(self._watches.values())

    def check_changes(self, get_value_func: callable) -> list[WatchChange]:
        """
        Check all watches for value changes.

        Args:
            get_value_func: Function that takes expression string and returns value

        Returns:
            List of WatchChange for watches that changed
        """
        changes = []
        for watch in self._watches.values():
            new_value = get_value_func(watch.expression)
            if new_value != watch.last_value:
                changes.append(
                    WatchChange(
                        watch=watch,
                        old_value=watch.last_value,
                        new_value=new_value,
                    )
                )
                watch.last_value = new_value
        return changes
