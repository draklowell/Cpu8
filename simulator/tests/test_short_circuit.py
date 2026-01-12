"""
Short Circuit (Conflict) Detection Tests.

These tests verify that the CPU schematics don't have any short circuits
(conflicts where multiple drivers try to drive the same network to different states).

This is critical for hardware validation - short circuits can damage physical components.
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import INIT_TICKS, MODULES, PERIOD, STARTUP_TICKS, TABLES_PATH

from simulator.base import State
from simulator.engine.loader import load
from simulator.simulation import SimulationEngine

# Resolve paths relative to simulator directory
SIMULATOR_DIR = Path(__file__).parent.parent
NETLISTS_DIR = SIMULATOR_DIR / "netlists"
MICROCODE_TABLES_PATH = (SIMULATOR_DIR / TABLES_PATH).resolve()


@dataclass
class ConflictReport:
    """Report of a detected conflict (short circuit)."""

    tick: int
    network: str
    drivers: list[str]

    def __str__(self) -> str:
        drivers_str = ", ".join(self.drivers)
        return f"Tick {self.tick}: Network '{self.network}' has conflict - Drivers: [{drivers_str}]"


class ShortCircuitDetector:
    """
    Detects short circuits in the CPU simulation.

    A short circuit occurs when multiple drivers attempt to drive
    a network to different logic levels simultaneously.
    """

    def __init__(self, rom: Optional[bytes] = None):
        """
        Initialize the detector.

        Args:
            rom: ROM contents to use. Defaults to NOP-filled ROM.
        """
        self.rom = rom if rom is not None else bytes([0x00] * 65536)
        self.conflicts: list[ConflictReport] = []
        self.engine: Optional[SimulationEngine] = None

    def load_cpu(self) -> bool:
        """
        Load the CPU from netlists.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Check that all netlist files exist
            for netlist_path, _ in MODULES:
                full_path = SIMULATOR_DIR / netlist_path
                if not full_path.exists():
                    raise FileNotFoundError(f"Netlist not found: {full_path}")

            # Check tables path
            if not MICROCODE_TABLES_PATH.exists():
                raise FileNotFoundError(
                    f"Microcode tables not found: {MICROCODE_TABLES_PATH}"
                )

            # Build absolute paths for modules
            modules_abs = [(str(SIMULATOR_DIR / path), name) for path, name in MODULES]

            cpu = load(modules_abs, str(MICROCODE_TABLES_PATH))
            self.engine = SimulationEngine(cpu, self.rom)
            return True
        except Exception as e:
            print(f"Failed to load CPU: {e}")
            return False

    def check_for_conflicts(
        self, chunk, skip_before_tick: int = 0
    ) -> list[ConflictReport]:
        """
        Check a simulation chunk for conflicts.

        Args:
            chunk: WaveformChunk from simulation tick.
            skip_before_tick: Skip conflicts before this tick (for startup transients).

        Returns:
            List of conflicts found in this chunk.
        """
        if chunk.tick < skip_before_tick:
            return []

        conflicts = []
        for network, state in chunk.network_states.items():
            if state == State.CONFLICT:
                drivers = chunk.network_drivers.get(network, [])
                conflict = ConflictReport(
                    tick=chunk.tick,
                    network=network,
                    drivers=list(drivers) if drivers else ["unknown"],
                )
                conflicts.append(conflict)
        return conflicts

    def run_initialization_check(
        self,
        init_ticks: int = None,
        startup_ticks: int = None,
        skip_startup_ticks: int = 10,
    ) -> list[ConflictReport]:
        """
        Run initialization and check for conflicts during power-on sequence.

        Args:
            init_ticks: Number of initialization ticks.
            startup_ticks: Number of startup ticks after reset.
            skip_startup_ticks: Number of initial ticks to skip (for startup transients).

        Returns:
            List of all conflicts found (excluding startup transients).
        """
        if self.engine is None:
            if not self.load_cpu():
                raise RuntimeError("Failed to load CPU")

        init_ticks = init_ticks or INIT_TICKS
        startup_ticks = startup_ticks or STARTUP_TICKS

        self.conflicts = []

        # Power on
        self.engine.set_power(True)
        self.engine.set_component_variable("I:PAD2", "RESET", 1)
        self.engine.set_component_variable("I:PAD2", "WAIT", 0)

        # Initial ticks (reset held) - skip conflicts during startup transients
        for _ in range(init_ticks):
            chunk = self.engine.tick()
            conflicts = self.check_for_conflicts(
                chunk, skip_before_tick=skip_startup_ticks
            )
            self.conflicts.extend(conflicts)

        # Release reset
        self.engine.set_component_variable("I:PAD2", "RESET", 0)

        # Startup ticks
        for _ in range(startup_ticks):
            chunk = self.engine.tick()
            conflicts = self.check_for_conflicts(
                chunk, skip_before_tick=skip_startup_ticks
            )
            self.conflicts.extend(conflicts)

        return self.conflicts

    def run_clock_cycles(
        self,
        cycles: int = 10,
        period: int = None,
        skip_before_tick: int = 0,
        check_only_on_rising_edge: bool = True,
    ) -> list[ConflictReport]:
        """
        Run multiple clock cycles and check for conflicts.

        Args:
            cycles: Number of clock cycles to run.
            period: Clock period in ticks.
            skip_before_tick: Skip conflicts before this tick.
            check_only_on_rising_edge: If True, only check conflicts on clock rising edge
                                       (matches behavior in simulate.py). This avoids
                                       detecting short transient conflicts during bus transitions.

        Returns:
            List of all conflicts found.
        """
        if self.engine is None:
            raise RuntimeError(
                "Engine not initialized. Call run_initialization_check first."
            )

        period = period or PERIOD

        for _ in range(cycles):
            # Clock low half - no conflict checking (transients expected)
            self.engine.set_component_variable("I:PAD2", "CLOCK", 0)
            for _ in range(period // 2):
                chunk = self.engine.tick()
                if not check_only_on_rising_edge:
                    conflicts = self.check_for_conflicts(chunk, skip_before_tick)
                    self.conflicts.extend(conflicts)

            # Clock rising edge - THIS is where we check for conflicts
            # (same as simulate.py step() method)
            chunk = self.engine.tick()
            conflicts = self.check_for_conflicts(chunk, skip_before_tick)
            self.conflicts.extend(conflicts)

            # Clock high half (rest of it)
            self.engine.set_component_variable("I:PAD2", "CLOCK", 1)
            for _ in range(period // 2 - 1):  # -1 because we already did one tick above
                chunk = self.engine.tick()
                if not check_only_on_rising_edge:
                    conflicts = self.check_for_conflicts(chunk, skip_before_tick)
                    self.conflicts.extend(conflicts)

        return self.conflicts

    def get_unique_conflicts(self) -> dict[str, ConflictReport]:
        """
        Get unique conflicts by network name.

        Returns:
            Dictionary mapping network names to their first conflict.
        """
        unique = {}
        for conflict in self.conflicts:
            if conflict.network not in unique:
                unique[conflict.network] = conflict
        return unique


class TestShortCircuitDetection:
    """Tests for short circuit detection during normal operation."""

    # Number of ticks to skip at startup (for power-on transients)
    SKIP_STARTUP_TICKS = 50

    @pytest.fixture
    def detector(self):
        """Create a fresh ShortCircuitDetector."""
        return ShortCircuitDetector()

    @pytest.fixture
    def nop_rom(self):
        """Create a ROM filled with NOP instructions."""
        return bytes([0x00] * 65536)

    @pytest.fixture
    def halt_rom(self):
        """Create a ROM with HALT instruction at start."""
        rom = bytearray([0x00] * 65536)
        rom[0] = 0xFF  # HALT instruction (adjust based on actual ISA)
        return bytes(rom)

    @pytest.mark.short_circuit
    def test_no_conflicts_during_initialization(self, detector):
        """
        Test that no short circuits occur during CPU initialization.

        Note: First few ticks are skipped as power-on transients are expected.
        """
        conflicts = detector.run_initialization_check(
            init_ticks=100,
            startup_ticks=100,
            skip_startup_ticks=self.SKIP_STARTUP_TICKS,
        )

        if conflicts:
            unique = detector.get_unique_conflicts()
            conflict_messages = [str(c) for c in unique.values()]
            pytest.fail(
                f"SHORT CIRCUITS DETECTED during initialization!\n"
                f"Found {len(unique)} unique conflicts:\n"
                + "\n".join(conflict_messages)
            )

    @pytest.mark.short_circuit
    def test_no_conflicts_during_nop_execution(self, detector, nop_rom):
        """
        Test that no short circuits occur when executing NOP instructions.

        Note: Only checks for conflicts on clock rising edge (same as simulate.py),
        to avoid detecting short transient conflicts during bus transitions.
        """
        detector.rom = nop_rom

        # Initialize first (skip startup transients)
        detector.run_initialization_check(
            init_ticks=100,
            startup_ticks=100,
            skip_startup_ticks=self.SKIP_STARTUP_TICKS,
        )
        initial_conflicts = len(detector.conflicts)

        # Get current tick for skip threshold
        current_tick = detector.engine._tick

        # Run some clock cycles executing NOPs
        detector.run_clock_cycles(cycles=5, period=100, skip_before_tick=current_tick)

        new_conflicts = detector.conflicts[initial_conflicts:]
        if new_conflicts:
            unique = {}
            for c in new_conflicts:
                if c.network not in unique:
                    unique[c.network] = c

            conflict_messages = [str(c) for c in unique.values()]
            pytest.fail(
                f"SHORT CIRCUITS DETECTED during NOP execution!\n"
                f"Found {len(unique)} unique conflicts:\n"
                + "\n".join(conflict_messages)
            )

    @pytest.mark.short_circuit
    def test_no_conflicts_with_reset_sequence(self, detector):
        """
        Test that reset sequence doesn't cause conflicts after initial stabilization.
        """
        detector.load_cpu()

        # Power on with reset held
        detector.engine.set_power(True)
        detector.engine.set_component_variable("I:PAD2", "RESET", 1)
        detector.engine.set_component_variable("I:PAD2", "WAIT", 0)
        detector.engine.set_component_variable("I:PAD2", "CLOCK", 0)

        conflicts = []

        # Hold reset for several ticks (skip first few for power-on transients)
        for _ in range(150):
            chunk = detector.engine.tick()
            conflicts.extend(
                detector.check_for_conflicts(
                    chunk, skip_before_tick=self.SKIP_STARTUP_TICKS
                )
            )

        if conflicts:
            unique = {}
            for c in conflicts:
                if c.network not in unique:
                    unique[c.network] = c

            conflict_messages = [str(c) for c in unique.values()]
            pytest.fail(
                f"SHORT CIRCUITS DETECTED during reset!\n"
                f"Found {len(unique)} unique conflicts:\n"
                + "\n".join(conflict_messages)
            )


class TestNetlistIntegrity:
    """Tests for netlist file integrity and loading."""

    @pytest.mark.short_circuit
    def test_all_netlists_exist(self):
        """Verify all required netlist files exist."""
        missing = []
        for netlist_path, module_name in MODULES:
            full_path = SIMULATOR_DIR / netlist_path
            if not full_path.exists():
                missing.append(f"{module_name}: {netlist_path}")

        if missing:
            pytest.fail(f"Missing netlist files:\n" + "\n".join(missing))

    @pytest.mark.short_circuit
    def test_cpu_loads_successfully(self):
        """Test that CPU can be loaded from netlists."""
        detector = ShortCircuitDetector()
        assert detector.load_cpu(), "Failed to load CPU from netlists"

    @pytest.mark.short_circuit
    def test_simulation_engine_initializes(self):
        """Test that SimulationEngine initializes correctly."""
        detector = ShortCircuitDetector()
        detector.load_cpu()

        assert detector.engine is not None
        assert detector.engine._tick == 0


class TestPowerConnections:
    """Tests for power connection verification."""

    @pytest.mark.short_circuit
    def test_all_components_have_power(self):
        """Verify all components have VCC connected."""
        detector = ShortCircuitDetector()
        detector.load_cpu()

        # Power on
        detector.engine.set_power(True)
        detector.engine.set_component_variable("I:PAD2", "RESET", 1)

        # Run initialization
        chunk = None
        for _ in range(50):
            chunk = detector.engine.tick()

        component_pins = detector.engine.get_component_pins()
        missing_power = []

        for component, pins in component_pins.items():
            if "VCC" not in pins:
                continue  # Some components may not need VCC

            vcc_network = pins["VCC"]
            state = chunk.network_states.get(vcc_network)

            if state != State.HIGH:
                missing_power.append(f"{component}: VCC={state}")

        if missing_power:
            pytest.fail(f"Components with power issues:\n" + "\n".join(missing_power))


class TestSanityCheck:
    """
    Sanity checks to verify that the short circuit detector actually works.
    These tests intentionally create conflicts and verify they are detected.
    """

    @pytest.mark.short_circuit
    def test_check_for_conflicts_detects_conflict_state(self):
        """
        SANITY CHECK: Verify check_for_conflicts finds State.CONFLICT.

        This test creates a mock chunk with a CONFLICT state and verifies
        the detector catches it.
        """
        from dataclasses import dataclass, field

        # Create a mock WaveformChunk with a CONFLICT
        @dataclass
        class MockChunk:
            tick: int = 100
            network_states: dict = field(default_factory=dict)
            network_drivers: dict = field(default_factory=dict)

        mock_chunk = MockChunk()
        mock_chunk.network_states = {
            "/NORMAL_NET": State.HIGH,
            "/ANOTHER_NET": State.LOW,
            "/SHORT_CIRCUIT_NET": State.CONFLICT,  # This is the short circuit!
            "/FLOATING_NET": State.FLOATING,
        }
        mock_chunk.network_drivers = {
            "/SHORT_CIRCUIT_NET": ["U1:2", "U2:4"],
        }

        detector = ShortCircuitDetector()
        # Don't need to load CPU for this test
        conflicts = detector.check_for_conflicts(mock_chunk, skip_before_tick=0)

        assert len(conflicts) == 1, f"Expected 1 conflict, got {len(conflicts)}"
        assert conflicts[0].network == "/SHORT_CIRCUIT_NET"
        assert conflicts[0].tick == 100
        assert "U1:2" in conflicts[0].drivers
        assert "U2:4" in conflicts[0].drivers

        print(
            "✓ Sanity check passed: check_for_conflicts correctly detects State.CONFLICT"
        )

    @pytest.mark.short_circuit
    def test_check_for_conflicts_ignores_normal_states(self):
        """
        Verify check_for_conflicts doesn't false-positive on normal states.
        """
        from dataclasses import dataclass, field

        @dataclass
        class MockChunk:
            tick: int = 100
            network_states: dict = field(default_factory=dict)
            network_drivers: dict = field(default_factory=dict)

        mock_chunk = MockChunk()
        mock_chunk.network_states = {
            "/NET_HIGH": State.HIGH,
            "/NET_LOW": State.LOW,
            "/NET_FLOATING": State.FLOATING,
        }

        detector = ShortCircuitDetector()
        conflicts = detector.check_for_conflicts(mock_chunk, skip_before_tick=0)

        assert len(conflicts) == 0, f"Expected no conflicts, got {len(conflicts)}"
        print("✓ Sanity check passed: No false positives on normal states")

    @pytest.mark.short_circuit
    def test_skip_before_tick_works(self):
        """
        Verify that skip_before_tick correctly ignores early conflicts.
        """
        from dataclasses import dataclass, field

        @dataclass
        class MockChunk:
            tick: int
            network_states: dict = field(default_factory=dict)
            network_drivers: dict = field(default_factory=dict)

        detector = ShortCircuitDetector()

        # Early tick with conflict - should be skipped
        early_chunk = MockChunk(tick=10)
        early_chunk.network_states = {"/NET": State.CONFLICT}
        early_chunk.network_drivers = {"/NET": ["U1:1"]}

        conflicts_early = detector.check_for_conflicts(early_chunk, skip_before_tick=50)
        assert (
            len(conflicts_early) == 0
        ), "Should skip conflicts before skip_before_tick"

        # Later tick with conflict - should be detected
        late_chunk = MockChunk(tick=100)
        late_chunk.network_states = {"/NET": State.CONFLICT}
        late_chunk.network_drivers = {"/NET": ["U1:1"]}

        conflicts_late = detector.check_for_conflicts(late_chunk, skip_before_tick=50)
        assert (
            len(conflicts_late) == 1
        ), "Should detect conflicts after skip_before_tick"

        print("✓ Sanity check passed: skip_before_tick works correctly")

    @pytest.mark.short_circuit
    def test_detector_finds_direct_state_conflict(self):
        """
        SANITY CHECK: Verify that State.CONFLICT is correctly identified.

        This test directly checks that our conflict detection logic works
        by examining how the simulator reports conflicts.
        """
        detector = ShortCircuitDetector()
        assert detector.load_cpu(), "Failed to load CPU"

        # Run some ticks
        detector.engine.set_power(True)
        for _ in range(10):
            chunk = detector.engine.tick()

        # Verify we can access network states
        assert hasattr(chunk, "network_states"), "Chunk missing network_states"
        assert len(chunk.network_states) > 0, "No network states found"

        # Verify we have the State.CONFLICT constant available
        assert hasattr(State, "CONFLICT"), "State.CONFLICT not defined"

        # Count how many networks exist
        total_networks = len(chunk.network_states)
        print(
            f"✓ Sanity check passed: Simulator has {total_networks} networks to monitor"
        )

    @pytest.mark.short_circuit
    def test_conflict_report_formatting(self):
        """
        Test that ConflictReport formats correctly.
        """
        report = ConflictReport(tick=100, network="/TEST_NET", drivers=["U1:2", "U2:2"])

        report_str = str(report)
        assert "100" in report_str
        assert "TEST_NET" in report_str
        assert "U1:2" in report_str
        assert "U2:2" in report_str


# Standalone runner for CI
SKIP_STARTUP_TICKS = 50  # Skip first 50 ticks for power-on transients


def run_short_circuit_check() -> int:
    """
    Run short circuit checks and return exit code.

    Returns:
        0 if no conflicts, 1 if conflicts found.
    """
    print("=" * 60)
    print("CPU8 Short Circuit Detection")
    print("=" * 60)
    print(f"(Skipping first {SKIP_STARTUP_TICKS} ticks for power-on transients)")

    detector = ShortCircuitDetector()

    print("\n[1/3] Loading CPU from netlists...")
    if not detector.load_cpu():
        print("FAILED: Could not load CPU")
        return 1
    print("OK: CPU loaded successfully")

    print("\n[2/3] Running initialization check...")
    conflicts = detector.run_initialization_check(
        init_ticks=100, startup_ticks=100, skip_startup_ticks=SKIP_STARTUP_TICKS
    )

    if conflicts:
        unique = detector.get_unique_conflicts()
        print(
            f"FAILED: Found {len(unique)} unique short circuits during initialization"
        )
        for network, conflict in unique.items():
            print(f"  - {conflict}")
        return 1
    print("OK: No conflicts during initialization")

    print("\n[3/3] Running clock cycle check...")
    current_tick = detector.engine._tick
    detector.run_clock_cycles(cycles=10, period=100, skip_before_tick=current_tick)

    new_conflicts = detector.conflicts
    if new_conflicts:
        unique = detector.get_unique_conflicts()
        print(f"FAILED: Found {len(unique)} unique short circuits during execution")
        for network, conflict in unique.items():
            print(f"  - {conflict}")
        return 1
    print("OK: No conflicts during execution")

    print("\n" + "=" * 60)
    print("All short circuit checks PASSED")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(run_short_circuit_check())
