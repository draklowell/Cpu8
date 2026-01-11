"""
CPU state representation
"""

from dataclasses import dataclass


@dataclass
class CPUState:
    """
    current CPU state
    """

    cycle: int = 0
    pc: int = 0
    sp: int = 0
    instruction: int = 0
    mnemonic: str = "???"

    # Registers
    ac: int = 0
    xh: int = 0
    xl: int = 0
    yh: int = 0
    yl: int = 0
    zh: int = 0
    zl: int = 0
    flags: int = 0

    # Status
    halted: bool = False

    # Memory
    address_bus: int = 0
    data_bus: int = 0
