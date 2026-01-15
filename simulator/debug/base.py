"""
Core debugger
"""

import re

from config import (
    INIT_TICKS,
    MODULES,
    PERIOD,
    STARTUP_TICKS,
    TABLES_PATH,
    load_microcode_data,
)
from debug.breakpoint import BreakpointManager
from debug.disassembler import Disassembler
from debug.state import CPUState
from debug.watch import WatchManager
from simulator.simulation import SimulationEngine, State, WaveformChunk


class DebuggerCore:
    """
    Core debugger functionality
    """

    def __init__(self, rom_path: str):
        self.rom_path = rom_path
        self.readers, self.writers, self.microcode, self.cycles = load_microcode_data()

        # Load ROM
        with open(rom_path, "rb") as f:
            self.rom = f.read()

        # Initialize simulation
        self.engine = SimulationEngine.load(MODULES, TABLES_PATH, self.rom)
        self.period = PERIOD
        self._component_pins = self.engine.get_component_pins()

        # State
        self.state = CPUState()
        self.last_chunk: WaveformChunk | None = None
        self.initialized = False

        # Managers
        self.breakpoints = BreakpointManager()
        self.watches = WatchManager()

        # Disassembler
        self.disasm = Disassembler(self.rom, self.microcode)

        # History
        self.instruction_history: list[CPUState] = []
        self.max_history = 100

    def initialize(self) -> None:
        """
        Init CPU
        """
        self.engine.set_power(True)
        self.engine.set_component_variable("I:PAD2", "RESET", 1)
        self.engine.set_component_variable("I:PAD2", "WAIT", 0)

        # Init ticks
        for _ in range(INIT_TICKS):
            chunk = self._tick(verbose=False)

        # Release reset
        self.engine.set_component_variable("I:PAD2", "RESET", 0)

        # Startup ticks
        for _ in range(STARTUP_TICKS):
            chunk = self._tick(verbose=False)

        self.last_chunk = chunk
        self.initialized = True
        self._update_state()

    def _tick(self, verbose: bool = True) -> WaveformChunk:
        chunk = self.engine.tick()
        return chunk

    def step_instruction(self) -> CPUState:
        """
        Execute a single clock cycle (one tick).
        Note: A full CPU instruction may take multiple clock cycles.
        Use step_full_instruction() to execute a complete instruction.
        """
        if not self.initialized:
            self.initialize()

        if len(self.instruction_history) >= self.max_history:
            self.instruction_history.pop(0)
        self.instruction_history.append(CPUState(**vars(self.state)))

        # Clock low
        self.engine.set_component_variable("I:PAD2", "CLOCK", 0)
        for _ in range(self.period // 2):
            self._tick(False)
        self._tick(True)

        # Clock high
        self.engine.set_component_variable("I:PAD2", "CLOCK", 1)
        for _ in range(self.period // 2):
            chunk = self._tick(False)

        self.last_chunk = chunk
        self.state.cycle += 1
        self._update_state()

        return self.state

    def step_full_instruction(self, max_cycles: int = 50) -> CPUState:
        """
        Execute clock cycles until a full instruction is completed.

        Uses PC tracking to determine when an instruction finishes.
        The instruction is complete when PC has moved past the current instruction
        (including its operands) and stabilized.

        Args:
            max_cycles: Maximum cycles as a safety limit

        Returns:
            CPUState after the instruction completes
        """
        if not self.initialized:
            self.initialize()

        # Record starting PC and calculate expected next PC
        start_pc = self.state.pc
        opcode = self.rom[start_pc] if start_pc < len(self.rom) else 0xFF

        # Calculate instruction size based on mnemonic
        mnemonic = self.microcode.get(opcode, "")
        if "[word]" in mnemonic:
            instr_size = 3  # opcode + 2 byte operand
        elif "[byte]" in mnemonic:
            instr_size = 2  # opcode + 1 byte operand
        else:
            instr_size = 1  # just opcode

        # Expected next instruction address (for non-jump instructions)
        expected_next_pc = start_pc + instr_size

        # The instruction ends when PC is outside the range [start_pc, start_pc + instr_size)
        # and has stabilized for at least 1 cycle
        prev_pc = start_pc
        stable_count = 0

        for _ in range(max_cycles):
            self.step_instruction()

            if self.state.halted:
                break

            current_pc = self.state.pc

            # Check if we've moved outside the current instruction
            # PC should be either at expected_next_pc (sequential) or somewhere else (jump)
            outside_current_instr = (
                current_pc < start_pc or current_pc >= expected_next_pc
            )

            if outside_current_instr:
                # Wait for PC to stabilize
                if current_pc == prev_pc:
                    stable_count += 1
                    if stable_count >= 1:
                        break
                else:
                    stable_count = 0
                    prev_pc = current_pc
            else:
                # Still within current instruction (fetching operands)
                prev_pc = current_pc
                stable_count = 0

        return self.state

    def _update_state(self) -> None:
        """
        Update CPU state from last chunk
        """
        if self.last_chunk is None:
            return

        chunk = self.last_chunk

        self.state.pc = self._read_register(
            chunk, ["PC:U4", "PC:U5", "PC:U2", "PC:U3"], 16
        )
        self.state.sp = self._read_register(
            chunk, ["SP:U4", "SP:U5", "SP:U2", "SP:U3"], 16
        )
        self.state.instruction = self._read_register(chunk, ["C1:INSTRUCTION1"], 8)
        self.state.mnemonic = self.microcode.get(self.state.instruction, "???")
        self.state.zh = self._read_register(chunk, ["REG:ZH1"], 8)
        self.state.zl = self._read_register(chunk, ["REG:ZL1"], 8)
        self.state.yh = self._read_register(chunk, ["REG:YH1"], 8)
        self.state.yl = self._read_register(chunk, ["REG:YL1"], 8)
        self.state.xh = self._read_register(chunk, ["REG:XH1"], 8)
        self.state.xl = self._read_register(chunk, ["REG:XL1"], 8)
        self.state.address_bus = self._read_register(
            chunk, ["I:U8", "I:U7", "I:U6", "I:U5"], 16
        )

        network = self._component_pins["I:PAD2"].get("N_HALT")
        if network and chunk.network_states.get(network) == State.LOW:
            self.state.halted = True

    def _read_register(
        self, chunk: WaveformChunk, registers: list[str], size: int
    ) -> int:
        """
        Read a register value from the simulation.
        """
        if size % len(registers) != 0:
            return 0

        result = 0
        size_per_reg = size // len(registers)
        for i, comp in enumerate(registers):
            if comp in chunk.variables and "Q" in chunk.variables[comp]:
                result |= chunk.variables[comp]["Q"] << (i * size_per_reg)
        return result

    def _read_bus(self, chunk: WaveformChunk, network_prefix: str, size: int) -> int:
        """
        Read a bus value
        """
        value = 0
        for i in range(size):
            network = f"{network_prefix}{i}!"
            if network in chunk.network_states:
                if chunk.network_states[network] == State.HIGH:
                    value |= 1 << i
        return value

    def read_memory(self, address: int, size: int = 1) -> bytes:
        """
        Read from ROM
        """
        if address + size <= len(self.rom):
            return self.rom[address : address + size]
        return b""

    def get_register_value(self, name: str) -> int | None:
        """
        Get a register value by name.
        Note: AC (Accumulator) = XL
        """
        name = name.lower()
        mapping = {
            "pc": self.state.pc,
            "sp": self.state.sp,
            "ac": self.state.xl,  # AC = XL (Accumulator)
            "accumulator": self.state.xl,
            "xh": self.state.xh,
            "xl": self.state.xl,
            "x": (self.state.xh << 8) | self.state.xl,
            "yh": self.state.yh,
            "yl": self.state.yl,
            "y": (self.state.yh << 8) | self.state.yl,
            "zh": self.state.zh,
            "zl": self.state.zl,
            "z": (self.state.zh << 8) | self.state.zl,
            "flags": self.state.flags,
            "fr": self.state.flags,
        }
        return mapping.get(name)

    def tick_simulator(self) -> WaveformChunk:
        """
        Execute a single simulator tick
        """
        chunk = self._tick(verbose=True)
        self.last_chunk = chunk
        return chunk

    def set_variable(self, component: str, var: str, value: int) -> bool:
        """
        Set a component variable
        """
        return self.engine.set_component_variable(component, var, value)

    def set_period(self, period: int) -> None:
        """
        Set clock period (simulator ticks per CPU tick)
        """
        self.period = period

    def get_network_state(self, network: str) -> State | None:
        """
        Get the state of a network
        """
        if self.last_chunk is None:
            return None
        return self.last_chunk.network_states.get(network)

    def get_network_states(self, networks: list[str]) -> list[State | None]:
        """
        Get the states of multiple networks
        """
        return [self.get_network_state(n) for n in networks]

    def get_component_pin(
        self, component: str, pin_alias: str
    ) -> tuple[str | None, State | None]:
        """
        Get network name and state for a component pin by alias
        """
        pins = self._component_pins.get(component)
        if pins is None:
            return None, None
        network = pins.get(pin_alias)
        if network is None:
            return None, None
        state = self.get_network_state(network)
        return network, state

    def get_component_pins(self, component: str) -> dict[str, str] | None:
        """
        Get all pins for a component (alias -> network)
        """
        return self._component_pins.get(component)

    def list_components(self) -> list[str]:
        """
        List all component names
        """
        return list(self._component_pins.keys())

    def expand_network_range(self, range_spec: str) -> list[str]:
        """
        Expand a network range specification

        Examples:
            "C3:/STATE16 - C3:/STATE0" -> ["C3:/STATE16!", "C3:/STATE15!", ..., "C3:/STATE0!"]
            "PC:/DATA7 - PC:/DATA0" -> ["PC:/DATA7!", ..., "PC:/DATA0!"]
        """
        if " - " not in range_spec:
            network = range_spec.strip()
            if not network.endswith("!"):
                network += "!"
            return [network]

        parts = range_spec.split(" - ")
        if len(parts) != 2:
            return []

        start_spec = parts[0].strip()
        end_spec = parts[1].strip()

        # Parse prefix and number from each spec
        start_match = re.match(r"(.+?)(\d+)(!?)$", start_spec)
        end_match = re.match(r"(.+?)(\d+)(!?)$", end_spec)

        if not start_match or not end_match:
            return []

        start_prefix = start_match.group(1)
        start_num = int(start_match.group(2))
        end_prefix = end_match.group(1)
        end_num = int(end_match.group(2))

        if start_prefix != end_prefix:
            return []

        # generate range (high to low)
        if start_num >= end_num:
            nums = range(start_num, end_num - 1, -1)
        else:
            nums = range(start_num, end_num + 1)

        return [f"{start_prefix}{n}!" for n in nums]

    def read_networks_as_binary(self, networks: list[str]) -> str:
        """
        Read multiple networks and return as binary string.
        Returns characters: 1, 0, Z (floating), X (conflict)
        First network in list = leftmost bit
        """
        result = ""
        for network in networks:
            state = self.get_network_state(network)
            if state == State.HIGH:
                result += "1"
            elif state == State.LOW:
                result += "0"
            elif state == State.FLOATING:
                result += "Z"
            elif state == State.CONFLICT:
                result += "X"
            else:
                result += "?"
        return result

    def read_networks_as_int(self, networks: list[str]) -> int | None:
        """
        Read multiple networks as an integer value.
        First network in list = MSB, last = LSB.
        Returns None if any network is not driven (Z or X)
        """
        value = 0
        for i, network in enumerate(networks):
            state = self.get_network_state(network)
            if state == State.HIGH:
                value |= 1 << (len(networks) - 1 - i)
            elif state == State.LOW:
                pass
            else:
                return None
        return value
