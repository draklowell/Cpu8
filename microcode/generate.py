from compiler import Compiler, Flags, code

compiler = Compiler()


def NextOperation(flags: Flags):
    yield code(
        program_counter_to_abus=1,
        instruction_from_dbus=1,
        memory_read=1,
        program_counter_increment=1,
        step_counter_clear=1,
    )


def MemoryToTemp16(flags: Flags):
    yield code(
        program_counter_to_abus=1,
        temporary_high_from_dbus=1,
        memory_read=1,
        program_counter_increment=1,
    )
    yield code(
        program_counter_to_abus=1,
        temporary_low_from_dbus=1,
        memory_read=1,
        program_counter_increment=1,
    )


def PushProgramCounter(flags: Flags):
    yield code(
        program_counter_low_to_dbus=1,
        stack_pointer_to_abus=1,
        stack_pointer_decrement=1,
        memory_write=1,
    )
    yield code(
        program_counter_high_to_dbus=1,
        stack_pointer_to_abus=1,
        stack_pointer_decrement=1,
        memory_write=1,
    )


def PopProgramCounter(flags: Flags):
    yield code(
        program_counter_high_from_dbus=1,
        stack_pointer_to_abus=1,
        stack_pointer_increment=1,
        memory_read=1,
    )
    yield code(
        program_counter_low_from_dbus=1,
        stack_pointer_to_abus=1,
        stack_pointer_increment=1,
        memory_read=1,
    )


def RegisterPairToTemp16(flags: Flags, base: int):
    yield code(
        file_read_index=base,
        temporary_high_from_dbus=1,
    )
    yield code(
        file_read_index=base + 1,
        temporary_low_from_dbus=1,
    )


# nop
@compiler.instruction("nop")
def Nop(flags: Flags):
    yield from NextOperation(flags)


# ldi (8)
for register in range(6):

    @compiler.instruction(f"ldi-r{register}-[data]")
    def ldi(flags: Flags):
        yield code(
            program_counter_to_abus=1,
            file_write_index=register,
            memory_read=1,
            program_counter_increment=1,
        )
        yield from NextOperation(flags)


@compiler.instruction(f"ldi-a")
def ldi(flags: Flags):
    yield code(
        program_counter_to_abus=1,
        accumulator_from_dbus=1,
        memory_read=1,
        program_counter_increment=1,
    )
    yield from NextOperation(flags)


@compiler.instruction(f"ldi-sp-[addr]")
def ldi(flags: Flags):
    yield code(
        program_counter_to_abus=1,
        stack_pointer_high_from_dbus=1,
        memory_read=1,
        program_counter_increment=1,
    )
    yield code(
        program_counter_to_abus=1,
        stack_pointer_low_from_dbus=1,
        memory_read=1,
        program_counter_increment=1,
    )
    yield from NextOperation(flags)


# ld (8)
for register in range(6):

    @compiler.instruction(f"ld-r{register}-[data]")
    def ld(flags: Flags):
        yield from MemoryToTemp16(flags)
        yield code(
            temporary_to_abus=1,
            file_write_index=register,
            memory_read=1,
        )
        yield from NextOperation(flags)


@compiler.instruction(f"ld-a-[data]")
def ld(flags: Flags):
    yield from MemoryToTemp16(flags)
    yield code(
        temporary_to_abus=1,
        accumulator_from_dbus=1,
        memory_read=1,
    )
    yield from NextOperation(flags)


@compiler.instruction(f"ld-f-[data]")
def ld(flags: Flags):
    yield from MemoryToTemp16(flags)
    yield code(
        temporary_to_abus=1,
        flags_from_dbus=1,
        memory_read=1,
    )
    yield from NextOperation(flags)


# ldx (18)
for base in range(0, 6, 2):
    for register in range(6):
        if base == register or base + 1 == register:
            continue

        @compiler.instruction(f"ldx-r{register}-r{base}{base+1}")
        def ldx(flags: Flags):
            yield from RegisterPairToTemp16(flags, base)
            yield code(
                temporary_to_abus=1,
                file_write_index=register,
                memory_read=1,
            )
            yield from NextOperation(flags)

    @compiler.instruction(f"ldx-a-r{base}{base+1}")
    def ldx(flags: Flags):
        yield from RegisterPairToTemp16(flags, base)
        yield code(
            temporary_to_abus=1,
            accumulator_from_dbus=1,
            memory_read=1,
        )
        yield from NextOperation(flags)

    @compiler.instruction(f"ldx-f-r{base}{base+1}")
    def ldx(flags: Flags):
        yield from RegisterPairToTemp16(flags, base)
        yield code(
            temporary_to_abus=1,
            flags_from_dbus=1,
            memory_read=1,
        )
        yield from NextOperation(flags)


