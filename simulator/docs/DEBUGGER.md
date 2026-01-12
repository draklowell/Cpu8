# Dragonfly 8b9m GDB CLI - Debugger Documentation

Interactive debugger for the CPU8 simulator with GDB-style commands.

## Quick Start

```bash
# Start debugger with ROM file
python debugger.py program.bin

# Execute command on startup
python debugger.py -c "run" program.bin

# Execute commands from file
python debugger.py -x commands.txt program.bin
```

## Architecture Notes

### Instruction Encoding

Instructions are 1, 2, or 3 bytes:
- **1-byte**: Opcode only (e.g., `nop`, `hlt`, `ret`)
- **2-byte**: Opcode + byte operand (e.g., `ldi zh, 0x10`)
- **3-byte**: Opcode + word operand (e.g., `ldi sp, 0xFFFE`, `call 0x000D`)

### Endianness

Word operands (16-bit addresses/values) are stored in **big-endian** format:
- High byte first, then low byte
- Example: `ldi sp, 0xFFFE` is encoded as `14 FF FE`
  - `0x14` = opcode
  - `0xFF` = high byte
  - `0xFE` = low byte

### Accumulator (AC)

The Accumulator (AC) is the **XL register** — they are the same physical register:
- `ac` and `xl` refer to the same 8-bit register
- The X register pair consists of XH (high byte) and XL/AC (low byte)

## Command Reference

### Execution Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `run` | `r` | Start or restart the program |
| `nexti [count]` | `n`, `ni` | Execute next instruction(s) (full instruction) |
| `step [count]` | `s` | Step program (same as nexti) |
| `stepi [count]` | `si` | Step one clock cycle (more granular than nexti) |
| `continue` | `c` | Continue until breakpoint or halt |
| `reset` | - | Reset CPU to initial state |

#### Execution Granularity

The debugger provides three levels of execution control:

1. **`nexti`/`n`** — Execute a **full CPU instruction**
   - A 3-byte instruction (e.g., `ldi sp, 0xFFFE`) executes completely
   - PC advances by the instruction size (1, 2, or 3 bytes)

2. **`stepi`/`si`** — Execute one **clock cycle**
   - More granular than nexti
   - Useful for seeing CPU state mid-instruction

3. **`tick`/`t`** — Execute one **simulator tick**
   - Lowest level granularity
   - One clock cycle = period/2 ticks per phase

#### Examples
```
(gdb-dragonfly) run
(gdb-dragonfly) nexti 5        # Execute 5 full instructions
(gdb-dragonfly) stepi 10       # Execute 10 clock cycles
(gdb-dragonfly) continue       # Run until breakpoint
```

---

### Display Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `info <what>` | `i` | Display various information |
| `registers` | `reg` | Display all CPU registers |
| `print <expr>` | `p` | Print register/expression value |
| `examine [/FMT] <addr>` | `x` | Examine memory |
| `disassemble [addr] [count]` | `dis` | Disassemble instructions |
| `list [addr]` | `l` | List disassembly around location |
| `backtrace [count]` | `bt` | Show execution history |
| `status` | - | Show CPU status |

#### Register Display

The `registers` command shows all CPU registers:

```
--------- Registers ----------
  PC = 0x0009   (    9)
  SP = 0xFFFE   (65534)

  X = 0x000C     XH=0x00 AC=0x0C
  Y = 0x0000     YH=0x00 YL=0x00
  Z = 0x0800     ZH=0x08 ZL=0x00

  FLAGS = 0b00000000  (0x00)
------------------------------
```

> The X register line shows AC (Accumulator) instead of XL because AC = XL.

#### Info Subcommands
```
info registers      (or: info reg, info r)   - Display all CPU registers
info breakpoints    (or: info b)             - List all breakpoints
info watches        (or: info w)             - List watch expressions
info program                                 - Show ROM and program info
info cpu                                     - Show CPU state
info components     (or: info comp, info c)  - List hardware components
info period                                  - Show clock period
```

#### Examine Format
Format: `/[count][format]`
- `b` - bytes
- `h` - halfwords (16-bit)
- `w` - words (32-bit)
- `i` - instructions

#### Examples
```
(gdb-dragonfly) info registers
(gdb-dragonfly) print pc
(gdb-dragonfly) x/16b 0x100     # Examine 16 bytes at 0x100
(gdb-dragonfly) x/8i 0x0        # Disassemble 8 instructions
(gdb-dragonfly) disassemble 0x100 20
```

---

### Breakpoint Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `break <addr>` | `b` | Set breakpoint at address |
| `delete [id]` | `d` | Delete breakpoint(s) |
| `enable <id>` | - | Enable breakpoint |
| `disable <id>` | - | Disable breakpoint |

#### Examples
```
(gdb-dragonfly) break 0x100     # Set breakpoint
(gdb-dragonfly) info b          # List breakpoints
(gdb-dragonfly) delete 1        # Delete breakpoint #1
(gdb-dragonfly) delete          # Delete all breakpoints
```

---

### Watch Commands

| Command | Description |
|---------|-------------|
| `watch <expr>` | Add watch expression |

#### Examples
```
(gdb-dragonfly) watch pc        # Watch program counter
(gdb-dragonfly) watch x         # Watch X register
(gdb-dragonfly) info watches    # Show all watches
```

