"""
Breakpoint management for the debugger
"""

from dataclasses import dataclass

from debug.color import Color, colored


@dataclass
class Breakpoint:
    """
    Represents a breakpoint in the debugger
    """

    id: int
    address: int
    enabled: bool = True
    hit_count: int = 0
    condition: str | None = None

    def __str__(self) -> str:
        status = colored("●", Color.GREEN) if self.enabled else colored("○", Color.GRAY)
        cond = f" if {self.condition}" if self.condition else ""
        return (
            f"{status} #{self.id}: 0x{self.address:04X}{cond} (hits: {self.hit_count})"
        )


class BreakpointManager:
    """
    Manages breakpoints for the debugger
    """

    def __init__(self):
        self._breakpoints: dict[int, Breakpoint] = {}
        self._next_id = 1
        self._address_index: dict[int, int] = {}  # address -> bp_id

    def _check_breakpoint(self, breakpoint_id: int) -> Breakpoint | None:
        """
        Helper function to check if bp in avaliable breakpoints

        Args:
            breakpoint_id (int): The ID of the breakpoint to check

        Returns:
            Breakpoint | None: The breakpoint if found None otherwise
        """

        return True if breakpoint_id in self._breakpoints else False

    def add(self, address: int, condition: str | None = None) -> Breakpoint:
        """
        Set break point

        Args:
            address (int): The address to set the breakpoint at
            condition (str | None, optional): The condition for the breakpoint. Defaults to None.

        Returns:
            Breakpoint: The created breakpoint instance
        """
        breakp_id = self._next_id
        self._next_id += 1
        bp = Breakpoint(id=breakp_id, address=address, condition=condition)
        self._breakpoints[breakp_id] = bp
        self._address_index[address] = breakp_id
        return bp

    def remove(self, breakpoint_id: int) -> bool:
        """
        Remove breakpoint

        Args:
            bp_id (int): The ID of the breakpoint to remove

        Returns:
            bool: True if the breakpoint was removed, False otherwise
        """
        if self._check_breakpoint(breakpoint_id):
            bp = self._breakpoints[breakpoint_id]
            del self._address_index[bp.address]
            del self._breakpoints[breakpoint_id]
            return True
        return False

    def enable(self, breakpoint_id: int) -> bool:
        """
        Enable the breakpoint

        Args:
            breakpoint_id (int): The ID of the breakpoint to enable

        Returns:
            bool: True if the breakpoint was enabled, False otherwise
        """
        if self._check_breakpoint(breakpoint_id):
            self._breakpoints[breakpoint_id].enabled = True
            return True
        return False

    def disable(self, breakpoint_id: int) -> bool:
        """
        Disables the bp

        Args:
            breakpoint_id (int): The ID of the breakpoint to disable

        Returns:
            bool: True if the breakpoint was disabled, False otherwise
        """
        if self._check_breakpoint(breakpoint_id):
            self._breakpoints[breakpoint_id].enabled = False
            return True
        return False

    def check(self, address: int) -> Breakpoint | None:
        """
        Check if curr breakpoint is active

        Args:
            address (int): The address to check

        Returns:
            Breakpoint | None: The breakpoint if hit, None otherwise
        """
        bp_id = self._address_index.get(address)
        if bp_id and self._check_breakpoint(bp_id) and self._breakpoints[bp_id].enabled:
            bp = self._breakpoints[bp_id]
            bp.hit_count += 1
            return bp
        return None

    def list_all(self) -> list[Breakpoint]:
        """
        List of all breakpoints

        Returns:
            list[Breakpoint]: List of all breakpoints
        """
        return list(self._breakpoints.values())

    def clear_all(self) -> int:
        """
        Delete all bps

        Returns:
            int: The number of breakpoints removed
        """
        count = len(self._breakpoints)
        self._breakpoints.clear()
        self._address_index.clear()
        return count
