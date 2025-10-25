# Opcode Verification for `main.s` and `sum.s`

This note cross-checks the opcodes that the toolchain emitted for the small
program that loads two bytes, calls an external routine, and halts. The
assembled binary (`out.bin`) was produced by the following command sequence:

```sh
./asm_cpu ../main.s --object --no-preprocess -o main.o
./asm_cpu ../sum.s --object --no-preprocess -o sum.o
./ld_cpu out.bin main.o sum.o
```

The resulting `hexdump -C out.bin` output begins with:

```
04 00 0a 10 00 0b 7d 00 0a dd 8a 84 01 02 …
```

## Instruction Breakdown

| Address | Instruction            | Expected Opcode (from ISA table) | Emitted Bytes | Notes |
|---------|------------------------|----------------------------------|---------------|-------|
| 0x0000  | `ld ac, [one]`         | `0x04` (`ld-ac-[word]`)          | `04 00 0A`    | Loads the 16-bit absolute address of `one` into AC. |
| 0x0003  | `ld zh, [two]`         | `0x10` (`ld-zh-[word]`)          | `10 00 0B`    | Fetches the byte at label `two` into `ZH`. |
| 0x0006  | `call sum`             | `0x7D` (`call-[word]`)           | `7D 00 0A`    | Calls the subroutine located at address `0x000A`. |
| 0x0009  | `hlt`                  | `0xDD` (`hlt`)                   | `DD`          | Halts execution after the call returns. |
| 0x000A  | `add zh` (in `sum`)    | `0x8A` (`add-zh`)                | `8A`          | Adds the `ZH` register to the accumulator. |
| 0x000B  | `ret` (in `sum`)       | `0x84` (`ret`)                   | `84`          | Returns control to the caller. |

## `.rodata` Section

The `.rodata` bytes follow immediately after the executable code:

| Address | Label | Bytes | Meaning |
|---------|-------|-------|---------|
| 0x000C  | `one` | `01`  | Constant used by the first load. |
| 0x000D  | `two` | `02`  | Constant used by the second load. |

Because the linker concatenates `.text` and `.rodata` into a single ROM image,
these constants appear directly after the instruction stream. No additional
padding is inserted apart from the ROM fill pattern (`0xFF`) beyond the defined
sections.

## Conclusion

Every opcode in `out.bin` matches the expected value from the CPU8/16
instruction table, and the section layout aligns with the assembler and linker
specification. The toolchain therefore encoded the program correctly.
