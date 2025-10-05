import csv
from typing import Dict, List


class InstructionParser:

    def __init__(self):
        self.instructions_by_hex = {}
        self.instructions_by_dec = {}
        self.instructions_by_mnemonic = {}

    def parse_csv_file(self, filename: str) -> Dict:
        with open(filename, 'r', encoding='utf-8') as file:
            return self.parse(file.read())

    def parse(self, content) -> Dict:

        instructions = {}

        lines = content.strip().split('\n')
        reader = csv.reader(lines)

        header = next(reader)

        for row in reader:
            if len(row) < 5:
                continue
                
            hex_opcode, dec_opcode, mnemonic, max_cycles, min_cycles = row

            hex_val = int(hex_opcode, 16)
            dec_val = int(dec_opcode)
            
            instruction_data = {
                'hex_opcode': hex_val,
                'dec_opcode': dec_val,
                'mnemonic': mnemonic,
                'max_cycles': int(max_cycles),
                'min_cycles': int(min_cycles),
                'raw_mnemonic': mnemonic
            }

            self._analyze_instruction_type(instruction_data)

            instructions[dec_val] = instruction_data
            self.instructions_by_hex[hex_val] = instruction_data
            self.instructions_by_dec[dec_val] = instruction_data
            self.instructions_by_mnemonic[mnemonic] = instruction_data
        
        return instructions


    def _analyze_instruction_type(self, instruction: Dict):
        """
        determines type o mnemonic and args
        """

        mnemonic = instruction["mnemonic"]

        # determine type of instruction
        if mnemonic.startswith('ldi-'):
            instruction['type'] = 'load_immediate'
        elif mnemonic.startswith('ld-'):
            instruction['type'] = 'load_memory' 
        elif mnemonic.startswith('st-'):
            instruction['type'] = 'store_memory'
        elif mnemonic.startswith('ldx-'):
            instruction['type'] = 'load_indexed'
        elif mnemonic.startswith('stx-'):
            instruction['type'] = 'store_indexed'
        elif mnemonic.startswith('mov-'):
            instruction['type'] = 'move'
        elif mnemonic.startswith('push-'):
            instruction['type'] = 'push'
        elif mnemonic.startswith('pop-'):
            instruction['type'] = 'pop'
        elif mnemonic.startswith('j') and '[word]' in mnemonic:
            instruction['type'] = 'jump_absolute'
        elif mnemonic.startswith('j') and 'x' in mnemonic:
            instruction['type'] = 'jump_indexed'
        elif mnemonic.startswith('c') and '[word]' in mnemonic:
            instruction['type'] = 'call_absolute'
        elif mnemonic.startswith('r'):
            instruction['type'] = 'return'
        elif mnemonic in ['nop', 'inte', 'intd', 'inth', 'hlt']:
            instruction['type'] = 'control'
        elif any(mnemonic.startswith(prefix) for prefix in ['add', 'sub', 'nand', 'xor', 'nor', 'adc', 'sbb']):
            instruction['type'] = 'arithmetic'
        elif any(mnemonic.startswith(prefix) for prefix in ['inc', 'dec', 'icc', 'dcb', 'not', 'cmp']):
            instruction['type'] = 'arithmetic_single'
        elif mnemonic in ['shl', 'shr']:
            instruction['type'] = 'shift'
        else:
            instruction['type'] = 'other'

        # determine args
        if '[byte]' in mnemonic:
            instruction['arg_type'] = 'immediate_byte'
            instruction['registers'] = self._extract_registers(mnemonic.replace('-[byte]', ''))
        elif '[word]' in mnemonic:
            instruction['arg_type'] = 'immediate_word'
            instruction['registers'] = self._extract_registers(mnemonic.replace('-[word]', ''))
        else:
            instruction['arg_type'] = 'none'
            instruction['registers'] = self._extract_registers(mnemonic)

    
    def _extract_registers(self, mnemonic: str) -> List[str]:
        """
        determines names of registers from mnemonics
        """
        parts = mnemonic.split('-')
        registers = []
        
        for part in parts:
            if part in ['ac', 'xh', 'yl', 'yh', 'zl', 'zh', 'fr', 'x', 'y', 'z', 'sp', 'pc']:
                registers.append(part)
        
        return registers




    def get_instruction_by_opcode(self, opcode: int) -> Dict:
        return self.instructions_by_dec.get(opcode)

    def get_instruction_by_hex(self, hex_opcode: int) -> Dict:
        return self.instructions_by_hex.get(hex_opcode)

    def get_instruction_by_mnemonic(self, mnemonic: str) -> Dict:
        return self.instructions_by_mnemonic.get(mnemonic)

    

    def summary(self):

        print(f"⟶ Total num of instructions: {len(self.instructions_by_dec)}")

        types = {}
        for instr in self.instructions_by_dec.values():
            instr_type = instr['type']
            types[instr_type] = types.get(instr_type, 0) + 1
        
        print("\n⟶ Types distribution:")
        for instr_type, count in sorted(types.items()):
            print(f"  {instr_type}: {count} instructions")


def parse(filename) -> InstructionParser:
    parser = InstructionParser()
    parser.parse_csv_file(filename)
    return parser


# if __name__ == "__main__":
#     parser = parse("emulation/table.csv")
#     parser.summary()
    
#     nop_instr = parser.get_instruction_by_opcode(0)
#     print(f"\nNOP instruction: {nop_instr}")