# st (8)
for register in range(6):

    @compiler.instruction(f"st-[addr]-r{register}")
    def st(flags: Flags):
        yield from MemoryToTemp16(flags)
        yield code(
            temporary_to_abus=1,
            file_read_index=register,
            memory_write=1,
        )
        yield from NextOperation(flags)


@compiler.instruction(f"st-[addr]-a")
def st(flags: Flags):
    yield from MemoryToTemp16(flags)
    yield code(
        temporary_to_abus=1,
        accumulator_to_dbus=1,
        memory_write=1,
    )
    yield from NextOperation(flags)


@compiler.instruction(f"st-[addr]-f")
def st(flags: Flags):
    yield from MemoryToTemp16(flags)
    yield code(
        temporary_to_abus=1,
        flags_to_dbus=1,
        memory_write=1,
    )
    yield from NextOperation(flags)


# stx (18)
for base in range(0, 6, 2):
    for register in range(6):
        if base == register or base + 1 == register:
            continue

        @compiler.instruction(f"stx-r{base}{base+1}-r{register}")
        def stx(flags: Flags):
            yield from RegisterPairToTemp16(flags, base)
            yield code(
                temporary_to_abus=1,
                file_read_index=register,
                memory_write=1,
            )
            yield from NextOperation(flags)

    @compiler.instruction(f"stx-r{base}{base+1}-a")
    def stx(flags: Flags):
        yield from RegisterPairToTemp16(flags, base)
        yield code(
            temporary_to_abus=1,
            accumulator_to_dbus=1,
            memory_write=1,
        )
        yield from NextOperation(flags)

    @compiler.instruction(f"stx-r{base}{base+1}-f")
    def stx(flags: Flags):
        yield from RegisterPairToTemp16(flags, base)
        yield code(
            temporary_to_abus=1,
            flags_to_dbus=1,
            memory_write=1,
        )
        yield from NextOperation(flags)


# mov (72)
for register_a in range(6):
    for register_b in range(6):
        if register_a == register_b:
            continue

        @compiler.instruction(f"mov-r{register_b}-r{register_a}")
        def mov(flags: Flags):
            yield code(
                file_read_index=register_a,
                file_write_index=register_b,
            )
            yield from NextOperation(flags)

    @compiler.instruction(f"mov-a-r{register_a}")
    def mov(flags: Flags):
        yield code(
            file_read_index=register_a,
            accumulator_from_dbus=1,
        )
        yield from NextOperation(flags)

    @compiler.instruction(f"mov-r{register_a}-a")
    def mov(flags: Flags):
        yield code(
            file_write_index=register_a,
            accumulator_to_dbus=1,
        )
        yield from NextOperation(flags)

    @compiler.instruction(f"mov-f-r{register_a}")
    def mov(flags: Flags):
        yield code(
            file_read_index=register_a,
            flags_from_dbus=1,
        )
        yield from NextOperation(flags)

    @compiler.instruction(f"mov-r{register_a}-f")
    def mov(flags: Flags):
        yield code(
            file_write_index=register_a,
            flags_to_dbus=1,
        )
        yield from NextOperation(flags)


for base in range(0, 6, 2):

    @compiler.instruction(f"mov-sp-r{base}{base+1}")
    def mov(flags: Flags):
        yield code(
            file_read_index=base,
            stack_pointer_high_from_dbus=1,
        )
        yield code(
            file_read_index=base + 1,
            stack_pointer_low_from_dbus=1,
        )
        yield from NextOperation(flags)

    @compiler.instruction(f"mov-r{base}{base+1}-sp")
    def mov(flags: Flags):
        yield code(
            file_write_index=base,
            stack_pointer_high_to_dbus=1,
        )
        yield code(
            file_write_index=base + 1,
            stack_pointer_low_to_dbus=1,
        )
        yield from NextOperation(flags)

    @compiler.instruction(f"mov-r{base}{base+1}-pc")
    def mov(flags: Flags):
        yield code(
            file_write_index=base,
            program_counter_high_to_dbus=1,
        )
        yield code(
            file_write_index=base + 1,
            program_counter_low_to_dbus=1,
        )
        yield from NextOperation(flags)


