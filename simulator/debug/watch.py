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
