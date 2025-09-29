from compiler import Compiler, Context, FromDBus, ToABus, ToDBus, code

compiler = Compiler()


def NextOperation(ctx: Context):
    if not ctx.interrupt:
        yield code(
            to_a_bus=ToABus.PROGRAM_COUNTER,
            to_d_bus=ToDBus.MEMORY,
            from_d_bus=FromDBus.INSTRUCTION_REGISTER,
            program_counter_increment=1,
            step_counter_clear=1,
        )
    else:
        yield code(
            to_d_bus=ToDBus.INTERRUPT_HANDLE_CONSTANT,
            from_d_bus=FromDBus.INSTRUCTION_REGISTER,
            step_counter_clear=1,
        )


def ReadWord(ctx: Context):
    yield code(
        from_d_bus=FromDBus.TEMPORARY_HIGH,
        to_d_bus=ToDBus.MEMORY,
        to_a_bus=ToABus.PROGRAM_COUNTER,
        program_counter_increment=1,
    )
    yield code(
        from_d_bus=FromDBus.TEMPORARY_LOW,
        to_d_bus=ToDBus.MEMORY,
        to_a_bus=ToABus.PROGRAM_COUNTER,
        program_counter_increment=1,
    )


def PushProgramCounter(ctx: Context):
    yield code(
        from_d_bus=FromDBus.MEMORY,
        to_d_bus=ToDBus.PROGRAM_COUNTER_LOW,
        to_a_bus=ToABus.STACK_POINTER,
        stack_pointer_decrement=1,
    )
    yield code(
        from_d_bus=FromDBus.MEMORY,
        to_d_bus=ToDBus.PROGRAM_COUNTER_HIGH,
        to_a_bus=ToABus.STACK_POINTER,
        stack_pointer_decrement=1,
    )


# nop (1)
@compiler.instruction("nop", 0x00)
def nop(ctx: Context):
    yield from NextOperation(ctx)


# inth/inte/intd (3)
@compiler.instruction("inth", 0x1C)
def inth(ctx: Context):
    yield from PushProgramCounter(ctx)
    yield code(
        from_d_bus=FromDBus.PROGRAM_COUNTER_LOW,
        to_d_bus=ToDBus.MEMORY,
        interrupt_acknowledge=1,
    )
    yield code(
        from_d_bus=FromDBus.PROGRAM_COUNTER_HIGH,
        to_d_bus=ToDBus.INTERRUPT_HANDLE_CONSTANT,
    )
    yield from NextOperation(ctx)


@compiler.instruction("inte")
def inte(ctx: Context):
    yield code(
        interrupt_enable=1,
    )
    yield from NextOperation(ctx)  # Can be optimized


@compiler.instruction("intd")
def intd(ctx: Context):
    yield code(
        interrupt_disable=1,
    )
    yield from NextOperation(ctx)  # Can be optimized


# ldi (11)
for register, name in [
    (FromDBus.ACCUMULATOR, "ac"),
    (FromDBus.XH, "xh"),
    (FromDBus.YL, "yl"),
    (FromDBus.YH, "yh"),
    (FromDBus.ZL, "zl"),
    (FromDBus.ZH, "zh"),
    (FromDBus.FLAGS, "fr"),
]:

    @compiler.instruction(f"ldi-{name}-[byte]")
    def ldi(ctx: Context):
        yield code(
            to_a_bus=ToABus.PROGRAM_COUNTER,
            to_d_bus=ToDBus.MEMORY,
            from_d_bus=register,
            program_counter_increment=1,
        )
        yield from NextOperation(ctx)


for register_high, register_low, name in [
    (FromDBus.STACK_POINTER_HIGH, FromDBus.STACK_POINTER_LOW, "sp"),
    (FromDBus.XH, FromDBus.ACCUMULATOR, "x"),
    (FromDBus.YH, FromDBus.YL, "y"),
    (FromDBus.ZH, FromDBus.ZL, "z"),
]:

    @compiler.instruction(f"ldi-{name}-[word]")
    def ldi(ctx: Context):
        yield code(
            to_a_bus=ToABus.PROGRAM_COUNTER,
            to_d_bus=ToDBus.MEMORY,
            from_d_bus=register_high,
            program_counter_increment=1,
        )
        yield code(
            to_a_bus=ToABus.PROGRAM_COUNTER,
            to_d_bus=ToDBus.MEMORY,
            from_d_bus=register_low,
            program_counter_increment=1,
        )
        yield from NextOperation(ctx)


