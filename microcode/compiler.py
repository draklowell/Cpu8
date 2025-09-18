import os.path
from dataclasses import dataclass
from typing import Callable, Generator


def code(
    memory_read: int = 0,
    memory_write: int = 0,
    flags_from_alu: int = 0,
    flags_to_dbus: int = 0,
    flags_from_dbus: int = 0,
    halt: int = 0,
    alu_enable: int = 0,
    alu_carry: int = 0,  # Boundary
    alu_mode: int = 0,
    accumulator_to_dbus: int = 0,
    accumulator_from_dbus: int = 0,
    step_counter_clear: int = 0,
    temporary_to_abus: int = 0,
    temporary_low_to_dbus: int = 0,
    temporary_high_from_dbus: int = 0,
    temporary_low_from_dbus: int = 0,  # Boundary
    instruction_from_dbus: int = 0,
    program_counter_high_from_dbus: int = 0,
    program_counter_low_from_dbus: int = 0,
    program_counter_high_to_dbus: int = 0,
    program_counter_low_to_dbus: int = 0,
    program_counter_increment: int = 0,
    program_counter_to_abus: int = 0,
    stack_pointer_high_from_dbus: int = 0,  # Boundary
    stack_pointer_low_from_dbus: int = 0,
    stack_pointer_high_to_dbus: int = 0,
    stack_pointer_low_to_dbus: int = 0,
    stack_pointer_increment: int = 0,
    alu_opcode: int = 0,  # Boundary
    stack_pointer_decrement: int = 0,
    stack_pointer_to_abus: int = 0,
    file_write_index: int = 0x7,
    file_read_index: int = 0x7,
):
    not_halt = 1 - halt
    not_program_counter_increment = 1 - program_counter_increment
    not_stack_pointer_increment = 1 - stack_pointer_increment
    not_stack_pointer_decrement = 1 - stack_pointer_decrement
    not_alu_carry = 1 - alu_carry

    return (
        (
            (memory_read << 0)
            | (memory_write << 1)
            | (flags_from_alu << 2)
            | (flags_to_dbus << 3)
            | (flags_from_dbus << 4)
            | (not_halt << 5)
            | (alu_enable << 6)
            | (not_alu_carry << 7)
        ),
        (
            (alu_mode << 0)
            | (accumulator_to_dbus << 1)
            | (accumulator_from_dbus << 2)
            | (step_counter_clear << 3)
            | (temporary_to_abus << 4)
            | (temporary_low_to_dbus << 5)
            | (temporary_high_from_dbus << 6)
            | (temporary_low_from_dbus << 7)
        ),
        (
            (instruction_from_dbus << 0)
            | (program_counter_high_from_dbus << 1)
            | (program_counter_low_from_dbus << 2)
            | (program_counter_high_to_dbus << 3)
            | (program_counter_low_to_dbus << 4)
            | (not_program_counter_increment << 5)
            | (program_counter_to_abus << 6)
            | (stack_pointer_high_from_dbus << 7)
        ),
        (
            (stack_pointer_low_from_dbus << 0)
            | (stack_pointer_high_to_dbus << 1)
            | (stack_pointer_low_to_dbus << 2)
            | (not_stack_pointer_increment << 3)
            | (alu_opcode << 4)
        ),
        (
            (not_stack_pointer_decrement << 0)
            | (stack_pointer_to_abus << 1)
            | (file_write_index << 2)
            | (file_read_index << 5)
        ),
    )


@dataclass
class Flags:
    sign: int
    carry: int
    zero: int

    def get_value(self) -> int:
        not_carry = 1 - self.carry
        return (self.sign << 8) | (not_carry << 9) | (self.zero << 10)


POSSIBLE_FLAGS = [
    Flags(0, 0, 0),
    Flags(0, 0, 1),
    Flags(0, 1, 0),
    Flags(0, 1, 1),
    Flags(1, 0, 0),
    Flags(1, 0, 1),
    Flags(1, 1, 0),
    Flags(1, 1, 1),
]


Code = tuple[int, int, int, int, int]


class Compiler:
    def __init__(self):
        self.blocks = [bytearray(2**15) for _ in range(5)]
        self.counter = 0
        self.table = {}

    def instruction(self, name: str):
        def _instruction(callback: Callable[[Flags], Generator[Code, None, None]]):
            self.create_instruction(name, callback)

        return _instruction

    def create_instruction(
        self,
        name: str,
        callback: Callable[[Flags], Generator[Code, None, None]],
    ):
        # Name is reserved for future use

        for flags in POSSIBLE_FLAGS:
            base = self.counter | flags.get_value()
            for step, opcodes in enumerate(callback(flags)):
                if step > 15:
                    raise ValueError(f"Too much microcode for instruction {name}")

                address = base | (step << 11)

                for block, value in enumerate(opcodes):
                    self.blocks[block][address] = value

        self.table[self.counter] = name
        self.counter += 1

        if self.counter > 255:
            raise ValueError(f"Too much instructions")

    def save(self, path: str):
        for index, block in enumerate(self.blocks):
            with open(os.path.join(path, f"rom{index}.bin"), "wb") as file:
                file.write(block)

        with open(os.path.join(path, "table.txt"), "w") as file:
            for code, name in sorted(self.table.items()):
                file.write(hex(code).upper()[2:].zfill(2) + ": " + name + "\n")
