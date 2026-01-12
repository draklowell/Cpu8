import json
from enum import IntEnum

from compiler import Compiler, Component, Context, code, components

compiler = Compiler()

## COMMON ROUTINES ##


# 1 tick
def Move(to: Component, from_: Component):
    yield code(
        bus_reader=to,
        bus_writer=from_,
    )


# 2 ticks
def MoveWord(to: tuple[Component, Component], from_: tuple[Component, Component]):
    yield from Move(to[0], from_[0])
    yield from Move(to[1], from_[1])


# 3 ticks
def Read(to: Component):
    yield from MoveWord(components.ADDRESS, components.PROGRAM_COUNTER)
    yield code(
        bus_reader=to,
        bus_writer=components.MEMORY,
        program_counter_increment=1,
        address_increment=1,
    )


# 4 ticks
def ReadWord(to: tuple[Component, Component]):
    yield from Read(to[0])
    yield code(
        bus_reader=to[1],
        bus_writer=components.MEMORY,
        program_counter_increment=1,
    )


# 3 ticks
def NextOperation(ctx: Context, ignore_interrupts: bool = False):
    if (not ctx.interrupt) or ignore_interrupts:
        yield code(
            bus_reader=components.ADDRESS_HIGH,
            bus_writer=components.PROGRAM_COUNTER_HIGH,
        )
    else:
        yield code(
            bus_reader=components.INSTRUCTION,
            bus_writer=components.INTERRUPT_HANDLE_CONSTANT,
            step_counter_clear=1,
        )

    yield code(
        bus_reader=components.ADDRESS_LOW,
        bus_writer=components.PROGRAM_COUNTER_LOW,
    )
    yield code(
        bus_reader=components.INSTRUCTION,
        bus_writer=components.MEMORY,
        program_counter_increment=1,
        step_counter_clear=1,
    )


# 3 ticks
def Push(from_: Component):
    yield from MoveWord(components.ADDRESS, components.STACK_POINTER)
    yield code(
        bus_reader=components.MEMORY,
        bus_writer=from_,
        stack_pointer_decrement=1,
        address_decrement=1,
    )


# 4 ticks
def PushWord(from_: tuple[Component, Component]):
    yield from Push(from_[1])
    yield code(
        bus_reader=components.MEMORY,
        bus_writer=from_[0],
        stack_pointer_decrement=1,
    )


# 4 ticks
def Pop(to: Component):
    yield code(
        stack_pointer_increment=1,
    )
    yield from MoveWord(components.ADDRESS, components.STACK_POINTER)
    yield code(
        bus_reader=to,
        bus_writer=components.MEMORY,
        stack_pointer_increment=1,
        address_increment=1,
    )


# 5 ticks
def PopWord(to: tuple[Component, Component]):
    yield from Pop(to[0])
    yield code(
        bus_reader=to[1],
        bus_writer=components.MEMORY,
    )


# 1 tick
class CarryMode(IntEnum):
    ALWAYS_ZERO = 0
    ALWAYS_ONE = 1
    TRANSPARENT = 2  # sampe as carry flag
    INVERTED = 3  # inverted carry flag


def ApplyALU(
    ctx: Context, to: Component, carry_mode: CarryMode, selection: int, mode: int
):
    if carry_mode == CarryMode.TRANSPARENT:
        carry = ctx.carry
    elif carry_mode == CarryMode.INVERTED:
        carry = 1 - ctx.carry
    else:
        carry = carry_mode.value

    yield code(
        bus_reader=to,
        bus_writer=components.ALU,
        alu_selection=selection,
        alu_mode=mode,
        alu_carry=carry,
        flags_from_alu=1,
    )


# conditions
def NotZero(ctx: Context) -> bool:
    return not bool(ctx.zero)


def Zero(ctx: Context) -> bool:
    return bool(ctx.zero)


def NoCarry(ctx: Context) -> bool:
    return not bool(ctx.carry)