# ld (7)
for register, name in [
    (FromDBus.ACCUMULATOR, "ac"),
    (FromDBus.XH, "xh"),
    (FromDBus.YL, "yl"),
    (FromDBus.YH, "yh"),
    (FromDBus.ZL, "zl"),
    (FromDBus.ZH, "zh"),
    (FromDBus.FLAGS, "fr"),
]:

    @compiler.instruction(f"ld-{name}-[word]")
    def ld(ctx: Context):
        yield from ReadWord(ctx)
        yield code(
            from_d_bus=register,
            to_d_bus=ToDBus.MEMORY,
            to_a_bus=ToABus.TEMPORARY,
        )
        yield from NextOperation(ctx)


# ldx (5)
for register, name in [
    (FromDBus.ACCUMULATOR, "ac"),
    (FromDBus.XH, "xh"),
    (FromDBus.YL, "yl"),
    (FromDBus.YH, "yh"),
    (FromDBus.FLAGS, "fr"),
]:

    @compiler.instruction(f"ldx-{name}")
    def ldx(ctx: Context):
        yield code(
            from_d_bus=FromDBus.TEMPORARY_HIGH,
            to_d_bus=ToDBus.ZH,
        )
        yield code(
            from_d_bus=FromDBus.TEMPORARY_LOW,
            to_d_bus=ToDBus.ZL,
        )
        yield code(
            from_d_bus=register,
            to_d_bus=ToDBus.MEMORY,
            to_a_bus=ToABus.TEMPORARY,
        )
        yield from NextOperation(ctx)


# st (7)
for register, name in [
    (ToDBus.ACCUMULATOR, "ac"),
    (ToDBus.XH, "xh"),
    (ToDBus.YL, "yl"),
    (ToDBus.YH, "yh"),
    (ToDBus.ZL, "zl"),
    (ToDBus.ZH, "zh"),
    (ToDBus.FLAGS, "fr"),
]:

    @compiler.instruction(f"st-[word]-{name}")
    def st(ctx: Context):
        yield from ReadWord(ctx)
        yield code(
            from_d_bus=ToDBus.MEMORY,
            to_d_bus=register,
            to_a_bus=ToABus.TEMPORARY,
        )
        yield from NextOperation(ctx)


# stx (5)
for register, name in [
    (ToDBus.ACCUMULATOR, "ac"),
    (ToDBus.XH, "xh"),
    (ToDBus.YL, "yl"),
    (ToDBus.YH, "yh"),
    (ToDBus.FLAGS, "fr"),
]:

    @compiler.instruction(f"stx-{name}")
    def stx(ctx: Context):
        yield code(
            from_d_bus=FromDBus.TEMPORARY_HIGH,
            to_d_bus=ToDBus.ZH,
        )
        yield code(
            from_d_bus=FromDBus.TEMPORARY_LOW,
            to_d_bus=ToDBus.ZL,
        )
        yield code(
            from_d_bus=FromDBus.MEMORY,
            to_d_bus=register,
            to_a_bus=ToABus.TEMPORARY,
        )
        yield from NextOperation(ctx)


# mov (33)
for from_register, from_name in [
    (ToDBus.ACCUMULATOR, "ac"),
    (ToDBus.XH, "xh"),
    (ToDBus.YL, "yl"),
    (ToDBus.YH, "yh"),
    (ToDBus.ZL, "zl"),
    (ToDBus.ZH, "zh"),
    (ToDBus.FLAGS, "fr"),
]:
    for to_register, to_name in [
        (FromDBus.ACCUMULATOR, "ac"),
        (FromDBus.XH, "xh"),
        (FromDBus.YL, "yl"),
        (FromDBus.YH, "yh"),
        (FromDBus.ZL, "zl"),
        (FromDBus.ZH, "zh"),
        (FromDBus.FLAGS, "fr"),
    ]:
        if from_name == to_name:
            continue

        @compiler.instruction(f"mov-{to_name}-{from_name}")
        def mov(ctx: Context):
            yield code(
                from_d_bus=to_register,
                to_d_bus=from_register,
            )
            yield from NextOperation(ctx)


@compiler.instruction(f"mov-sp-z")
def mov(ctx: Context):
    yield code(
        from_d_bus=FromDBus.STACK_POINTER_HIGH,
        to_d_bus=ToDBus.ZH,
    )
    yield code(
        from_d_bus=FromDBus.STACK_POINTER_LOW,
        to_d_bus=ToDBus.ZL,
    )
    yield from NextOperation(ctx)


@compiler.instruction(f"mov-z-sp")
def mov(ctx: Context):
    yield code(
        from_d_bus=FromDBus.ZH,
        to_d_bus=ToDBus.STACK_POINTER_HIGH,
    )
    yield code(
        from_d_bus=FromDBus.ZL,
        to_d_bus=ToDBus.STACK_POINTER_LOW,
    )
    yield from NextOperation(ctx)