---

### Low-Level Simulation Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `tick [count]` | `t` | Execute simulator ticks (lowest level) |
| `period [value]` | - | Get/set clock period |
| `check [cycles]` | `sc` | Check for short circuits |

#### Simulation Levels

The CPU8 simulator operates at multiple levels:

```
┌─────────────────────────────────────────────────────────┐
│  nexti/n    Execute full instruction (1-3 bytes)        │
│             PC advances by instruction size             │
├─────────────────────────────────────────────────────────┤
│  stepi/si   Execute one clock cycle                     │
│             PC may advance by 1 byte                    │
├─────────────────────────────────────────────────────────┤
│  tick/t     Execute one simulator tick                  │
│             Lowest level (period/2 ticks = half cycle)  │
└─────────────────────────────────────────────────────────┘
```

- **tick**: Executes individual simulator ticks (lowest granularity)
- **period**: Controls simulator ticks per CPU clock cycle (default: 800)
- **check**: Runs simulation and checks for conflicts (short circuits) on rising clock edge

#### Examples
```
(gdb-dragonfly) tick            # Execute one simulator tick
(gdb-dragonfly) tick 100        # Execute 100 ticks
(gdb-dragonfly) period          # Show current period
(gdb-dragonfly) period 800      # Set period to 800 ticks
(gdb-dragonfly) check           # Check 1 clock cycle for short circuits
(gdb-dragonfly) check 10        # Check 10 clock cycles
(gdb-dragonfly) sc 100          # Check 100 cycles (alias)
```

---

### Network/Pin Read Commands

| Command | Description |
|---------|-------------|
| `rn <network> [...]` | Read network value(s) |
| `rc <component> <pin>` | Read component pin by alias |
| `pins <component>` | Show all pins for component |
| `components [filter]` | List components |

#### Network Output Format
- `1` - HIGH (driven high)
- `0` - LOW (driven low)
- `Z` - FLOATING (not driven)
- `X` - CONFLICT (multiple drivers)

#### Range Specification
Use ` - ` (with spaces) to specify a range from high bit to low bit:
```
rn C3:/STATE16 - C3:/STATE0    # Read 17 bits (16 down to 0)
rn PC:/DATA7 - PC:/DATA0       # Read 8-bit bus
```

#### Examples
```
(gdb-dragonfly) rn C3:/STATE0!              # Single network
(gdb-dragonfly) rn NET1 NET2 NET3           # Multiple networks
(gdb-dragonfly) rn C3:/STATE16 - C3:/STATE0 # Range (17 bits)

(gdb-dragonfly) rc C1:DECODER1 Y0           # Read decoder output
(gdb-dragonfly) rc I:PAD2 CLOCK             # Read clock input
(gdb-dragonfly) rc I:PAD2 N_HALT            # Read halt signal

(gdb-dragonfly) pins C1:DECODER1            # Show all decoder pins
(gdb-dragonfly) pins I:PAD2                 # Show interface pins

(gdb-dragonfly) components                  # List all components
(gdb-dragonfly) components C1               # Filter by prefix
```

---

### Configuration Commands

| Command | Description |
|---------|-------------|
| `set disasm on\|off` | Toggle auto-disassembly |
| `set context <count>` | Set disassembly context lines |
| `set period <ticks>` | Set clock period |
| `set var <comp> <var> <val>` | Set component variable |

#### Examples
```
(gdb-dragonfly) set disasm off              # Disable auto-disassembly
(gdb-dragonfly) set context 10              # Show 10 context lines
(gdb-dragonfly) set period 800              # Set clock period
(gdb-dragonfly) set var I:PAD2 RESET 1      # Set RESET high
(gdb-dragonfly) set var I:PAD2 WAIT 0       # Set WAIT low
```

---

### Other Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `quit` | `q` | Exit debugger |
| `help [command]` | - | Show help |

---

## Available Registers

| Register | Description |
|----------|-------------|
| `pc` | Program Counter (16-bit) |
| `sp` | Stack Pointer (16-bit) |
| `ac` | Accumulator (same as `xl`) |
| `x`, `xh`, `xl` | X register pair and bytes (XL = Accumulator) |
| `y`, `yh`, `yl` | Y register pair and bytes |
| `z`, `zh`, `zl` | Z register pair and bytes |
| `flags`, `fr` | Flags register |

> **Note:** The Accumulator (AC) is the same physical register as XL.
> In the register display, it appears as `X = 0x00XX  XH=0x00 AC=0xXX`.

---

## Component Naming Convention

Components use the format `MODULE:COMPONENT`:

| Module | Description |
|--------|-------------|
| `ALU` | ALU hub |
| `C1` | Core 1 (instruction decoder) |
| `C2` | Core 2 |
| `C3` | Core 3 (microcode) |
| `I` | Interface (external connections) |
| `PC` | Program counter |
| `REG` | Register file |
| `SP` | Stack pointer |

---

## Tips

1. **Empty line** repeats the last command (like GDB)
2. **Tab completion** works for commands
3. Use `help <command>` for detailed help on any command
4. Network names usually end with `!` - it's added automatically if missing
5. Use `info components` to discover available component names
6. Use `pins <component>` to see available pin aliases
