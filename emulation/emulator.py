'''
emulator for 8-bit cpu
'''

from typing import Dict
from parser import parse

class CPU:

    def __init__(self, memory_size=65536):

        self.memory = bytearray(memory_size)

        # 8 bit registers 
        self.ac = 0  # X low / Accum
        self.xh = 0  # X High
        self.yl = 0  # Y Low
        self.yh = 0  # Y High
        self.zl = 0  # Z Low
        self.zh = 0  # Z High
        self.fr = 0  # Flags Register 

        # program counter
        self.pc = 0

        # stack pointer
        self.sp = 0

        # instruction register
        self.ir = 0

        # step counter
        self.step = 0

        # cpu state
        self.interrupts_enabled = False
        self.halt = False
        self.cycles = 0


        self.instruction_set = None
        self.load_instruction_table()



    def load_instruction_table(self):
        try:
            self.instruction_set = parse("emulation/table.csv")
            print(f"⟶ Loaded {len(self.instruction_set.instructions_by_dec)} instructions")
        except FileNotFoundError:
            print("file not found :(")



    @property
    def x(self):
        return (self.xh << 8) | self.ac

    @x.setter
    def x(self, value):
        self.xh = (value >> 8) & 0xFF
        self.ac = value & 0xFF



    @property
    def y(self):
        return (self.yh << 8) | self.yl

    @y.setter
    def y(self, value):
        self.yh = (value >> 8) & 0xFF
        self.yl = value & 0xFF



    @property
    def z(self):
        return (self.zh << 8) | self.zl

    @z.setter
    def z(self, value):
        self.zh = (value >> 8) & 0xFF
        self.zl = value & 0xFF



    # FLAGS #
    def get_flag_sign(self):
        '1 if result < 0'
        return (self.fr >> 2) & 1

    def get_flag_carry(self):
        '1 if carry'
        return not ((self.fr >> 1) & 1)

    def get_flag_zero(self):
        '1 if result is zero'
        return self.fr & 1

    def set_flags(self, result, carry=None):

        zero = 1 if (result & 0xFF) == 0 else 0
        self.fr = (self.fr & 0b110) | zero

        sign = 1 if (result & 0x80) else 0
        self.fr = (self.fr & 0b011) | (sign << 2)
        
        if carry is not None:
            not_carry = 0 if carry else 1
            self.fr = (self.fr & 0b101) | (not_carry << 1)
        elif result > 0xFF or result < 0:
            # if result is out if byte automatically find carry
            not_carry = 0 if (result > 0xFF or result < 0) else 1
            self.fr = (self.fr & 0b101) | (not_carry << 1)
    


    # READ/WRITE FROM MEM #
    def read_byte(self, address):
        return self.memory[address & 0xFFFF]

    def write_byte(self, address, value):
        self.memory[address & 0xFFFF] = value & 0xFF
    
    def read_word(self, address):
        high = self.read_byte(address)
        low = self.read_byte(address + 1)
        return (high << 8) | low
    
    def write_word(self, address, value):
        self.write_byte(address, (value >> 8) & 0xFF)
        self.write_byte(address + 1, value & 0xFF)


    # STACK LOGIC #
    def push_byte(self, value):
        self.sp = (self.sp - 1) & 0xFFFF
        self.write_byte(self.sp, value)

    def pop_byte(self):
        value = self.read_byte(self.sp)
        self.sp = (self.sp + 1) & 0xFFFF
        return value
    
    def push_word(self, value):
        self.push_byte(value & 0xFF)         # Low 
        self.push_byte((value >> 8) & 0xFF)  # High 
    
    def pop_word(self):
        high = self.pop_byte()
        low = self.pop_byte()
        return (high << 8) | low



    # FETCH #
    def fetch_byte(self):
        value = self.read_byte(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        return value
    
    def fetch_word(self):
        value = self.read_word(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        return value

    

    # INSTRUCTION EXECUTION #

    def execute_instruction(self):

        if self.halt:
            return 0
        
        opcode = self.fetch_byte()

        instruction = self.instruction_set.get_instruction_by_opcode(opcode)
        if not instruction:
            raise ValueError(f"unknown opcode: {opcode:02x}")

        print(f"executing: {instruction['mnemonic']} (opcode: {opcode:02x})")

        cycles = self._execute_instruction_logic(instruction)
        self.cycles += cycles
        
        return cycles
    

    def _execute_instruction_logic(self, instruction: Dict):

        mnemonic = instruction["mnemonic"]

        # CONTROL INSTRUCTIONS
        if mnemonic == 'nop':
            return self.nop()
        elif mnemonic == 'inte':
            return self.inte()
        elif mnemonic == 'intd':
            return self.intd()
        elif mnemonic == 'inth':
            return self.inth()
        elif mnemonic == 'hlt':
            return self.hlt()

        # LOAD IMMEDIATE - BYTE
        elif mnemonic == 'ldi-ac-[byte]':
            return self.ldi_byte('ac')
        elif mnemonic == 'ldi-xh-[byte]':
            return self.ldi_byte('xh')
        elif mnemonic == 'ldi-yl-[byte]':
            return self.ldi_byte('yl')
        elif mnemonic == 'ldi-yh-[byte]':
            return self.ldi_byte('yh')
        elif mnemonic == 'ldi-fr-[byte]':
            return self.ldi_byte('fr')
        elif mnemonic == 'ldi-zl-[byte]':
            return self.ldi_byte('zl')
        elif mnemonic == 'ldi-zh-[byte]':
            return self.ldi_byte('zh')
        
        # LOAD IMMEDIATE - WORD
        elif mnemonic == 'ldi-x-[word]':
            return self.ldi_word('x')
        elif mnemonic == 'ldi-y-[word]':
            return self.ldi_word('y')
        elif mnemonic == 'ldi-z-[word]':
            return self.ldi_word('z')
        elif mnemonic == 'ldi-sp-[word]':
            return self.ldi_word('sp')
        
        # LOAD FROM MEMORY
        elif mnemonic == 'ld-ac-[word]':
            return self.ld_memory('ac')
        elif mnemonic == 'ld-xh-[word]':
            return self.ld_memory('xh')
        elif mnemonic == 'ld-yl-[word]':
            return self.ld_memory('yl')
        elif mnemonic == 'ld-yh-[word]':
            return self.ld_memory('yh')
        elif mnemonic == 'ld-fr-[word]':
            return self.ld_memory('fr')
        elif mnemonic == 'ld-zl-[word]':
            return self.ld_memory('zl')
        elif mnemonic == 'ld-zh-[word]':
            return self.ld_memory('zh')
        
        # LOAD INDEXED
        elif mnemonic == 'ldx-ac':
            return self.ldx('ac')
        elif mnemonic == 'ldx-xh':
            return self.ldx('xh')
        elif mnemonic == 'ldx-yl':
            return self.ldx('yl')
        elif mnemonic == 'ldx-yh':
            return self.ldx('yh')
        elif mnemonic == 'ldx-fr':
            return self.ldx('fr')
        
        # STORE TO MEMORY
        elif mnemonic == 'st-[word]-ac':
            return self.st_memory('ac')
        elif mnemonic == 'st-[word]-xh':
            return self.st_memory('xh')
        elif mnemonic == 'st-[word]-yl':
            return self.st_memory('yl')
        elif mnemonic == 'st-[word]-yh':
            return self.st_memory('yh')
        elif mnemonic == 'st-[word]-fr':
            return self.st_memory('fr')
        elif mnemonic == 'st-[word]-zl':
            return self.st_memory('zl')
        elif mnemonic == 'st-[word]-zh':
            return self.st_memory('zh')
        
        # STORE INDEXED
        elif mnemonic == 'stx-ac':
            return self.stx('ac')
        elif mnemonic == 'stx-xh':
            return self.stx('xh')
        elif mnemonic == 'stx-yl':
            return self.stx('yl')
        elif mnemonic == 'stx-yh':
            return self.stx('yh')
        elif mnemonic == 'stx-fr':
            return self.stx('fr')
        
        # MOVE INSTRUCTIONS (unfinished)
        elif mnemonic.startswith('mov-'):
            return self.handle_move(mnemonic)

        # PUSH/POP
        elif mnemonic.startswith('push-'):
            return self.handle_push(mnemonic)
        elif mnemonic.startswith('pop-'):
            return self.handle_pop(mnemonic)
        
        # JUMP INSTRUCTIONS (unfinished)
        elif mnemonic == 'jmp-[word]':
            return self.jmp_word()
        elif mnemonic == 'jmpx':
            return self.jmp_x()

        # ARITHMETIC (unfinished)
        elif mnemonic == 'add-ac':
            return self.add('ac')
        elif mnemonic == 'add-xh':
            return self.add('xh')
        elif mnemonic == 'addi-[byte]':
            return self.addi_byte()

        else:
            print(f"✖ Instruction {mnemonic} has not been executed")
            return instruction['min_cycles']
        

    # CONTROL INSTRUCTIONS 
    def nop(self):
        "no operation"
        return 3
    
    def inte(self):
        "Interrupt enable"
        return 4
    
    def intd(self):
        "Interrupt disable"
        return 4
    
    def inth(self):
        "Software interrupt"
        self.push_word(self.pc)
        # тут має бути типу перехід до interrupt controller ???
        return 11
    
    def hlt(self):
        "CPU Halt"
        self.halt = True
        return 1
    
    # LOAD IMMEDIATE - BYTE
    def ldi_byte(self, register):
        "Load immediate byte to register"
        value = self.fetch_byte()
        setattr(self, register, value)
        return 6
    
    # LOAD IMMEDIATE - WORD
    def ldi_word(self, register):
        "Load immediate word to register"
        value = self.fetch_word()
        if register == 'sp':
            self.sp = value
        else:
            setattr(self, register, value)
        return 7
    
    # LOAD FROM MEMORY 
    def ld_memory(self, register):
        "Load from memory to register"
        address = self.fetch_word()
        value = self.read_byte(address)
        setattr(self, register, value)
        return 10

    # LOAD INDEXED
    def ldx(self, register):
        "Load indexed (from address in Z)"
        value = self.read_byte(self.z)
        setattr(self, register, value)
        return 6
    
    # STORE TO MEMORY
    def st_memory(self, register):
        "Store register to memory"
        address = self.fetch_word()
        value = getattr(self, register)
        self.write_byte(address, value)
        return 10

    # STORE INDEXED
    def stx(self, register):
        "Store indexed (to address in Z)"
        value = getattr(self, register)
        self.write_byte(self.z, value)
        return 6
    
    # MOVE INSTRUCTIONS
    def handle_move(self, mnemonic):
        "Handle move instruction"

        parts = mnemonic.split("-")
        
        if len(parts) == 3:      # mov-dest-src
            dest, src = parts[1], parts[2]

            if dest == 'sp' and src == 'z':
                self.sp = self.z
                return 5
            elif dest == 'z' and src == 'sp':
                self.z = self.sp
                return 5
            elif dest == 'z' and src == 'pc':
                self.z = self.pc
                return 5
            else:                           # mov register to register
                value = getattr(self, src)
                setattr(self, dest, value)
                return 4
        return 4
    
    # PUSH/POP INSTRUCTIONS
    def handle_push(self, mnemonic):
        "Handle push instructions"
        register = mnemonic.split('-')[1]
        
        if register in ['ac', 'xh', 'yl', 'yh', 'fr', 'zl', 'zh']:
            value = getattr(self, register)
            self.push_byte(value)
            return 6
        elif register in ['x', 'y', 'z', 'pc']:
            value = getattr(self, register)
            self.push_word(value)
            return 7
        return 6
    
    def handle_pop(self, mnemonic):
        "Handle pop instructions"
        register = mnemonic.split('-')[1]
        
        if register in ['ac', 'xh', 'yl', 'yh', 'fr', 'zl', 'zh']:
            value = self.pop_byte()
            setattr(self, register, value)
            return 7
        elif register in ['x', 'y', 'z']:
            value = self.pop_word()
            setattr(self, register, value)
            return 8
        return 7
    
    # JUMP INSTRUCTIONS
    def jmp_word(self):
        "Jump to address"
        address = self.fetch_word()
        self.pc = address
        return 9

    def jmp_x(self):
        "Jump to address in X"
        self.pc = self.x
        return 5

    # ARITHMETIC INSTRUCTIONS
    def add(self, register):
        "Add register to AC"
        value = getattr(self, register)
        result = self.ac + value
        self.set_flags(result)
        self.ac = result & 0xFF
        return 5

    def addi_byte(self):
        "Add immediate byte to AC"
        value = self.fetch_byte()
        result = self.ac + value
        self.set_flags(result)
        self.ac = result & 0xFF
        return 7


    def reset(self):
        self.ac = 0
        self.xh = 0
        self.yl = 0
        self.yh = 0
        self.zl = 0
        self.zh = 0
        self.fr = 0
        self.pc = 0
        self.sp = 0
        self.ir = 0
        self.step = 0
        self.interrupts_enabled = False
        self.halt = False
        self.cycles = 0
    



    def load_program(self, program, start_address=0):
        for i, byte in enumerate(program):
            self.memory[start_address + i] = byte
    
    def run(self, steps=100):
        "Starts emulation for some number of steps"
        for i in range(steps):
            if self.halt:
                print("CPU HALT")
                break
            cycles = self.execute_instruction()
            print(f"Step {i+1}: {self} (cycles: {cycles})")
    

    def __repr__(self):
        return (f"CPU(PC={self.pc:04X}, SP={self.sp:04X}, "
            f"AC={self.ac:02X}, XH={self.xh:02X}, "
            f"YL={self.yl:02X}, YH={self.yh:02X}, "
            f"ZL={self.zl:02X}, ZH={self.zh:02X}, "
            f"FR={self.fr:03b} [S={self.get_flag_sign()} "
            f"C={self.get_flag_carry()} Z={self.get_flag_zero()}], "
            f"X={self.x:04X}, Y={self.y:04X}, Z={self.z:04X})")


# if __name__ == "__main__":
#     cpu = CPU()
#     print(cpu)
    
#     cpu.instruction_set.summary()
    

#     cpu.write_word(0x1000, 0xABCD)
#     print(f"\n⤵ Written word 0xABCD in address 0x1000")
#     print(f"⤴ Read: 0x{cpu.read_word(0x1000):04X}")

#     cpu.x = 0x1234
#     print(f"\n⟹ Set X = 0x1234")
#     print(f"XH = 0x{cpu.xh:02X}, AC = 0x{cpu.ac:02X}")
    
#     cpu.sp = 0xFFFF
#     cpu.push_word(0xBEEF)
#     print(f"\n⤋ Push 0xBEEF to stack")
#     print(f"SP = 0x{cpu.sp:04X}")
#     value = cpu.pop_word()
#     print(f"⤊ Pop: 0x{value:04X}")

#     cpu.set_flags(0x00)  # zero
#     print(f"\nFlags after set_flags(0x00): Z={cpu.get_flag_zero()}")
#     cpu.set_flags(0x80)  # sign
#     print(f"Flags after set_flags(0x80): S={cpu.get_flag_sign()}")