def Carry(ctx: Context) -> bool:
    return bool(ctx.carry)


def Plus(ctx: Context) -> bool:
    return not bool(ctx.sign)


def Minus(ctx: Context) -> bool:
    return bool(ctx.sign)


## GROUPS ##

# 7
CONDITIONS = [
    (NotZero, "nz"),
    (Zero, "z"),
    (NoCarry, "nc"),
    (Carry, "c"),
    (Plus, "p"),
    (Minus, "m"),
    (lambda _: True, ""),
]

# 6
REGISTERS_BYTE_ARITHMETICS = [
    (components.ACCUMULATOR, "ac"),
    (components.XH, "xh"),
    (components.YL, "yl"),
    (components.YH, "yh"),
    (components.ZL, "zl"),
    (components.ZH, "zh"),
]

# 5
REGISTERS_BYTE_NOZ = [
    (components.ACCUMULATOR, "ac"),
    (components.XH, "xh"),
    (components.YL, "yl"),
    (components.YH, "yh"),
    (components.FLAGS, "fr"),
]

# 7
REGISTERS_BYTE = REGISTERS_BYTE_NOZ + [
    (components.ZL, "zl"),
    (components.ZH, "zh"),
]

# 3
REGISTERS_WORD = [
    (components.X, "x"),
    (components.Y, "y"),
    (components.Z, "z"),
]

# 4
REGISTERS_WORD_SP = REGISTERS_WORD + [
    (components.STACK_POINTER, "sp"),
]

# 4
REGISTERS_WORD_PC = REGISTERS_WORD + [
    (components.PROGRAM_COUNTER, "pc"),
]

## INSTRUCTIONS ##


# nop (1)
@compiler.instruction("nop", 0x00)
def nop(ctx: Context):
    yield from NextOperation(ctx)


# inth/inte/intd (3)
@compiler.instruction("inth", 0x1C)
def inth(ctx: Context):
    yield from PushWord(components.PROGRAM_COUNTER)
    yield from Move(components.ADDRESS_LOW, components.INTERRUPT_CODE)
    yield from Move(components.ADDRESS_HIGH, components.INTERRUPT_HANDLE_CONSTANT)
    yield from Move(components.PROGRAM_COUNTER_HIGH, components.MEMORY)
    yield from Move(components.PROGRAM_COUNTER_LOW, components.MEMORY)
    yield from NextOperation(ctx, ignore_interrupts=True)


@compiler.instruction("inte")
def inte(ctx: Context):
    yield code(
        interrupt_enable=1,
    )
    yield from NextOperation(ctx)


@compiler.instruction("intd")
def intd(ctx: Context):
    yield code(
        interrupt_disable=1,
    )
    yield from NextOperation(ctx)


# ldi/ld (18)
for register, name in REGISTERS_BYTE:

    @compiler.instruction(f"ldi-{name}-[byte]")
    def ldi(ctx: Context):
        yield from Read(register)
        yield from NextOperation(ctx)

    @compiler.instruction(f"ld-{name}-[word]")
    def ld(ctx: Context):
        yield from ReadWord(components.ARGUMENT)
        yield from MoveWord(components.ADDRESS, components.ARGUMENT)
        yield code(bus_reader=register, bus_writer=components.MEMORY)
        yield from NextOperation(ctx)


for register, name in REGISTERS_WORD_SP:

    @compiler.instruction(f"ldi-{name}-[word]")
    def ldi(ctx: Context):
        yield from ReadWord(register)
        yield from NextOperation(ctx)


# ldx (5)
for register, name in REGISTERS_BYTE_NOZ:

    @compiler.instruction(f"ldx-{name}")
    def ldx(ctx: Context):
        yield from MoveWord(components.ADDRESS, components.Z)
        yield code(
            bus_reader=register,
            bus_writer=components.MEMORY,
        )
        yield from NextOperation(ctx)


