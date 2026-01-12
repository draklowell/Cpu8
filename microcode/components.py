from dataclasses import dataclass


@dataclass
class Component:
    reader: int | None
    writer: int | None
    name: str

    def __str__(self):
        return self.name


DISABLE = Component(0x00, 0x00, "Disable")
MEMORY = Component(0x01, 0x01, "Memory")
STACK_POINTER_HIGH = Component(0x02, 0x02, "StackPointerHigh")
STACK_POINTER_LOW = Component(0x03, 0x03, "StackPointerLow")
PROGRAM_COUNTER_HIGH = Component(0x04, 0x04, "ProgramCounterHigh")
PROGRAM_COUNTER_LOW = Component(0x05, 0x05, "ProgramCounterLow")
ARGUMENT_HIGH = Component(0x06, 0x06, "ArgumentHigh")
ARGUMENT_LOW = Component(0x07, 0x07, "ArgumentLow")
ACCUMULATOR = Component(0x08, 0x08, "Accumulator")
XH = Component(0x09, 0x09, "XH")
YL = Component(0x0A, 0x0A, "YL")
YH = Component(0x0B, 0x0B, "YH")
ZL = Component(0x0C, 0x0C, "ZL")
ZH = Component(0x0D, 0x0D, "ZH")
FLAGS = Component(0x0E, 0x0E, "Flags")
INSTRUCTION = Component(0x0F, None, "Instruction")
ADDRESS_HIGH = Component(0x10, None, "AddressHigh")
ADDRESS_LOW = Component(0x11, None, "AddressLow")
INTERRUPT_HANDLE_CONSTANT = Component(None, 0x0F, "InterruptHandleConstant")
ALU = Component(None, 0x10, "ALU")
INTERRUPT_CODE = Component(None, 0x11, "InterruptCode")

ALL_COMPONENTS = [
    DISABLE,
    MEMORY,
    STACK_POINTER_HIGH,
    STACK_POINTER_LOW,
    PROGRAM_COUNTER_HIGH,
    PROGRAM_COUNTER_LOW,
    ARGUMENT_HIGH,
    ARGUMENT_LOW,
    ACCUMULATOR,
    XH,
    YL,
    YH,
    ZL,
    ZH,
    FLAGS,
    INSTRUCTION,
    ADDRESS_HIGH,
    ADDRESS_LOW,
    INTERRUPT_HANDLE_CONSTANT,
    ALU,
    INTERRUPT_CODE,
]

STACK_POINTER = (STACK_POINTER_HIGH, STACK_POINTER_LOW)
PROGRAM_COUNTER = (PROGRAM_COUNTER_HIGH, PROGRAM_COUNTER_LOW)
ARGUMENT = (ARGUMENT_HIGH, ARGUMENT_LOW)
X = (XH, ACCUMULATOR)
Y = (YH, YL)
Z = (ZH, ZL)
ADDRESS = (ADDRESS_HIGH, ADDRESS_LOW)
