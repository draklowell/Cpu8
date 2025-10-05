import os.path
from dataclasses import dataclass
from typing import Callable, Generator

import components
from components import Component


def code(
    bus_reader: Component = components.DISABLE,
    alu_mode: int = 0,
    alu_carry: int = 0,
    flags_from_alu: int = 0,  # Boundary
    bus_writer: Component = components.DISABLE,
    step_counter_clear: int = 0,
    halt: int = 0,
    program_counter_increment: int = 0,  # Boundary
    alu_selection: int = 0,
    stack_pointer_decrement: int = 0,
    stack_pointer_increment: int = 0,
    accumulator_shift_left: int = 0,  # Boundary
    accumulator_shift_right: int = 0,
    interrupt_enable: int = 0,
    interrupt_disable: int = 0,
    address_decrement: int = 0,
    address_increment: int = 0,
):
    if bus_reader.reader is None:
        raise ValueError(f"Component {bus_reader.name} can't read from bus")
    if bus_writer.writer is None:
        raise ValueError(f"Component {bus_writer.name} can't write to bus")

    not_halt = 1 - halt
    not_program_counter_increment = 1 - program_counter_increment
    not_stack_pointer_decrement = 1 - stack_pointer_decrement
    not_stack_pointer_increment = 1 - stack_pointer_increment
    not_alu_carry = 1 - alu_carry
    not_address_decrement = 1 - address_decrement
    not_address_increment = 1 - address_increment

    return (
        (
            (bus_reader.reader << 0)
            | (alu_mode << 5)
            | (not_alu_carry << 6)
            | (flags_from_alu << 7)
        ),
        (
            (bus_writer.writer << 0)
            | (step_counter_clear << 5)
            | (not_halt << 6)
            | (not_program_counter_increment << 7)
        ),
        (
            (alu_selection << 0)
            | (not_stack_pointer_decrement << 4)
            | (not_stack_pointer_increment << 5)
            | (accumulator_shift_left << 6)
            | (accumulator_shift_right << 7)
        ),
        (
            (interrupt_enable << 0)
            | (interrupt_disable << 1)
            | (not_address_decrement << 2)
            | (not_address_increment << 3)
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