# st (7)
for register, name in REGISTERS_BYTE:

    @compiler.instruction(f"st-[word]-{name}")
    def st(ctx: Context):
        yield from ReadWord(components.ARGUMENT)
        yield from MoveWord(components.ADDRESS, components.ARGUMENT)
        yield code(
            bus_reader=components.MEMORY,
            bus_writer=register,
        )
        yield from NextOperation(ctx)


# stx (5)
for register, name in REGISTERS_BYTE_NOZ:

    @compiler.instruction(f"stx-{name}")
    def stx(ctx: Context):
        yield from MoveWord(components.ADDRESS, components.Z)
        yield code(
            bus_reader=components.MEMORY,
            bus_writer=register,
        )
        yield from NextOperation(ctx)


# mov (45)
for from_, from_name in REGISTERS_BYTE:
    for to, to_name in REGISTERS_BYTE:
        if from_ == to:
            continue

        @compiler.instruction(f"mov-{to_name}-{from_name}")
        def mov(ctx: Context):
            yield from Move(to, from_)
            yield from NextOperation(ctx)


@compiler.instruction(f"mov-sp-z")
def mov(ctx: Context):
    yield from MoveWord(components.STACK_POINTER, components.Z)
    yield from NextOperation(ctx)


@compiler.instruction(f"mov-z-sp")
def mov(ctx: Context):
    yield from MoveWord(components.Z, components.STACK_POINTER)
    yield from NextOperation(ctx)


@compiler.instruction(f"mov-z-pc")
def mov(ctx: Context):
    yield from MoveWord(components.Z, components.PROGRAM_COUNTER)
    yield from NextOperation(ctx)


# push (11)
for register, name in REGISTERS_BYTE:

    @compiler.instruction(f"push-{name}")
    def push(ctx: Context):
        yield from Push(register)
        yield from NextOperation(ctx)


for register, name in REGISTERS_WORD_PC:

    @compiler.instruction(f"push-{name}")
    def push(ctx: Context):
        yield from PushWord(register)
        yield from NextOperation(ctx)


# pop (11)
for register, name in REGISTERS_BYTE:

    @compiler.instruction(f"pop-{name}")
    def pop(ctx: Context):
        yield from Pop(register)
        yield from NextOperation(ctx)


for register, name in REGISTERS_WORD:

    @compiler.instruction(f"pop-{name}")
    def pop(ctx: Context):
        yield from PopWord(register)
        yield from NextOperation(ctx)


# jmp (14)
for condition, name in CONDITIONS:
    name = name or "mp"

    @compiler.instruction(f"j{name}-[word]")
    def jmp(ctx: Context):
        if not condition(ctx):
            yield from NextOperation(ctx)
            return

        yield from ReadWord(components.ARGUMENT)
        yield from MoveWord(components.PROGRAM_COUNTER, components.ARGUMENT)
        yield from NextOperation(ctx)

    @compiler.instruction(f"j{name}x")
    def jmpx(ctx: Context):
        if not condition(ctx):
            yield from NextOperation(ctx)
            return

        yield from MoveWord(components.PROGRAM_COUNTER, components.Z)
        yield from NextOperation(ctx)


# call (7)
for condition, name in CONDITIONS:
    name = name or "all"

    @compiler.instruction(f"c{name}-[word]")
    def call(ctx: Context):
        if not condition(ctx):
            yield from NextOperation(ctx)
            return

        yield from ReadWord(components.ARGUMENT)
        yield from PushWord(components.PROGRAM_COUNTER)
        yield from MoveWord(components.PROGRAM_COUNTER, components.ARGUMENT)
        yield from NextOperation(ctx)


# ret (7)
for condition, name in CONDITIONS:
    name = name or "et"

    @compiler.instruction(f"r{name}")
    def ret(ctx: Context):
        if not condition(ctx):
            yield from NextOperation(ctx)
            return

        yield from PopWord(components.PROGRAM_COUNTER)
        yield from NextOperation(ctx)


