"""
Debug package for CPU8 simulator.
"""

from debug.base import DebuggerCore
from debug.breakpoint import Breakpoint, BreakpointManager
from debug.color import Color, colored, print_header, print_separator
from debug.disassembler import Disassembler
from debug.state import CPUState
from debug.ui import DebuggerStrings
from debug.watch import Watch, WatchManager

from simulator.config import (
    INIT_TICKS,
    MODULES,
    PERIOD,
    STARTUP_TICKS,
    TABLES_PATH,
    load_microcode_data,
)

__all__ = [
    "Color",
    "colored",
    "print_header",
    "print_separator",
    "DebuggerStrings",
    "Breakpoint",
    "BreakpointManager",
    "Watch",
    "WatchManager",
    "CPUState",
    "Disassembler",
    "PERIOD",
    "INIT_TICKS",
    "STARTUP_TICKS",
    "MODULES",
    "TABLES_PATH",
    "load_microcode_data",
    "DebuggerCore",
]
