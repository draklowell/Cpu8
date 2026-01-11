#!/usr/bin/env python3
"""
Dragonfly 8b9m GDB CLI
Interactive debugger for the CPU8 simulator with GDB-style commands.
"""

import cmd
import os
import sys

from debug.base import DebuggerCore
from debug.breakpoint import BreakpointManager
from debug.color import Color, colored, print_header, print_separator
from debug.disassembler import Disassembler
from debug.state import CPUState
from debug.ui import DebuggerStrings
from debug.watch import Watch, WatchManager

from simulator.config import load_microcode_data
from simulator.simulation import LogLevel, SimulationEngine, State, WaveformChunk

STRINGS = DebuggerStrings()


class DebuggerCLI(cmd.Cmd):
    """Interactive GDB-like debugger CLI."""

    intro = colored(STRINGS.ui.BANNER, Color.CYAN)
    prompt = colored(STRINGS.ui.PROMPT, Color.GREEN, Color.BOLD)

    def __init__(self, rom_path: str):
        super().__init__()
        self.debugger = DebuggerCore(rom_path)
        self.show_disasm_on_step = True
        self.disasm_context = 5

        self.aliases = {
            "n": "nexti",
            "ni": "nexti",
            "s": "step",
            "si": "stepi",
            "c": "continue",
            "r": "run",
            "q": "quit",
            "p": "print",
            "x": "examine",
            "i": "info",
            "b": "break",
            "d": "delete",
            "bt": "backtrace",
            "l": "list",
            "dis": "disassemble",
            "t": "tick",
        }

    def precmd(self, line: str) -> str:
        """Handle command aliases."""
        if not line:
            return line
        parts = line.split()
        cmd = parts[0]

        if "/" in cmd:
            base_cmd = cmd.split("/")[0]
            rest = cmd[len(base_cmd) :]
            if base_cmd in self.aliases:
                parts[0] = self.aliases[base_cmd] + rest
                return " ".join(parts)
        elif cmd in self.aliases:
            parts[0] = self.aliases[cmd]
            return " ".join(parts)
        return line

    def emptyline(self) -> bool:
        """Repeat last command on empty line (like GDB)."""
        if self.lastcmd:
            return self.onecmd(self.lastcmd)
        return False

    def do_run(self, arg: str) -> None:
        """
        Start or restart the program from the beginning.

        Usage:
            run

        Alias: r

        Description:
            Initializes the CPU (power on, reset sequence) and starts execution.
            If the program was already running, it will be restarted.

        Examples:
            (gdb-dragonfly) run
            (gdb-dragonfly) r
        """
        print(colored(STRINGS.execution.STARTING_PROGRAM, Color.YELLOW))
        self.debugger.initialized = False
        self.debugger.initialize()
        self._show_current_location()

    def do_nexti(self, arg: str) -> None:
        """
        Execute next CPU instruction(s).

        Usage:
            nexti [count]

        Alias: n, ni

        Arguments:
            count   - Number of instructions to execute (default: 1)

        Description:
            Executes one or more CPU clock cycles. Each cycle represents
            one instruction execution. Stops at breakpoints.

        Examples:
            (gdb-dragonfly) nexti       - Execute one instruction
            (gdb-dragonfly) nexti 5     - Execute 5 instructions
            (gdb-dragonfly) n           - Same as nexti
            (gdb-dragonfly) ni 10       - Execute 10 instructions
        """
        count = 1
        if arg:
            try:
                count = int(arg)
            except ValueError:
                print(colored(STRINGS.errors.INVALID_COUNT, Color.RED))
                return

        if not self.debugger.initialized:
            self.debugger.initialize()

        for i in range(count):
            if self.debugger.state.halted:
                print(colored(STRINGS.execution.PROGRAM_HALTED, Color.YELLOW))
                break

            state = self.debugger.step_instruction()

            # Check breakpoints
            bp = self.debugger.breakpoints.check(state.pc)
            if bp:
                print(
                    colored(
                        "\n"
                        + STRINGS.breakpoints.BREAKPOINT_HIT.format(
                            id=bp.id, address=state.pc
                        ),
                        Color.YELLOW,
                        Color.BOLD,
                    )
                )
                break

        self._show_current_location()

    def do_step(self, arg: str) -> None:
        """
        Step program (same as nexti).

        Usage:
            step [count]

        Alias: s

        Description:
            Equivalent to nexti. Steps through CPU instructions.

        Examples:
            (gdb-dragonfly) step        - Execute one instruction
            (gdb-dragonfly) step 3      - Execute 3 instructions
            (gdb-dragonfly) s           - Same as step
        """
        self.do_nexti(arg)

    def do_stepi(self, arg: str) -> None:
        """
        Step one instruction exactly.

        Usage:
            stepi [count]

        Alias: si

        Description:
            Equivalent to nexti. Steps through CPU instructions.

        Examples:
            (gdb-dragonfly) stepi       - Execute one instruction
            (gdb-dragonfly) si 5        - Execute 5 instructions
        """
        self.do_nexti(arg)

    def do_continue(self, arg: str) -> None:
        """
        Continue execution until breakpoint or halt.

        Usage:
            continue

        Alias: c

        Description:
            Continues running the program until a breakpoint is hit,
            the CPU halts, or 10000 cycles are executed.

        Examples:
            (gdb-dragonfly) continue
            (gdb-dragonfly) c
        """
        if not self.debugger.initialized:
            self.debugger.initialize()

        max_cycles = 10000
        print(colored(STRINGS.execution.CONTINUING, Color.YELLOW))

        for _ in range(max_cycles):
            if self.debugger.state.halted:
                print(
                    colored("\n" + STRINGS.execution.PROGRAM_HALTED_ALT, Color.YELLOW)
                )
                break

            state = self.debugger.step_instruction()
            bp = self.debugger.breakpoints.check(state.pc)
            if bp:
                print(
                    colored(
                        "\n"
                        + STRINGS.breakpoints.BREAKPOINT_HIT.format(
                            id=bp.id, address=state.pc
                        ),
                        Color.YELLOW,
                        Color.BOLD,
                    )
                )
                break
        else:
            print(
                colored(
                    "\n"
                    + STRINGS.execution.STOPPED_AFTER_CYCLES.format(
                        max_cycles=max_cycles
                    ),
                    Color.YELLOW,
                )
            )

        self._show_current_location()

    def do_info(self, arg: str) -> None:
        """
        Display various information about the debugger state.

        Usage:
            info <what>

        Alias: i

        Subcommands:
            info registers    (or: info reg, info r)   - Display all CPU registers
            info breakpoints  (or: info b)             - List all breakpoints
            info watches      (or: info w)             - List watch expressions
            info program                               - Show ROM and program info
            info cpu                                   - Show CPU state and cycle count
            info components   (or: info comp, info c)  - List hardware components
            info period                                - Show clock period setting

        Examples:
            (gdb-dragonfly) info registers
            (gdb-dragonfly) i reg
            (gdb-dragonfly) info components C1
            (gdb-dragonfly) i c
        """
        args = arg.split()
        if not args:
            print(STRINGS.usage.USAGE_INFO)
            return

        subcmd = args[0].lower()

        if subcmd in ("registers", "reg", "r"):
            self._show_registers()
        elif subcmd in ("breakpoints", "break", "b"):
            self._show_breakpoints()
        elif subcmd in ("watches", "watch", "w"):
            self._show_watches()
        elif subcmd == "program":
            self._show_program_info()
        elif subcmd == "cpu":
            self._show_cpu_state()
        elif subcmd in ("components", "comp", "c"):
            filter_arg = args[1] if len(args) > 1 else ""
            self.do_components(filter_arg)
        elif subcmd == "period":
            self.do_period("")
        else:
            print(STRINGS.errors.UNKNOWN_INFO_CMD.format(subcmd=subcmd))

    def do_registers(self, arg: str) -> None:
        """
        Display all CPU registers.

        Usage:
            registers

        Alias: reg

        Description:
            Shows PC, SP, X, Y, Z register pairs and FLAGS.
            16-bit registers X, Y, Z are shown both as combined
            values and as individual high/low bytes.

        Examples:
            (gdb-dragonfly) registers
            (gdb-dragonfly) reg
        """
        self._show_registers()

    def do_print(self, arg: str) -> None:
        """
        Print value of a register or expression.

        Usage:
            print <expression>

        Alias: p

        Arguments:
            expression  - Register name or expression to evaluate

        Available registers:
            pc, sp      - Program Counter, Stack Pointer
            x, y, z     - 16-bit register pairs
            xh, xl      - X register high/low bytes
            yh, yl      - Y register high/low bytes
            zh, zl      - Z register high/low bytes
            flags, fr   - Flags register
            ac          - Accumulator

        Examples:
            (gdb-dragonfly) print pc        - Print program counter
            (gdb-dragonfly) print $sp       - Print stack pointer ($ optional)
            (gdb-dragonfly) p zh            - Print ZH register
            (gdb-dragonfly) p x             - Print X register (16-bit)
        """
        if not arg:
            print(STRINGS.usage.USAGE_PRINT)
            return

        name = arg.strip().lstrip("$")
        value = self.debugger.get_register_value(name)

        if value is not None:
            print(f"{name} = {colored(f'0x{value:04X}', Color.BRIGHT_CYAN)} ({value})")
        else:
            print(colored(STRINGS.errors.UNKNOWN_REGISTER.format(name=name), Color.RED))

    def do_examine(self, arg: str) -> None:
        """
        Examine memory contents.

        Usage:
            examine[/FMT] <address>
            x[/FMT] <address>

        Alias: x

        Arguments:
            address - Memory address (hex with 0x prefix or decimal)
            FMT     - Optional format: [count][format]
                      count  - Number of units to display
                      format - b=bytes, h=halfwords, w=words, i=instructions

        Description:
            Displays memory contents at the specified address.
            Can also disassemble instructions with /i format.

        Examples:
            (gdb-dragonfly) x 0x100         - Examine 16 bytes at 0x100
            (gdb-dragonfly) x/16b 0x100     - Examine 16 bytes
            (gdb-dragonfly) x/8h 0x200      - Examine 8 halfwords (16-bit)
            (gdb-dragonfly) x/8i 0x100      - Disassemble 8 instructions
            (gdb-dragonfly) x/32b pc        - Examine 32 bytes at current PC
        """
        if not arg:
            print(STRINGS.usage.USAGE_EXAMINE)
            return

        count = 16
        fmt = "b"

        if arg.startswith("/"):
            # Format: /8i 0x100
            space_idx = arg.find(" ")
            if space_idx == -1:
                print(STRINGS.usage.USAGE_EXAMINE)
                return
            fmt_str = arg[1:space_idx]
            addr_str = arg[space_idx + 1 :].strip()

            if fmt_str and fmt_str[-1] in "bhwi":
                fmt = fmt_str[-1]
                if len(fmt_str) > 1:
                    try:
                        count = int(fmt_str[:-1])
                    except ValueError:
                        pass
            elif fmt_str:
                try:
                    count = int(fmt_str)
                except ValueError:
                    pass
        else:
            parts = arg.split()
            addr_str = parts[-1]

            if len(parts) > 1 and parts[0].startswith("/"):
                fmt_str = parts[0][1:]
                # Parse count and format
                if fmt_str and fmt_str[-1] in "bhwi":
                    fmt = fmt_str[-1]
                    if len(fmt_str) > 1:
                        try:
                            count = int(fmt_str[:-1])
                        except ValueError:
                            pass
                elif fmt_str:
                    try:
                        count = int(fmt_str)
                    except ValueError:
                        pass

        try:
            if addr_str.startswith("0x"):
                address = int(addr_str, 16)
            else:
                address = int(addr_str)
        except ValueError:
            reg_val = self.debugger.get_register_value(addr_str)
            if reg_val is not None:
                address = reg_val
            else:
                print(
                    colored(
                        STRINGS.errors.INVALID_ADDRESS.format(address=addr_str),
                        Color.RED,
                    )
                )
                return

        if fmt == "i":
            self._disassemble_at(address, count)
        else:
            self._examine_memory(address, count, fmt)

    def do_disassemble(self, arg: str) -> None:
        """
        Disassemble instructions from ROM.

        Usage:
            disassemble [address] [count]

        Alias: dis

        Arguments:
            address - Starting address (default: current PC)
            count   - Number of instructions to show (default: 10)

        Description:
            Shows disassembled instructions from ROM. Displays address,
            raw bytes, and mnemonic for each instruction.

        Examples:
            (gdb-dragonfly) disassemble             - Disassemble at current PC
            (gdb-dragonfly) disassemble 0x100       - Disassemble at 0x100
            (gdb-dragonfly) disassemble 0x100 20    - Disassemble 20 instructions
            (gdb-dragonfly) dis 0x0 50              - Show first 50 instructions
        """
        args = arg.split()

        address = self.debugger.state.pc
        count = 10

        if len(args) >= 1:
            try:
                address = int(args[0], 16) if args[0].startswith("0x") else int(args[0])
            except ValueError:
                print(
                    colored(
                        STRINGS.errors.INVALID_ADDRESS.format(address=args[0]),
                        Color.RED,
                    )
                )
                return

        if len(args) >= 2:
            try:
                count = int(args[1])
            except ValueError:
                pass

        self._disassemble_at(address, count)

    def do_list(self, arg: str) -> None:
        """
        List disassembly around current location or specified address.

        Usage:
            list [address]

        Alias: l

        Arguments:
            address - Center address (default: current PC)

        Description:
            Shows 20 instructions centered around the specified address.
            Current instruction is highlighted.

        Examples:
            (gdb-dragonfly) list        - List around current PC
            (gdb-dragonfly) list 0x100  - List around 0x100
            (gdb-dragonfly) l           - Same as list
        """
        address = self.debugger.state.pc
        if arg:
            try:
                address = int(arg, 16) if arg.startswith("0x") else int(arg)
            except ValueError:
                pass

        start = max(0, address - 10)
        self._disassemble_at(start, 20, highlight=address)

    def do_break(self, arg: str) -> None:
        """
        Set a breakpoint at specified address.

        Usage:
            break <address>

        Alias: b

        Arguments:
            address - Memory address (hex with 0x or decimal)

        Description:
            Sets a breakpoint. Execution will stop when PC reaches
            this address. Use 'info breakpoints' to list all breakpoints.

        Examples:
            (gdb-dragonfly) break 0x100     - Set breakpoint at 0x100
            (gdb-dragonfly) break 256       - Set breakpoint at address 256
            (gdb-dragonfly) b 0x0           - Set breakpoint at start
        """
        if not arg:
            print(STRINGS.usage.USAGE_BREAK)
            return

        try:
            if arg.startswith("0x"):
                address = int(arg, 16)
            else:
                address = int(arg)
        except ValueError:
            print(
                colored(STRINGS.errors.INVALID_ADDRESS.format(address=arg), Color.RED)
            )
            return

        bp = self.debugger.breakpoints.add(address)
        print(
            colored(
                STRINGS.breakpoints.BREAKPOINT_SET.format(id=bp.id, address=address),
                Color.GREEN,
            )
        )

    def do_delete(self, arg: str) -> None:
        """
        Delete breakpoint(s).

        Usage:
            delete [breakpoint-id]

        Alias: d

        Arguments:
            breakpoint-id - ID of breakpoint to delete (optional)

        Description:
            Deletes a specific breakpoint by ID, or all breakpoints
            if no ID is specified.

        Examples:
            (gdb-dragonfly) delete 1    - Delete breakpoint #1
            (gdb-dragonfly) delete      - Delete all breakpoints
            (gdb-dragonfly) d 2         - Delete breakpoint #2
        """
        if not arg:
            count = self.debugger.breakpoints.clear_all()
            print(
                colored(
                    STRINGS.breakpoints.BREAKPOINTS_DELETED.format(count=count),
                    Color.YELLOW,
                )
            )
            return

        try:
            bp_id = int(arg)
            if self.debugger.breakpoints.remove(bp_id):
                print(
                    colored(
                        STRINGS.breakpoints.BREAKPOINT_DELETED.format(id=bp_id),
                        Color.GREEN,
                    )
                )
            else:
                print(
                    colored(
                        STRINGS.breakpoints.BREAKPOINT_NOT_FOUND.format(id=bp_id),
                        Color.RED,
                    )
                )
        except ValueError:
            print(colored(STRINGS.breakpoints.INVALID_BREAKPOINT_ID, Color.RED))

    def do_enable(self, arg: str) -> None:
        """
        Enable a disabled breakpoint.

        Usage:
            enable <breakpoint-id>

        Arguments:
            breakpoint-id - ID of breakpoint to enable

        Examples:
            (gdb-dragonfly) enable 1    - Enable breakpoint #1
        """
        if not arg:
            print(STRINGS.usage.USAGE_ENABLE)
            return

        try:
            bp_id = int(arg)
            if self.debugger.breakpoints.enable(bp_id):
                print(
                    colored(
                        STRINGS.breakpoints.BREAKPOINT_ENABLED.format(id=bp_id),
                        Color.GREEN,
                    )
                )
            else:
                print(
                    colored(
                        STRINGS.breakpoints.BREAKPOINT_NOT_FOUND.format(id=bp_id),
                        Color.RED,
                    )
                )
        except ValueError:
            print(colored(STRINGS.breakpoints.INVALID_BREAKPOINT_ID, Color.RED))

    def do_disable(self, arg: str) -> None:
        """
        Disable a breakpoint without deleting it.

        Usage:
            disable <breakpoint-id>

        Arguments:
            breakpoint-id - ID of breakpoint to disable

        Description:
            Disables a breakpoint. The breakpoint remains in the list
            but won't trigger. Use 'enable' to re-enable it.

        Examples:
            (gdb-dragonfly) disable 1   - Disable breakpoint #1
        """
        if not arg:
            print(STRINGS.usage.USAGE_DISABLE)
            return

        try:
            bp_id = int(arg)
            if self.debugger.breakpoints.disable(bp_id):
                print(
                    colored(
                        STRINGS.breakpoints.BREAKPOINT_DISABLED.format(id=bp_id),
                        Color.GREEN,
                    )
                )
            else:
                print(
                    colored(
                        STRINGS.breakpoints.BREAKPOINT_NOT_FOUND.format(id=bp_id),
                        Color.RED,
                    )
                )
        except ValueError:
            print(colored(STRINGS.breakpoints.INVALID_BREAKPOINT_ID, Color.RED))

    def do_watch(self, arg: str) -> None:
        """
        Add a watch expression to monitor.

        Usage:
            watch <expression>

        Arguments:
            expression - Register or expression to watch

        Description:
            Adds an expression to the watch list. Use 'info watches'
            to see current values of all watched expressions.

        Examples:
            (gdb-dragonfly) watch pc    - Watch program counter
            (gdb-dragonfly) watch x     - Watch X register
            (gdb-dragonfly) watch sp    - Watch stack pointer
        """
        if not arg:
            print(STRINGS.usage.USAGE_WATCH)
            return

        watch = self.debugger.watches.add(arg)
        print(
            colored(
                STRINGS.watches.WATCH_SET.format(id=watch.id, expression=arg),
                Color.GREEN,
            )
        )

    def do_backtrace(self, arg: str) -> None:
        """
        Show execution history (instruction backtrace).

        Usage:
            backtrace [count]

        Alias: bt

        Arguments:
            count - Number of history entries to show (default: 10)

        Description:
            Shows the last N executed instructions with their cycle
            numbers, addresses, and mnemonics.

        Examples:
            (gdb-dragonfly) backtrace       - Show last 10 instructions
            (gdb-dragonfly) backtrace 20    - Show last 20 instructions
            (gdb-dragonfly) bt              - Same as backtrace
        """
        count = 10
        if arg:
            try:
                count = int(arg)
            except ValueError:
                pass

        history = self.debugger.instruction_history[-count:]
        if not history:
            print(STRINGS.info.NO_HISTORY)
            return

        print_header(STRINGS.ui.HEADER_INSTRUCTION_HISTORY)
        for i, state in enumerate(reversed(history)):
            age = len(history) - i
            print(
                f"  {colored(f'#{age:3}', Color.GRAY)} "
                f"cycle {state.cycle:5} @ "
                f"{colored(f'0x{state.pc:04X}', Color.CYAN)}: "
                f"{colored(state.mnemonic, Color.YELLOW)}"
            )

    def do_status(self, arg: str) -> None:
        """
        Show current debugger and CPU status.

        Usage:
            status

        Description:
            Displays current cycle count, program counter, current
            instruction, and whether the CPU is running or halted.

        Examples:
            (gdb-dragonfly) status
        """
        self._show_cpu_state()

    def do_reset(self, arg: str) -> None:
        """
        Reset the CPU to initial state.

        Usage:
            reset

        Description:
            Resets all CPU state including registers, cycle count,
            and execution history. The CPU will need to be started
            again with 'run'.

        Examples:
            (gdb-dragonfly) reset
        """
        print(colored(STRINGS.execution.RESETTING_CPU, Color.YELLOW))
        self.debugger.initialized = False
        self.debugger.state = CPUState()
        self.debugger.instruction_history.clear()
        print(colored(STRINGS.execution.RESET_COMPLETE, Color.GREEN))

    def do_set(self, arg: str) -> None:
        """
        Set debugger options or component variables.

        Usage:
            set <option> <value>

        Options:
            set disasm on|off                       - Toggle disassembly display after each step
            set context <count>                     - Set number of context lines in disassembly
            set period <ticks>                      - Set clock period (simulator ticks per CPU cycle)
            set var <component> <variable> <value>  - Set a component variable

        Description:
            Configures debugger behavior and allows setting internal
            component variables for simulation control.

        Examples:
            (gdb-dragonfly) set disasm off          - Disable auto-disassembly
            (gdb-dragonfly) set context 10          - Show 10 lines of context
            (gdb-dragonfly) set period 800          - Set clock period to 800 ticks
            (gdb-dragonfly) set var I:PAD2 RESET 1  - Set RESET signal high
            (gdb-dragonfly) set var I:PAD2 WAIT 0   - Set WAIT signal low
        """
        args = arg.split()
        if len(args) < 2:
            print(STRINGS.usage.USAGE_SET)
            return

        option = args[0].lower()
        value = args[1]

        if option == "disasm":
            self.show_disasm_on_step = value.lower() in ("on", "true", "1", "yes")
            print(
                STRINGS.settings.DISASM_ON_STEP.format(value=self.show_disasm_on_step)
            )
        elif option == "context":
            try:
                self.disasm_context = int(value)
                print(STRINGS.settings.DISASM_CONTEXT.format(count=self.disasm_context))
            except ValueError:
                print(STRINGS.errors.INVALID_CONTEXT)
        elif option == "period":
            try:
                period = int(value)
                if period < 2:
                    print(colored("Period must be at least 2", Color.RED))
                    return
                self.debugger.set_period(period)
                print(
                    colored(
                        f"Clock period set to {period} simulator ticks", Color.GREEN
                    )
                )
            except ValueError:
                print(colored("Invalid period value", Color.RED))
        elif option == "var":
            if len(args) < 4:
                print(
                    colored("Usage: set var <component> <variable> <value>", Color.RED)
                )
                return
            component = args[1]
            var_name = args[2]
            try:
                var_value = int(args[3])
            except ValueError:
                print(colored("Invalid value", Color.RED))
                return
            if self.debugger.set_variable(component, var_name, var_value):
                print(colored(f"Set {component}:{var_name} = {var_value}", Color.GREEN))
            else:
                print(
                    colored(f"Failed to set variable (component not found?)", Color.RED)
                )

    def do_tick(self, arg: str) -> None:
        """
        Execute low-level simulator ticks.

        Usage:
            tick [count]

        Alias: t

        Arguments:
            count - Number of simulator ticks to execute (default: 1)

        Description:
            Executes simulator ticks at the lowest level. This is more
            granular than 'nexti' which executes full CPU clock cycles.
            One CPU cycle = period/2 ticks (for each clock phase).
            Use this for detailed timing analysis.

        Examples:
            (gdb-dragonfly) tick            - Execute one simulator tick
            (gdb-dragonfly) tick 100        - Execute 100 simulator ticks
            (gdb-dragonfly) t 50            - Execute 50 ticks
        """
        count = 1
        if arg:
            try:
                count = int(arg)
            except ValueError:
                print(colored("Invalid count", Color.RED))
                return

        if not self.debugger.initialized:
            self.debugger.initialize()

        for _ in range(count):
            chunk = self.debugger.tick_simulator()
            self._print_logs(chunk)

        print(colored(f"Executed {count} simulator tick(s)", Color.GREEN))

    def do_period(self, arg: str) -> None:
        """
        Get or set clock period.

        Usage:
            period [value]

        Arguments:
            value - New period in simulator ticks (optional)

        Description:
            Controls how many simulator ticks make up one CPU clock cycle.
            Higher values = slower but more accurate simulation.
            Lower values = faster but may miss timing details.
            Default is 800 ticks.

        Examples:
            (gdb-dragonfly) period          - Show current period
            (gdb-dragonfly) period 800      - Set period to 800 ticks
            (gdb-dragonfly) period 100      - Set faster period (less accurate)
        """
        if not arg:
            print(
                f"Clock period: {colored(str(self.debugger.period), Color.CYAN)} simulator ticks"
            )
            return

        try:
            period = int(arg)
            if period < 2:
                print(colored("Period must be at least 2", Color.RED))
                return
            self.debugger.set_period(period)
            print(colored(f"Clock period set to {period} simulator ticks", Color.GREEN))
        except ValueError:
            print(colored("Invalid period value", Color.RED))

    def do_rn(self, arg: str) -> None:
        """
        Read network value(s) - displays state of simulation networks.

        Usage:
            rn <network> [network2 ...]
            rn <prefix>N - <prefix>M      (range specification)

        Arguments:
            network - Network name (add '!' suffix if not present)

        Output:
            Binary string where each character represents a network:
            - 1 = HIGH (driven high)
            - 0 = LOW (driven low)
            - Z = FLOATING (not driven)
            - X = CONFLICT (multiple drivers)

        Description:
            Reads the current state of one or more networks. Networks
            can be specified individually, as a space-separated list,
            or as a range (high to low, using ' - ' separator).

        Examples:
            (gdb-dragonfly) rn C3:/STATE0!              - Read single network
            (gdb-dragonfly) rn NET1 NET2 NET3           - Read multiple (left=MSB)
            (gdb-dragonfly) rn C3:/STATE16 - C3:/STATE0 - Read 17-bit bus
            (gdb-dragonfly) rn PC:/DATA7 - PC:/DATA0    - Read 8-bit data bus
            (gdb-dragonfly) rn I:/ADDRESS15 - I:/ADDRESS0  - Read 16-bit address
        """
        if not arg:
            print(
                colored(
                    "Usage: rn <network> [network2 ...] or rn <start> - <end>",
                    Color.RED,
                )
            )
            return

        if not self.debugger.initialized:
            self.debugger.initialize()

        # Check if it's a range specification
        if " - " in arg:
            networks = self.debugger.expand_network_range(arg)
            if not networks:
                print(colored("Invalid range specification", Color.RED))
                return
        else:
            # Multiple networks or single network
            networks = []
            for n in arg.split():
                if not n.endswith("!"):
                    n += "!"
                networks.append(n)

        binary_str = self.debugger.read_networks_as_binary(networks)
        int_val = self.debugger.read_networks_as_int(networks)

        # Print result
        print_header(f"Network Read ({len(networks)} bits)")
        print(f"  Binary: {colored(binary_str, Color.BRIGHT_CYAN)}")
        if int_val is not None:
            hex_width = (len(networks) + 3) // 4
            print(
                f"  Hex:    {colored(f'0x{int_val:0{hex_width}X}', Color.BRIGHT_YELLOW)}"
            )
            print(f"  Dec:    {colored(str(int_val), Color.WHITE)}")
        else:
            print(f"  {colored('(contains floating or conflict states)', Color.GRAY)}")
        print_separator()

    def do_rc(self, arg: str) -> None:
        """
        Read component pin by alias - shows pin state using friendly name.

        Usage:
            rc <component> <pin_alias>

        Arguments:
            component  - Component name (e.g., C1:DECODER1, I:PAD2)
            pin_alias  - Pin alias/name (e.g., Y0, CLOCK, VCC)

        Description:
            Reads a single component pin using its alias name instead
            of network name. Shows both the network name and current state.
            If pin not found, shows available pins for that component.

        Examples:
            (gdb-dragonfly) rc C1:DECODER1 Y0   - Read Y0 output of decoder
            (gdb-dragonfly) rc I:PAD2 CLOCK     - Read clock input state
            (gdb-dragonfly) rc I:PAD2 N_HALT    - Read halt signal
            (gdb-dragonfly) rc PC:U4 Q          - Read Q output of register

        See also:
            pins <component>  - List all pins for a component
            components        - List all components
        """
        args = arg.split()
        if len(args) < 2:
            print(colored("Usage: rc <component> <pin_alias>", Color.RED))
            return

        if not self.debugger.initialized:
            self.debugger.initialize()

        component = args[0]
        pin_alias = args[1]

        network, state = self.debugger.get_component_pin(component, pin_alias)
        if network is None:
            print(
                colored(
                    f"Component or pin not found: {component}:{pin_alias}", Color.RED
                )
            )
            pins = self.debugger.get_component_pins(component)
            if pins:
                print(colored(f"Available pins for {component}:", Color.YELLOW))
                for alias in sorted(pins.keys()):
                    print(f"  {alias}")
            else:
                print(colored(f"Component '{component}' not found", Color.RED))
                print(
                    colored(
                        "Use 'info components' to list available components", Color.GRAY
                    )
                )
            return

        state_str = self._format_state(state)
        print(f"{component}:{pin_alias} ({network}) = {state_str}")

    def do_pins(self, arg: str) -> None:
        """
        Show all pins for a component with their current states.

        Usage:
            pins <component>

        Arguments:
            component - Component name (e.g., C1:DECODER1, I:PAD2)

        Description:
            Lists all pin aliases for a component, their corresponding
            network names, and current signal states. Useful for
            understanding component connectivity and debugging.

        Examples:
            (gdb-dragonfly) pins C1:DECODER1    - Show decoder pins
            (gdb-dragonfly) pins I:PAD2         - Show interface pad pins
            (gdb-dragonfly) pins PC:U4          - Show program counter register pins
            (gdb-dragonfly) pins REG:ZH1        - Show ZH register pins

        See also:
            rc <component> <pin>  - Read specific pin
            components            - List all components
        """
        if not arg:
            print(colored("Usage: pins <component>", Color.RED))
            return

        if not self.debugger.initialized:
            self.debugger.initialize()

        component = arg.strip()
        pins = self.debugger.get_component_pins(component)

        if pins is None:
            print(colored(f"Component not found: {component}", Color.RED))
            print(
                colored(
                    "Use 'info components' to list available components", Color.GRAY
                )
            )
            return

        print_header(f"Pins: {component}")
        for alias, network in sorted(pins.items()):
            state = self.debugger.get_network_state(network)
            state_str = self._format_state(state)
            print(
                f"  {colored(alias, Color.CYAN):12} -> {colored(network, Color.GRAY):30} = {state_str}"
            )
        print_separator()

    def do_components(self, arg: str) -> None:
        """
        List all hardware components or filter by prefix.

        Usage:
            components [filter]

        Arguments:
            filter - Optional prefix to filter component names

        Description:
            Lists all components in the simulation. Components are named
            using the format MODULE:COMPONENT (e.g., C1:DECODER1).
            Use 'pins <component>' to see pins for a specific component.

        Module prefixes:
            ALU - ALU hub
            C1  - Core 1 (instruction decoder)
            C2  - Core 2
            C3  - Core 3 (microcode)
            I   - Interface (external connections)
            PC  - Program counter
            REG - Register file
            SP  - Stack pointer

        Examples:
            (gdb-dragonfly) components         - List all components
            (gdb-dragonfly) components C1      - List Core 1 components
            (gdb-dragonfly) components I:      - List interface components
            (gdb-dragonfly) components REG     - List register components
        """
        if not self.debugger.initialized:
            self.debugger.initialize()

        components = self.debugger.list_components()
        filter_prefix = arg.strip() if arg else None

        if filter_prefix:
            components = [c for c in components if c.startswith(filter_prefix)]

        print_header("Components")
        for comp in sorted(components):
            print(f"  {comp}")
        print(f"\n  Total: {len(components)} components")
        print_separator()

    def _format_state(self, state: State | None) -> str:
        """Format a network state for display."""
        if state == State.HIGH:
            return colored("HIGH (1)", Color.BRIGHT_GREEN)
        elif state == State.LOW:
            return colored("LOW (0)", Color.BRIGHT_BLUE)
        elif state == State.FLOATING:
            return colored("FLOATING (Z)", Color.YELLOW)
        elif state == State.CONFLICT:
            return colored("CONFLICT (X)", Color.BRIGHT_RED)
        else:
            return colored("UNKNOWN (?)", Color.GRAY)

    def _print_logs(self, chunk) -> None:
        """Print logs from a waveform chunk."""
        for level, source, message in chunk.logs:
            if level == LogLevel.INFO:
                color = Color.BLUE
            elif level == LogLevel.OK:
                color = Color.GREEN
            elif level == LogLevel.WARNING:
                color = Color.YELLOW
            elif level == LogLevel.ERROR:
                color = Color.RED
            else:
                color = Color.GRAY
            print(colored(f"[{chunk.tick}][{source}] {message}", color))

    def do_quit(self, arg: str) -> bool:
        """
        Exit the debugger.

        Usage:
            quit

        Alias: q

        Description:
            Exits the debugger. Can also use Ctrl+D.

        Examples:
            (gdb-dragonfly) quit
            (gdb-dragonfly) q
        """
        print(colored(STRINGS.ui.GOODBYE, Color.CYAN))
        return True

    def do_EOF(self, arg: str) -> bool:
        """Handle Ctrl+D."""
        print()
        return self.do_quit(arg)

    def _show_current_location(self) -> None:
        """Show current PC and instruction."""
        state = self.debugger.state

        print()
        mnemonic, size, raw_bytes = self.debugger.disasm.disassemble_at(state.pc)
        bytes_str = " ".join(f"{b:02X}" for b in raw_bytes)

        print(
            f"{colored('►', Color.GREEN)} {colored(f'0x{state.pc:04X}', Color.CYAN, Color.BOLD)}: "
            f"{colored(bytes_str, Color.GRAY):12} "
            f"{colored(mnemonic, Color.YELLOW, Color.BOLD)}"
        )

        if self.show_disasm_on_step:
            print()
            instructions = self.debugger.disasm.disassemble_range(
                state.pc + size, self.disasm_context
            )
            for addr, instr, _, raw in instructions:
                bytes_str = " ".join(f"{b:02X}" for b in raw)
                print(
                    f"  {colored(f'0x{addr:04X}', Color.GRAY)}: "
                    f"{bytes_str:12} {instr}"
                )

        print()

    def _show_registers(self) -> None:
        """Display all registers in a nice format."""
        state = self.debugger.state

        print_header(STRINGS.ui.HEADER_REGISTERS)

        # Main registers
        x = (state.xh << 8) | state.xl
        y = (state.yh << 8) | state.yl
        z = (state.zh << 8) | state.zl

        print(
            f"  {colored(STRINGS.info.REG_PC, Color.BRIGHT_CYAN):>4} = {colored(f'0x{state.pc:04X}', Color.WHITE, Color.BOLD)}"
            f"   ({state.pc:5})"
        )
        print(
            f"  {colored(STRINGS.info.REG_SP, Color.BRIGHT_CYAN):>4} = {colored(f'0x{state.sp:04X}', Color.WHITE, Color.BOLD)}"
            f"   ({state.sp:5})"
        )
        print()

        # 16-bit register pairs
        print(
            f"  {colored(STRINGS.info.REG_X, Color.BRIGHT_YELLOW):>4} = {colored(f'0x{x:04X}', Color.WHITE)}"
            f"     XH={colored(f'0x{state.xh:02X}', Color.GRAY)} XL={colored(f'0x{state.xl:02X}', Color.GRAY)}"
        )
        print(
            f"  {colored(STRINGS.info.REG_Y, Color.BRIGHT_YELLOW):>4} = {colored(f'0x{y:04X}', Color.WHITE)}"
            f"     YH={colored(f'0x{state.yh:02X}', Color.GRAY)} YL={colored(f'0x{state.yl:02X}', Color.GRAY)}"
        )
        print(
            f"  {colored(STRINGS.info.REG_Z, Color.BRIGHT_YELLOW):>4} = {colored(f'0x{z:04X}', Color.WHITE)}"
            f"     ZH={colored(f'0x{state.zh:02X}', Color.GRAY)} ZL={colored(f'0x{state.zl:02X}', Color.GRAY)}"
        )
        print()

        # Flags
        flags_str = f"{state.flags:08b}"
        print(
            f"  {colored(STRINGS.info.REG_FLAGS, Color.BRIGHT_MAGENTA):>5} = {colored(f'0b{flags_str}', Color.WHITE)}"
            f"  (0x{state.flags:02X})"
        )

        print_separator()

    def _show_breakpoints(self) -> None:
        """Display all breakpoints."""
        breakpoints = self.debugger.breakpoints.list_all()

        print_header(STRINGS.ui.HEADER_BREAKPOINTS)

        if not breakpoints:
            print(f"  {STRINGS.breakpoints.NO_BREAKPOINTS}")
        else:
            for bp in breakpoints:
                print(f"  {bp}")

        print_separator()

    def _show_watches(self) -> None:
        """Display all watches."""
        watches = self.debugger.watches.list_all()

        print_header(STRINGS.ui.HEADER_WATCHES)

        if not watches:
            print(f"  {STRINGS.watches.NO_WATCHES}")
        else:
            for w in watches:
                value = self.debugger.get_register_value(w.expression)
                if value is not None:
                    print(
                        f"  #{w.id}: {w.expression} = {colored(f'0x{value:04X}', Color.CYAN)}"
                    )
                else:
                    print(f"  #{w.id}: {w.expression} = {colored('???', Color.RED)}")

        print_separator()

    def _show_program_info(self) -> None:
        """Display program information."""
        print_header(STRINGS.ui.HEADER_PROGRAM_INFO)
        print(f"  {STRINGS.info.ROM_PATH.format(path=self.debugger.rom_path)}")
        print(f"  {STRINGS.info.ROM_SIZE.format(size=len(self.debugger.rom))}")
        print(f"  {STRINGS.info.INITIALIZED.format(value=self.debugger.initialized)}")
        print_separator()

    def _show_cpu_state(self) -> None:
        """Display detailed CPU state."""
        state = self.debugger.state

        print_header(STRINGS.ui.HEADER_CPU_STATE)

        print(
            f"  {STRINGS.info.CYCLE.format(cycle=colored(str(state.cycle), Color.WHITE, Color.BOLD))}"
        )
        print(f"  {STRINGS.info.REG_PC}: {colored(f'0x{state.pc:04X}', Color.CYAN)}")
        print(
            f"  {STRINGS.info.INSTRUCTION.format(opcode=state.instruction, mnemonic=colored(state.mnemonic, Color.YELLOW, Color.BOLD))}"
        )

        status = (
            colored(STRINGS.info.STATUS_RUNNING, Color.GREEN)
            if not state.halted
            else colored(STRINGS.info.STATUS_HALTED, Color.RED)
        )
        print(f"  {STRINGS.info.STATUS_LABEL.format(status=status)}")

        print_separator()

    def _disassemble_at(
        self, address: int, count: int, highlight: int | None = None
    ) -> None:
        """Disassemble and display instructions."""
        instructions = self.debugger.disasm.disassemble_range(address, count)

        print_header(STRINGS.ui.HEADER_DISASSEMBLY.format(address=address))

        for addr, mnemonic, size, raw_bytes in instructions:
            bytes_str = " ".join(f"{b:02X}" for b in raw_bytes)

            bp_marker = "  "
            bp = self.debugger.breakpoints._address_index.get(addr)
            if bp:
                bp_marker = colored("●", Color.RED) + " "

            if highlight is not None and addr == highlight:
                print(
                    colored(
                        f"{bp_marker}► 0x{addr:04X}: {bytes_str:12} {mnemonic}",
                        Color.GREEN,
                        Color.BOLD,
                    )
                )
            else:
                print(
                    f"{bp_marker}  {colored(f'0x{addr:04X}', Color.CYAN)}: "
                    f"{colored(bytes_str, Color.GRAY):12} {mnemonic}"
                )

        print_separator()

    def _examine_memory(self, address: int, count: int, fmt: str) -> None:
        """Examine and display memory."""
        data = self.debugger.read_memory(address, count)

        print_header(STRINGS.ui.HEADER_MEMORY.format(address=address))

        bytes_per_line = 16
        for i in range(0, len(data), bytes_per_line):
            line_addr = address + i
            line_data = data[i : i + bytes_per_line]

            hex_str = " ".join(f"{b:02X}" for b in line_data)
            hex_str = hex_str.ljust(bytes_per_line * 3 - 1)

            ascii_str = ""
            for b in line_data:
                if 32 <= b < 127:
                    ascii_str += chr(b)
                else:
                    ascii_str += "."

            print(
                f"  {colored(f'0x{line_addr:04X}', Color.CYAN)}: "
                f"{hex_str}  │{colored(ascii_str, Color.GRAY)}│"
            )

        print_separator()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="CPU8 GDB-like Debugger",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s program.bin          Start debugger with ROM file
  %(prog)s -c "run" program.bin Execute command and start interactive mode
        """,
    )
    parser.add_argument("rom", help="Path to ROM binary file")
    parser.add_argument("-c", "--command", help="Execute command on startup")
    parser.add_argument("-x", "--execute", help="Execute commands from file")

    args = parser.parse_args()

    if not os.path.exists(args.rom):
        print(colored(STRINGS.errors.ROM_NOT_FOUND.format(path=args.rom), Color.RED))
        sys.exit(1)

    try:
        cli = DebuggerCLI(args.rom)

        # Execute startup command
        if args.command:
            cli.onecmd(args.command)

        # Execute commands from file
        if args.execute and os.path.exists(args.execute):
            with open(args.execute) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        cli.onecmd(line)

        # Start interactive mode
        cli.cmdloop()

    except KeyboardInterrupt:
        print(colored("\n" + STRINGS.execution.INTERRUPTED, Color.YELLOW))
        sys.exit(0)
    except Exception as e:
        print(colored(STRINGS.errors.GENERAL_ERROR.format(message=e), Color.RED))
        raise


if __name__ == "__main__":
    main()