@compiler.instruction(f"mov-z-pc")
def mov(ctx: Context):
    yield code(
        from_d_bus=FromDBus.ZH,
        to_d_bus=ToDBus.PROGRAM_COUNTER_HIGH,
    )
    yield code(
        from_d_bus=FromDBus.ZL,
        to_d_bus=ToDBus.PROGRAM_COUNTER_LOW,
    )
    yield from NextOperation(ctx)


# push (11)
for register, name in [
    (ToDBus.ACCUMULATOR, "ac"),
    (ToDBus.XH, "xh"),
    (ToDBus.YL, "yl"),
    (ToDBus.YH, "yh"),
    (ToDBus.ZL, "zl"),
    (ToDBus.ZH, "zh"),
    (ToDBus.FLAGS, "fr"),
]:

    @compiler.instruction(f"push-{name}")
    def push(ctx: Context):
        yield code(
            from_d_bus=FromDBus.MEMORY,
            to_d_bus=register,
            to_a_bus=ToABus.STACK_POINTER,
            stack_pointer_decrement=1,
        )
        yield from NextOperation(ctx)


for register_high, register_low, name in [
    (ToDBus.PROGRAM_COUNTER_HIGH, ToDBus.PROGRAM_COUNTER_LOW, "pc"),
    (ToDBus.XH, ToDBus.ACCUMULATOR, "x"),
    (ToDBus.YH, ToDBus.YL, "y"),
    (ToDBus.ZH, ToDBus.ZL, "z"),
]:

    @compiler.instruction(f"push-{name}")
    def push(ctx: Context):
        yield code(
            from_d_bus=FromDBus.MEMORY,
            to_d_bus=register_low,
            to_a_bus=ToABus.STACK_POINTER,
            stack_pointer_decrement=1,
        )
        yield code(
            from_d_bus=FromDBus.MEMORY,
            to_d_bus=register_high,
            to_a_bus=ToABus.STACK_POINTER,
            stack_pointer_decrement=1,
        )
        yield from NextOperation(ctx)


# pop (10)
for register, name in [
    (FromDBus.ACCUMULATOR, "ac"),
    (FromDBus.XH, "xh"),
    (FromDBus.YL, "yl"),
    (FromDBus.YH, "yh"),
    (FromDBus.ZL, "zl"),
    (FromDBus.ZH, "zh"),
    (FromDBus.FLAGS, "fr"),
]:

    @compiler.instruction(f"pop-{name}")
    def pop(ctx: Context):
        yield code(
            from_d_bus=register,
            to_d_bus=ToDBus.MEMORY,
            to_a_bus=ToABus.STACK_POINTER,
            stack_pointer_increment=1,
        )
        yield from NextOperation(ctx)


for register_high, register_low, name in [
    (FromDBus.XH, FromDBus.ACCUMULATOR, "x"),
    (FromDBus.YH, FromDBus.YL, "y"),
    (FromDBus.ZH, FromDBus.ZL, "z"),
]:

    @compiler.instruction(f"pop-{name}")
    def pop(ctx: Context):
        yield code(
            from_d_bus=register_high,
            to_d_bus=ToDBus.MEMORY,
            to_a_bus=ToABus.STACK_POINTER,
            stack_pointer_increment=1,
        )
        yield code(
            from_d_bus=register_low,
            to_d_bus=ToDBus.MEMORY,
            to_a_bus=ToABus.STACK_POINTER,
            stack_pointer_increment=1,
        )
        yield from NextOperation(ctx)


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


conditions = {
    "nz": NotZero,
    "z": Zero,
    "nc": NoCarry,
    "c": Carry,
    "p": Plus,
    "m": Minus,
    "": lambda _: True,
}

# jmp (14)
for name, condition in conditions.items():
    name = name or "mp"

    @compiler.instruction(f"j{name}-[word]")
    def jmp(ctx: Context):
        if not condition(ctx):
            yield from NextOperation(ctx)
            return

        yield code(
            from_d_bus=FromDBus.TEMPORARY_LOW,
            to_d_bus=ToDBus.MEMORY,
            to_a_bus=ToABus.PROGRAM_COUNTER,
            program_counter_increment=1,
        )
        yield code(
            from_d_bus=FromDBus.PROGRAM_COUNTER_LOW,
            to_d_bus=ToDBus.MEMORY,
            to_a_bus=ToABus.PROGRAM_COUNTER,
        )
        yield code(
            from_d_bus=FromDBus.PROGRAM_COUNTER_HIGH,
            to_d_bus=ToDBus.TEMPORARY_LOW,
        )
        yield from NextOperation(ctx)

    @compiler.instruction(f"j{name}x")
    def jmpx(ctx: Context):
        if not condition(ctx):
            yield from NextOperation(ctx)
            return

        yield code(
            from_d_bus=FromDBus.PROGRAM_COUNTER_HIGH,
            to_d_bus=ToDBus.ZH,
        )
        yield code(
            from_d_bus=FromDBus.PROGRAM_COUNTER_LOW,
            to_d_bus=ToDBus.ZL,
        )
        yield from NextOperation(ctx)


