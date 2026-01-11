"""
Strings for the debugger UI.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class UIStrings:
    """
    General UI elems
    """

    BANNER: str = """
╔═══════════════════════════════════════════════════════════════╗
║           Dragonfly 8b9m GDB CLI                              ║
║                                                               ║
║  Type 'help' for available commands                           ║
║  Type 'help <command>' for detailed help on a command         ║
╚═══════════════════════════════════════════════════════════════╝
"""
    PROMPT: str = "(gdb-dragonfly) "
    GOODBYE: str = "Done!"

    HEADER_REGISTERS: str = "Registers"
    HEADER_BREAKPOINTS: str = "Breakpoints"
    HEADER_WATCHES: str = "Watches"
    HEADER_PROGRAM_INFO: str = "Program Info"
    HEADER_CPU_STATE: str = "CPU State"
    HEADER_INSTRUCTION_HISTORY: str = "Instruction History"
    HEADER_DISASSEMBLY: str = "Disassembly @ 0x{address:04X}"
    HEADER_MEMORY: str = "Memory @ 0x{address:04X}"


@dataclass(frozen=True)
class ExecutionStrings:
    """
    Execution related messages
    """

    STARTING_PROGRAM: str = "Starting program"
    CONTINUING: str = "Continuing"
    PROGRAM_HALTED: str = "Program has halted"
    PROGRAM_HALTED_ALT: str = "Program halted"
    STOPPED_AFTER_CYCLES: str = "Stopped after {max_cycles} cycles"
    RESETTING_CPU: str = "Resetting CPU"
    RESET_COMPLETE: str = "CPU reset complete"
    INTERRUPTED: str = "Interrupted"


@dataclass(frozen=True)
class BreakpointStrings:
    """
    Breakpoint related messages
    """

    BREAKPOINT_SET: str = "Breakpoint {id} set at 0x{address:04X}"
    BREAKPOINT_HIT: str = "Breakpoint {id} hit at 0x{address:04X}"
    BREAKPOINT_DELETED: str = "Deleted breakpoint {id}"
    BREAKPOINT_NOT_FOUND: str = "Breakpoint {id} not found"
    BREAKPOINTS_DELETED: str = "Deleted {count} breakpoints"
    BREAKPOINT_ENABLED: str = "Enabled breakpoint {id}"
    BREAKPOINT_DISABLED: str = "Disabled breakpoint {id}"
    INVALID_BREAKPOINT_ID: str = "Invalid breakpoint ID"
    NO_BREAKPOINTS: str = "No breakpoints set"


@dataclass(frozen=True)
class WatchStrings:
    """
    Watch related messages
    """

    WATCH_SET: str = "Watch {id} set for: {expression}"
    NO_WATCHES: str = "No watches set"


@dataclass(frozen=True)
class ErrorStrings:
    """
    Error messages.
    """

    INVALID_COUNT: str = "Error: Invalid count"
    INVALID_ADDRESS: str = "Invalid address: {address}"
    UNKNOWN_REGISTER: str = "Unknown register or expression: {name}"
    UNKNOWN_INFO_CMD: str = "Unknown info command: {subcmd}"
    ROM_NOT_FOUND: str = "Error: ROM file not found: {path}"
    GENERAL_ERROR: str = "Error: {message}"
    INVALID_CONTEXT: str = "Invalid context value"


@dataclass(frozen=True)
class UsageStrings:
    """
    usage/help messages
    """

    USAGE_EXAMINE: str = "Usage: examine [/FMT] <address>"
    USAGE_INFO: str = "Usage: info <registers|breakpoints|watches|program|cpu>"
    USAGE_PRINT: str = "Usage: print <register|expression>"
    USAGE_BREAK: str = "Usage: break <address>"
    USAGE_ENABLE: str = "Usage: enable <breakpoint-id>"
    USAGE_DISABLE: str = "Usage: disable <breakpoint-id>"
    USAGE_WATCH: str = "Usage: watch <expression>"
    USAGE_SET: str = "Usage: set <option> <value>"


@dataclass(frozen=True)
class InfoStrings:
    """
    Strings for info display
    """

    # Registers
    REG_PC: str = "PC"
    REG_SP: str = "SP"
    REG_X: str = "X"
    REG_Y: str = "Y"
    REG_Z: str = "Z"
    REG_FLAGS: str = "FLAGS"

    # Program info
    ROM_PATH: str = "ROM Path: {path}"
    ROM_SIZE: str = "ROM Size: {size} bytes"
    INITIALIZED: str = "Initialized: {value}"

    # CPU state
    CYCLE: str = "Cycle: {cycle}"
    INSTRUCTION: str = "Instruction: 0x{opcode:02X} ({mnemonic})"
    STATUS_RUNNING: str = "RUNNING"
    STATUS_HALTED: str = "HALTED"
    STATUS_LABEL: str = "Status: {status}"

    # History
    NO_HISTORY: str = "No execution history"


@dataclass(frozen=True)
class SettingsStrings:
    """
    Settings messages
    """

    DISASM_ON_STEP: str = "Disassembly on step: {value}"
    DISASM_CONTEXT: str = "Disassembly context: {count} lines"


@dataclass(frozen=True)
class DebuggerStrings:
    ui: UIStrings = field(default_factory=UIStrings)
    execution: ExecutionStrings = field(default_factory=ExecutionStrings)
    breakpoints: BreakpointStrings = field(default_factory=BreakpointStrings)
    watches: WatchStrings = field(default_factory=WatchStrings)
    errors: ErrorStrings = field(default_factory=ErrorStrings)
    usage: UsageStrings = field(default_factory=UsageStrings)
    info: InfoStrings = field(default_factory=InfoStrings)
    settings: SettingsStrings = field(default_factory=SettingsStrings)
