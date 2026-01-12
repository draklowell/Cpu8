import csv
import os.path
from dataclasses import dataclass
from typing import Callable, Generator

import components
from components import Component


def code(
    bus_reader: Component = components.DISABLE,
    alu_mode: int = 0,
    alu_carry: int = 0,
    flags_from_alu: int = 0,
    bus_writer: Component = components.DISABLE,
    step_counter_clear: int = 0,
    halt: int = 0,
    program_counter_increment: int = 0,
    alu_selection: int = 0,
    stack_pointer_decrement: int = 0,
    stack_pointer_increment: int = 0,
    accumulator_shift_left: int = 0,
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

    not_flags_from_alu = 1 - flags_from_alu
    not_alu_carry = 1 - alu_carry
    not_step_counter_clear = 1 - step_counter_clear
    not_halt = 1 - halt
    not_interrupt_enable = 1 - interrupt_enable
    not_interrupt_disable = 1 - interrupt_disable

    reader_0 = bus_reader.reader & 0x01
    reader_1 = (bus_reader.reader & 0x02) >> 1
    reader_2 = (bus_reader.reader & 0x04) >> 2
    reader_3 = (bus_reader.reader & 0x08) >> 3
    reader_4 = (bus_reader.reader & 0x10) >> 4
    not_reader_4 = 1 - reader_4

    writer_0 = bus_writer.writer & 0x01
    writer_1 = (bus_writer.writer & 0x02) >> 1
    writer_2 = (bus_writer.writer & 0x04) >> 2
    writer_3 = (bus_writer.writer & 0x08) >> 3
    writer_4 = (bus_writer.writer & 0x10) >> 4
    not_writer_4 = 1 - writer_4

    alu_selection_0 = alu_selection & 0x1
    alu_selection_1 = (alu_selection & 0x2) >> 1
    alu_selection_2 = (alu_selection & 0x4) >> 2
    alu_selection_3 = (alu_selection & 0x8) >> 3

    return (
        (
            (reader_2 << 0)
            | (reader_1 << 1)
            | (reader_0 << 2)
            | (writer_0 << 3)
            | (not_flags_from_alu << 4)
            | (not_alu_carry << 5)
            | (alu_mode << 6)
            | (reader_3 << 7)
        ),
        (
            (writer_3 << 0)
            | (writer_2 << 1)
            | (writer_1 << 2)
            | (alu_selection_1 << 3)
            | (alu_selection_0 << 4)
            | (program_counter_increment << 5)
            | (not_halt << 6)
            | (not_step_counter_clear << 7)
        ),
        (
            (stack_pointer_decrement << 0)
            | (alu_selection_3 << 1)
            | (alu_selection_2 << 2)
            | (not_writer_4 << 3)
            | (not_reader_4 << 4)
            | (accumulator_shift_right << 5)
            | (accumulator_shift_left << 6)
            | (stack_pointer_increment << 7)
        ),
        (
            (not_interrupt_enable << 0)
            | (not_interrupt_disable << 1)
            | (address_decrement << 2)
            | (address_increment << 3)
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
        not_interrupt = 1 - self.interrupt
        return (
            (self.sign << 8)
            | (not_carry << 9)
            | (self.zero << 10)
            | (not_interrupt << 15)
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
    blocks: list[bytearray]
    counter: int
    table: dict[int, tuple[str, list[int]]]

    def __init__(self, default_code: Code = code(halt=1)):
        self.blocks = [
            bytearray(bytes([value]) * 65536) for _, value in enumerate(default_code)
        ]
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

        cycles = []

        for ctx in POSSIBLE_CONTEXTS:
            base = code | ctx.get_value()
            for step, opcodes in enumerate(callback(ctx)):
                if step > 15:
                    raise ValueError(f"Too much microcode for instruction {name}")

                address = base | (step << 11)

                for block, value in enumerate(opcodes):
                    self.blocks[block][address] = value

            cycles.append(step + 1)  # last step

        self.table[code] = (name, cycles)

    def save(self, path: str):
        physical_blocks = []
        for index, block in enumerate(self.blocks):
            physical_blocks.append(block[:32768])
            physical_blocks.append(block[32768:])

            with open(os.path.join(path, f"rom{index}.bin"), "wb") as file:
                file.write(block)

        for index, block in enumerate(physical_blocks):
            with open(os.path.join(path, f"table{index}.bin"), "wb") as file:
                file.write(block)

        with open(os.path.join(path, "table.csv"), "w") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "hexOpcode",
                    "decOpcode",
                    "mnemonic",
                    "maxCycles",
                    "minCycles",
                ],
            )
            writer.writeheader()
            for code, (name, cycles) in sorted(self.table.items()):
                writer.writerow(
                    {
                        "hexOpcode": hex(code)[2:].zfill(2),
                        "decOpcode": str(code).zfill(3),
                        "mnemonic": name,
                        "maxCycles": max(cycles),
                        "minCycles": min(cycles),
                    }
                )