# alu operations (95)
for operation, selection, mode, carry_mode, to_mode, is_binary in [
    # to_mode = 0 - nowhere
    # to_mode = 1 - accumulator
    # to_mode = 2 - same register
    ("add", 0x9, 0, CarryMode.ALWAYS_ZERO, 1, True),
    ("sub", 0x6, 0, CarryMode.ALWAYS_ONE, 1, True),
    ("nand", 0x4, 1, CarryMode.ALWAYS_ZERO, 1, True),
    ("xor", 0x6, 1, CarryMode.ALWAYS_ZERO, 1, True),
    ("nor", 0x1, 1, CarryMode.ALWAYS_ZERO, 1, True),
    ("adc", 0x9, 0, CarryMode.TRANSPARENT, 1, True),
    ("sbb", 0x6, 0, CarryMode.INVERTED, 1, True),
    ("inc", 0x0, 0, CarryMode.ALWAYS_ONE, 2, False),
    ("dec", 0xF, 0, CarryMode.ALWAYS_ZERO, 2, False),
    ("icc", 0x0, 0, CarryMode.TRANSPARENT, 2, False),
    ("dcb", 0xF, 0, CarryMode.INVERTED, 2, False),
    ("not", 0x0, 1, CarryMode.ALWAYS_ZERO, 2, False),
    ("cmp", 0x6, 0, CarryMode.ALWAYS_ZERO, 0, True),
]:
    for register, name in REGISTERS_BYTE_ARITHMETICS:
        if to_mode == 0:
            to = components.DISABLE
        elif to_mode == 1:
            to = components.ACCUMULATOR
        elif to_mode == 2:
            to = register
        else:
            continue

        @compiler.instruction(f"{operation}-{name}")
        def op(ctx: Context):
            if is_binary:
                yield from Move(components.ARGUMENT_LOW, register)
                yield from Move(components.ARGUMENT_HIGH, components.ACCUMULATOR)
            else:
                yield from Move(components.ARGUMENT_HIGH, register)

            yield from ApplyALU(
                ctx,
                to,
                carry_mode,
                selection,
                mode,
            )
            yield from NextOperation(ctx)

    if not is_binary:
        continue

    if to_mode == 0:
        to = components.DISABLE
    elif to_mode == 1:
        to = components.ACCUMULATOR
    else:
        continue

    @compiler.instruction(f"{operation}i-[byte]")
    def opi(ctx: Context):
        yield from Read(components.ARGUMENT_LOW)
        yield from Move(components.ARGUMENT_HIGH, components.ACCUMULATOR)
        yield from ApplyALU(
            ctx,
            to,
            carry_mode,
            selection,
            mode,
        )
        yield from NextOperation(ctx)


# shl/shr (2)
@compiler.instruction("shl")
def shl(ctx: Context):
    yield code(
        bus_reader=components.ACCUMULATOR,
        bus_writer=components.ACCUMULATOR,
        accumulator_shift_left=1,
    )
    yield from NextOperation(ctx)


@compiler.instruction("shr")
def shr(ctx: Context):
    yield code(
        bus_reader=components.ACCUMULATOR,
        bus_writer=components.ACCUMULATOR,
        accumulator_shift_right=1,
    )
    yield from NextOperation(ctx)


# hlt (1)
@compiler.instruction("hlt")
def hlt(ctx: Context):
    yield code(
        halt=1,
    )


compiler.save("bin/")

data = {
    "readers": {},
    "writers": {},
}

for component in components.ALL_COMPONENTS:
    if component.reader is not None:
        if component.name in data["readers"]:
            raise ValueError(f"Duplicate reader code {component.reader}")

        data["readers"][component.reader] = component.name

    if component.writer is not None:
        if component.name in data["writers"]:
            raise ValueError(f"Duplicate writer code {component.writer}")

        data["writers"][component.writer] = component.name

with open(f"bin/components.json", "w") as file:
    json.dump(data, file, indent=4)