# call (7)
for name, condition in conditions.items():
    name = name or "all"

    @compiler.instruction(f"c{name}-[word]")
    def call(ctx: Context):
        if not condition(ctx):
            yield from NextOperation(ctx)
            return

        yield from ReadWord(ctx)
        yield from PushProgramCounter(ctx)
        yield code(
            from_d_bus=FromDBus.PROGRAM_COUNTER_HIGH,
            to_d_bus=ToDBus.TEMPORARY_HIGH,
        )
        yield code(
            from_d_bus=FromDBus.PROGRAM_COUNTER_LOW,
            to_d_bus=ToDBus.TEMPORARY_LOW,
        )
        yield from NextOperation(ctx)


# ret (7)
for name, condition in conditions.items():
    name = name or "et"

    @compiler.instruction(f"r{name}")
    def ret(ctx: Context):
        if not condition(ctx):
            yield from NextOperation(ctx)
            return

        yield code(
            from_d_bus=FromDBus.PROGRAM_COUNTER_HIGH,
            to_d_bus=ToDBus.MEMORY,
            to_a_bus=ToABus.STACK_POINTER,
            stack_pointer_increment=1,
        )
        yield code(
            from_d_bus=FromDBus.PROGRAM_COUNTER_LOW,
            to_d_bus=ToDBus.MEMORY,
            to_a_bus=ToABus.STACK_POINTER,
            stack_pointer_increment=1,
        )
        yield from NextOperation(ctx)


# inc/dec/not (18)
for operation, selection, mode, carry_mode in [
    ("inc", 0x0, 0, 1),
    ("dec", 0xF, 0, 0),
    ("not", 0x0, 1, 0),
]:
    for register, name in [
        (ToDBus.ACCUMULATOR, "ac"),
        (ToDBus.XH, "xh"),
        (ToDBus.YL, "yl"),
        (ToDBus.YH, "yh"),
        (ToDBus.ZL, "zl"),
        (ToDBus.ZH, "zh"),
    ]:

        @compiler.instruction(f"{operation}-{name}")
        def op(ctx: Context):
            if carry_mode == 2:
                carry = ctx.carry
            else:
                carry = carry_mode

            yield code(
                from_d_bus=FromDBus.TEMPORARY_HIGH,
                to_d_bus=register,
            )
            yield code(
                from_d_bus=register,
                alu_selection=selection,
                alu_mode=mode,
                alu_carry=carry,
                alu_enable=1,
                flags_from_alu=1,
            )
            yield from NextOperation(ctx)


# add/sub/nand/xor/nor/adc/sbb (49)
for operation, selection, mode, carry_mode in [
    ("add", 0x9, 0, 0),
    ("sub", 0x6, 0, 0),
    ("nand", 0x4, 1, 0),
    ("not", 0x0, 1, 0),
    ("xor", 0x6, 1, 0),
    ("nor", 0x1, 1, 0),
    ("adc", 0x9, 0, 2),
    ("sbb", 0xF, 0, 2),
]:
    for register, name in [
        (ToDBus.ACCUMULATOR, "-ac"),
        (ToDBus.XH, "-xh"),
        (ToDBus.YL, "-yl"),
        (ToDBus.YH, "-yh"),
        (ToDBus.ZL, "-zl"),
        (ToDBus.ZH, "-zh"),
        (ToDBus.MEMORY, "i-[byte]"),
    ]:

        @compiler.instruction(f"{operation}{name}")
        def op(ctx: Context):
            if carry_mode == 2:
                carry = ctx.carry
            else:
                carry = carry_mode

            yield code(
                from_d_bus=FromDBus.TEMPORARY_HIGH,
                to_d_bus=register,
            )
            yield code(
                from_d_bus=FromDBus.ACCUMULATOR,
                alu_selection=selection,
                alu_mode=mode,
                alu_carry=carry,
                alu_enable=1,
                flags_from_alu=1,
            )
            yield from NextOperation(ctx)


compiler.save("bin/")