# push (12)
for register in range(6):

    @compiler.instruction(f"push-r{register}")
    def push(flags: Flags):
        yield code(
            file_read_index=register,
            stack_pointer_to_abus=1,
            stack_pointer_decrement=1,
            memory_write=1,
        )
        yield from NextOperation(flags)


@compiler.instruction(f"push-a")
def push(flags: Flags):
    yield code(
        accumulator_to_dbus=1,
        stack_pointer_to_abus=1,
        stack_pointer_decrement=1,
        memory_write=1,
    )
    yield from NextOperation(flags)


@compiler.instruction(f"push-pc")
def push(flags: Flags):
    yield from PushProgramCounter(flags)
    yield from NextOperation(flags)


@compiler.instruction(f"push-f")
def push(flags: Flags):
    yield code(
        flags_to_dbus=1,
        stack_pointer_to_abus=1,
        stack_pointer_decrement=1,
        memory_write=1,
    )
    yield from NextOperation(flags)


for base in range(0, 6, 2):

    @compiler.instruction(f"push-r{base}{base+1}")
    def push(flags: Flags):
        yield code(
            file_read_index=base + 1,
            stack_pointer_to_abus=1,
            stack_pointer_decrement=1,
            memory_write=1,
        )
        yield code(
            file_read_index=base,
            stack_pointer_to_abus=1,
            stack_pointer_decrement=1,
            memory_write=1,
        )
        yield from NextOperation(flags)


# pop (11)
for register in range(6):

    @compiler.instruction(f"pop-r{register}")
    def pop(flags: Flags):
        yield code(
            file_write_index=register,
            stack_pointer_to_abus=1,
            stack_pointer_increment=1,
            memory_read=1,
        )
        yield from NextOperation(flags)


@compiler.instruction(f"pop-a")
def pop(flags: Flags):
    yield code(
        accumulator_from_dbus=1,
        stack_pointer_to_abus=1,
        stack_pointer_increment=1,
        memory_read=1,
    )
    yield from NextOperation(flags)


@compiler.instruction(f"pop-f")
def pop(flags: Flags):
    yield code(
        flags_from_dbus=1,
        stack_pointer_to_abus=1,
        stack_pointer_increment=1,
        memory_read=1,
    )
    yield from NextOperation(flags)


for base in range(0, 6, 2):

    @compiler.instruction(f"pop-r{base}{base+1}")
    def push(flags: Flags):
        yield code(
            file_write_index=base,
            stack_pointer_to_abus=1,
            stack_pointer_increment=1,
            memory_read=1,
        )
        yield code(
            file_write_index=base + 1,
            stack_pointer_to_abus=1,
            stack_pointer_increment=1,
            memory_read=1,
        )
        yield from NextOperation(flags)


# conditions
def NotZero(flags: Flags) -> bool:
    return not bool(flags.zero)


def Zero(flags: Flags) -> bool:
    return bool(flags.zero)


def NoCarry(flags: Flags) -> bool:
    return not bool(flags.carry)


def Carry(flags: Flags) -> bool:
    return bool(flags.carry)


def Plus(flags: Flags) -> bool:
    return not bool(flags.sign)


def Minus(flags: Flags) -> bool:
    return bool(flags.sign)


conditions = {
    "nz": NotZero,
    "z": Zero,
    "nc": NoCarry,
    "c": Carry,
    "p": Plus,
    "m": Minus,
    "": lambda _: True,
}

