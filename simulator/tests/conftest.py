"""
Pytest fixtures and configuration for debugger tests.
"""

import io
import os
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from typing import Generator
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from debug.breakpoint import Breakpoint, BreakpointManager
from debug.disassembler import Disassembler
from debug.state import CPUState
from debug.watch import Watch, WatchManager


@pytest.fixture
def temp_rom_file() -> Generator[str, None, None]:
    """Create a temporary ROM file for testing."""
    # Create a simple ROM with some instructions
    rom_data = bytes(
        [
            0x00,  # NOP
            0x01,  # Some instruction
            0x02,  # Some instruction
            0x10,
            0x20,  # Instruction with byte operand
            0x20,
            0x30,
            0x40,  # Instruction with word operand
            0xFF,  # HALT
        ]
        + [0x00] * 248
    )  # Pad to 256 bytes

    with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False) as f:
        f.write(rom_data)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def sample_rom() -> bytes:
    """Return sample ROM bytes for testing."""
    return bytes(
        [
            0x00,  # NOP
            0x01,  # Instruction 1
            0x02,  # Instruction 2
            0x10,
            0x20,  # Instruction with byte operand
            0x20,
            0x30,
            0x40,  # Instruction with word operand
            0xFF,  # HALT
        ]
        + [0x00] * 248
    )


@pytest.fixture
def sample_microcode() -> dict[int, str]:
    """Return sample microcode mapping for testing."""
    return {
        0x00: "NOP",
        0x01: "INC A",
        0x02: "DEC A",
        0x10: "LD A, [byte]",
        0x20: "JMP [word]",
        0xFF: "HALT",
    }


@pytest.fixture
def breakpoint_manager() -> BreakpointManager:
    """Return a fresh BreakpointManager for testing."""
    return BreakpointManager()


@pytest.fixture
def watch_manager() -> WatchManager:
    """Return a fresh WatchManager for testing."""
    return WatchManager()


@pytest.fixture
def cpu_state() -> CPUState:
    """Return a sample CPU state for testing."""
    return CPUState(
        cycle=100,
        pc=0x0100,
        sp=0x01FF,
        instruction=0x42,
        mnemonic="TEST",
        ac=0x12,
        xh=0x34,
        xl=0x56,
        yh=0x78,
        yl=0x9A,
        zh=0xBC,
        zl=0xDE,
        flags=0b10101010,
        halted=False,
        address_bus=0x1234,
        data_bus=0xAB,
    )


@pytest.fixture
def disassembler(sample_rom, sample_microcode) -> Disassembler:
    """Return a configured Disassembler for testing."""
    return Disassembler(sample_rom, sample_microcode)


class MockState:
    """Mock for simulator State enum."""

    HIGH = "HIGH"
    LOW = "LOW"
    FLOATING = "FLOATING"
    CONFLICT = "CONFLICT"


class MockWaveformChunk:
    """Mock for WaveformChunk."""

    def __init__(self):
        self.network_states = {
            "TEST_NET!": MockState.HIGH,
            "NET0!": MockState.LOW,
            "NET1!": MockState.HIGH,
            "C3:/STATE0!": MockState.HIGH,
            "C3:/STATE1!": MockState.LOW,
        }
        self.variables = {
            "C1:DECODER1": {"Q": 0x42},
            "I:PAD2": {"CLOCK": 1, "RESET": 0},
            "PC:U4": {"Q": 0x12},
        }
        self.logs = []
        self.tick = 0


class MockSimulationEngine:
    """Mock SimulationEngine for testing without actual simulation."""

    def __init__(self, *args, **kwargs):
        self._tick_count = 0
        self._power = False
        self._variables = {
            "I:PAD2": {"CLOCK": 0, "RESET": 0, "WAIT": 0},
            "C1:DECODER1": {"Y0": 0, "Y1": 0},
        }

    @classmethod
    def load(cls, *args, **kwargs):
        return cls()

    def set_power(self, state: bool):
        self._power = state

    def set_component_variable(self, component: str, var: str, value: int) -> bool:
        if component not in self._variables:
            self._variables[component] = {}
        self._variables[component][var] = value
        return True

    def tick(self) -> MockWaveformChunk:
        self._tick_count += 1
        return MockWaveformChunk()

    def get_component_pins(self) -> dict[str, dict[str, str]]:
        return {
            "I:PAD2": {"CLOCK": "CLOCK!", "RESET": "RESET!", "N_HALT": "N_HALT!"},
            "C1:DECODER1": {"Y0": "DEC_Y0!", "Y1": "DEC_Y1!"},
            "PC:U4": {"Q": "PC_Q!"},
            "REG:ZH1": {"Q": "ZH_Q!"},
        }


@pytest.fixture
def mock_simulation_engine():
    """Return a MockSimulationEngine for testing."""
    return MockSimulationEngine()


def capture_output(func, *args, **kwargs) -> tuple[str, str]:
    """
    Capture stdout and stderr from a function call.
    Returns (stdout, stderr).
    """
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
        func(*args, **kwargs)

    return stdout_capture.getvalue(), stderr_capture.getvalue()


@pytest.fixture
def capture():
    """Fixture to capture output."""
    return capture_output
