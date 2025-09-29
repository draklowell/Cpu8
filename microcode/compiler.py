import os.path
from dataclasses import dataclass
from enum import IntEnum
from typing import Callable, Generator


class ToABus(IntEnum):
    DISABLE = 0x0
    STACK_POINTER = 0x1
    PROGRAM_COUNTER = 0x2
    TEMPORARY = 0x3


class FromDBus(IntEnum):
    DISABLE = 0x0
    MEMORY = 0x1
    STACK_POINTER_HIGH = 0x2
    STACK_POINTER_LOW = 0x3
    PROGRAM_COUNTER_HIGH = 0x4
    PROGRAM_COUNTER_LOW = 0x5
    TEMPORARY_HIGH = 0x6
    TEMPORARY_LOW = 0x7
    ACCUMULATOR = 0x8
    XH = 0x9
    YL = 0xA
    YH = 0xB
    ZL = 0xC
    ZH = 0xD
    FLAGS = 0xE
    INSTRUCTION_REGISTER = 0xF


class ToDBus(IntEnum):
    DISABLE = 0x0
    MEMORY = 0x1
    STACK_POINTER_HIGH = 0x2
    STACK_POINTER_LOW = 0x3
    PROGRAM_COUNTER_HIGH = 0x4
    PROGRAM_COUNTER_LOW = 0x5
    TEMPORARY_HIGH = 0x6
    TEMPORARY_LOW = 0x7
    ACCUMULATOR = 0x8
    XH = 0x9
    YL = 0xA
    YH = 0xB
    ZL = 0xC
    ZH = 0xD
    FLAGS = 0xE
    INTERRUPT_HANDLE_CONSTANT = 0xF


def code(
    from_d_bus: FromDBus = FromDBus.DISABLE,
    to_d_bus: ToDBus = ToDBus.DISABLE,  # Boundary
    to_a_bus: ToABus = ToABus.DISABLE,
    alu_mode: int = 0,
    alu_carry: int = 0,
    alu_selection: int = 0,  # Boundary
    alu_enable: int = 0,
    flags_from_alu: int = 0,
    step_counter_clear: int = 0,
    program_counter_increment: int = 0,
    stack_pointer_increment: int = 0,
    stack_pointer_decrement: int = 0,
    halt: int = 0,
    interrupt_acknowledge: int = 0,  # Boundary
    accumulator_shift_left: int = 0,
    accumulator_shift_right: int = 0,
    interrupt_enable: int = 0,
    interrupt_disable: int = 0,
):
    if to_a_bus == ToABus.STACK_POINTER and from_d_bus in {
        FromDBus.STACK_POINTER_HIGH,
        FromDBus.STACK_POINTER_LOW,
    }:
        raise ValueError("illegal simultaneous read/write to stack pointer")

    not_halt = 1 - halt
    not_program_counter_increment = 1 - program_counter_increment
    not_stack_pointer_increment = 1 - stack_pointer_increment
    not_stack_pointer_decrement = 1 - stack_pointer_decrement
    not_alu_carry = 1 - alu_carry

    return (
        ((from_d_bus.value << 0) | (to_d_bus.value << 4)),
        (
            (to_a_bus.value << 0)
            | (alu_mode << 2)
            | (not_alu_carry << 3)
            | (alu_selection << 4)
        ),
        (
            (alu_enable << 0)
            | (flags_from_alu << 1)
            | (step_counter_clear << 2)
            | (not_program_counter_increment << 3)
            | (not_stack_pointer_increment << 4)
            | (not_stack_pointer_decrement << 5)
            | (not_halt << 6)
            | (interrupt_acknowledge << 7)
        ),
        (
            (accumulator_shift_left << 0)
            | (accumulator_shift_right << 1)
            | (interrupt_enable << 2)
            | (interrupt_disable << 3)
        ),
    )


@dataclass
class Context:
    sign: int
    carry: int
    zero: int
    interrupt: int

    def get_value(self) -> int:
        not_carry = 1 - self.carry
        return (
            (self.sign << 8)
            | (not_carry << 9)
            | (self.zero << 10)
            | (self.interrupt << 15)
        )


POSSIBLE_CONTEXTS = [
    Context(s, c, z, i)
    for s in range(2)
    for c in range(2)
    for z in range(2)
    for i in range(2)
]


Code = tuple[int, int, int, int]


class Compiler:
    def __init__(self):
        self.blocks = [bytearray(2**16) for _ in range(4)]
        self.counter = 0
        self.table = {}

    def instruction(self, name: str, code: int | None = None):
        def _instruction(callback: Callable[[Context], Generator[Code, None, None]]):
            self.create_instruction(name, callback, code)

        return _instruction

    def create_instruction(
        self,
        name: str,
        callback: Callable[[Context], Generator[Code, None, None]],
        code: int | None = None,
    ):
        # Name is reserved for future use
        if code is None:
            while self.counter in self.table:
                self.counter += 1
            code = self.counter
        else:
            if code in self.table:
                raise ValueError(
                    f"Cannot create more than one instruction with the same code: {name} ({code})"
                )

        if code > 255:
            raise ValueError("Too many instructions")

        for ctx in POSSIBLE_CONTEXTS:
            base = code | ctx.get_value()
            for step, opcodes in enumerate(callback(ctx)):
                if step > 15:
                    raise ValueError(f"Too much microcode for instruction {name}")

                address = base | (step << 11)

                for block, value in enumerate(opcodes):
                    self.blocks[block][address] = value

        self.table[code] = name

    def save(self, path: str):
        for index, block in enumerate(self.blocks):
            with open(os.path.join(path, f"rom{index}.bin"), "wb") as file:
                file.write(block)

        with open(os.path.join(path, "table.txt"), "w") as file:
            for code, name in sorted(self.table.items()):
                file.write(hex(code).upper()[2:].zfill(2) + ": " + name + "\n")