# jmp (28)
for name, condition in conditions.items():
    name = name or "mp"

    @compiler.instruction(f"j{name}-[addr]")
    def jmp(flags: Flags):
        if not condition(flags):
            yield from NextOperation(flags)

        yield code(
            program_counter_to_abus=1,
            temporary_low_from_dbus=1,
            memory_read=1,
            program_counter_increment=1,
        )
        yield code(
            program_counter_to_abus=1,
            program_counter_low_from_dbus=1,
            memory_read=1,
        )
        yield code(
            program_counter_high_from_dbus=1,
            temporary_low_to_dbus=1,
        )
        yield from NextOperation(flags)

    for base in range(0, 6, 2):

        @compiler.instruction(f"j{name}x-r{base}{base+1}")
        def jmp(flags: Flags):
            if not condition(flags):
                yield from NextOperation(flags)

            yield code(
                program_counter_high_from_dbus=1,
                file_read_index=base,
            )
            yield code(
                program_counter_low_from_dbus=1,
                file_read_index=base + 1,
            )
            yield from NextOperation(flags)


# call (7)
for name, condition in conditions.items():
    name = name or "all"

    @compiler.instruction(f"c{name}-[addr]")
    def call(flags: Flags):
        if not condition(flags):
            yield from NextOperation(flags)

        yield from PushProgramCounter(flags)
        yield code(
            program_counter_to_abus=1,
            temporary_low_from_dbus=1,
            memory_read=1,
            program_counter_increment=1,
        )
        yield code(
            program_counter_to_abus=1,
            program_counter_low_from_dbus=1,
            memory_read=1,
        )
        yield code(
            program_counter_high_from_dbus=1,
            temporary_low_to_dbus=1,
        )
        yield from NextOperation(flags)


# ret (7)
for name, condition in conditions.items():
    name = name or "et"

    @compiler.instruction(f"r{name}")
    def ret(flags: Flags):
        if not condition(flags):
            yield from NextOperation(flags)

        yield from PopProgramCounter(flags)
        yield from NextOperation(flags)


# swap (3)
for base in range(0, 6, 2):

    @compiler.instruction(f"swap-r{base}{base+1}")
    def swap(flags: Flags):
        yield code(
            file_read_index=base,
            temporary_low_from_dbus=1,
        )
        yield code(
            file_read_index=base + 1,
            file_write_index=base,
        )
        yield code(
            file_write_index=base + 1,
            temporary_low_to_dbus=1,
        )


# add/sub/nand/xor/nor (40)
for name, opcode, mode in [
    ("add", 0x9, 0),
    ("sub", 0x6, 0),
    ("nand", 0x4, 1),
    ("xor", 0x6, 1),
    ("nor", 0x1, 1),
    ("adc", 0x9, 0),
    ("sbb", 0xF, 0),
]:
    for register in range(6):

        @compiler.instruction(f"{name}-r{register}")
        def operation(flags: Flags):
            yield code(
                file_read_index=register,
                temporary_high_from_dbus=1,
            )
            yield code(
                alu_opcode=opcode,
                alu_mode=mode,
                alu_carry=0,
                alu_enable=1,
                accumulator_from_dbus=1,
                flags_from_alu=1,
            )
            yield from NextOperation(flags)

    @compiler.instruction(f"{name}-a")
    def operation(flags: Flags):
        yield code(
            accumulator_to_dbus=1,
            temporary_high_from_dbus=1,
        )
        yield code(
            alu_opcode=opcode,
            alu_mode=mode,
            alu_carry=0,
            alu_enable=1,
            accumulator_from_dbus=1,
            flags_from_alu=1,
        )
        yield from NextOperation(flags)

    @compiler.instruction(f"{name}i-[data]")
    def operation(flags: Flags):
        yield code(
            program_counter_to_abus=1,
            temporary_high_from_dbus=1,
            memory_read=1,
            program_counter_increment=1,
        )
        yield code(
            alu_opcode=opcode,
            alu_mode=mode,
            alu_carry=0,
            alu_enable=1,
            accumulator_from_dbus=1,
            flags_from_alu=1,
        )
        yield from NextOperation(flags)


# ion/ioff/iproc - reserved for interrupts
@compiler.instruction("ion")
def ion(flags: Flags):
    yield from NextOperation(flags)


@compiler.instruction("ioff")
def ioff(flags: Flags):
    yield from NextOperation(flags)


for ino in range(4):

    @compiler.instruction(f"irq-{ino}")
    def irq(flags: Flags):
        yield from NextOperation(flags)


# hlt
@compiler.instruction("hlt")
def hlt(flags: Flags):
    yield code(
        halt=1,
    )


compiler.save("bin/")
