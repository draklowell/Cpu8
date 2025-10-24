#include "emulator.hpp"

#include <bitset>
#include <csignal>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <ranges>
#include <sstream>
#include <string>
#include <vector>

void CPU::setFlags(int result, bool carryFlag) {

    // result is an int that may be outside 0-255 range to detect carry/borrow
    // Zero flag:
    if ((result & 0xFF) == 0)
        FR = (uint8_t) ((FR & 0xFE) | 0x01);
    else
        FR &= 0xFE;

    // Sign flag (bit 7 of result):
    if (result & 0x80)
        FR = (uint8_t) ((FR & 0xFB) | 0x04);
    else
        FR &= 0xFB;

    // Carry flag (stored inverted in bit1):
    if (carryFlag)
        FR &= 0xFD;
    else
        FR |= 0x02;
}

// STACK LOGIC
uint8_t CPU::popByte() {
    uint8_t val = readByte(SP);
    SP += 1;
    return val;
}
uint16_t CPU::popWord() {
    uint8_t low = popByte();
    uint8_t high = popByte();
    SP += 2;
    return (uint16_t(high) << 8) | low;
}
void CPU::pushByte(uint8_t val) {
    SP -= 1;
    writeByte(SP, val);
}
void CPU::pushWord(uint16_t val) {
    pushByte(val & 0xFF);
    pushByte((val >> 8) & 0xFF);
}

// LOAD INSTRUCTION TABLE
// helper function to split line
std::vector<std::string> splitString(const std::string& s, char delimiter) {
    std::vector<std::string> tokens;
    std::string token;
    std::istringstream tokenStream(s);

    while (std::getline(tokenStream, token, delimiter)) {
        tokens.push_back(token);
    }
    return tokens;
}

void CPU::loadInstructionTable(const std::string& file) {
    std::ifstream input(file);
    if (!input.is_open()) {
        std::cerr << "Error opening file!" << std::endl;
    }
    std::string line;

    std::getline(input, line);

    while (std::getline(input, line)) {
        std::vector<std::string> tokens = splitString(line, ',');
        const uint8_t opCode = static_cast<uint8_t>(std::stoi(tokens[0], nullptr, 16));
        const std::string& mnemonic = tokens[2];
        const int maxCycles = std::stoi(tokens[3]);
        const int minCycles = std::stoi(tokens[4]);
        instructionTable[opCode] = Instruction{opCode, mnemonic, minCycles, maxCycles};
    }
}
// SETUP OPCODE HANDLERS
void CPU::setupOpcodeHandlers() {
    opcodeHandlers[0x00] = [](CPU& cpu) -> int { return cpu.op_nop(); };
    opcodeHandlers[0x01] = [](CPU& cpu) -> int { return cpu.op_inte(); };
    opcodeHandlers[0x02] = [](CPU& cpu) -> int { return cpu.op_intd(); };
    opcodeHandlers[0x03] = [](CPU& cpu) -> int { return cpu.op_ldi_byte(cpu.AC); };
    opcodeHandlers[0x04] = [](CPU& cpu) -> int { return cpu.op_ld_mem(cpu.AC); };
    opcodeHandlers[0x05] = [](CPU& cpu) -> int { return cpu.op_ldi_byte(cpu.XH); };
    opcodeHandlers[0x06] = [](CPU& cpu) -> int { return cpu.op_ld_mem(cpu.XH); };
    opcodeHandlers[0x07] = [](CPU& cpu) -> int { return cpu.op_ldi_byte(cpu.YL); };
    opcodeHandlers[0x08] = [](CPU& cpu) -> int { return cpu.op_ld_mem(cpu.YL); };
    opcodeHandlers[0x09] = [](CPU& cpu) -> int { return cpu.op_ldi_byte(cpu.YH); };
    opcodeHandlers[0x0A] = [](CPU& cpu) -> int { return cpu.op_ld_mem(cpu.YH); };
    opcodeHandlers[0x0B] = [](CPU& cpu) -> int { return cpu.op_ldi_byte(cpu.FR); };
    opcodeHandlers[0x0C] = [](CPU& cpu) -> int { return cpu.op_ld_mem(cpu.FR); };
    opcodeHandlers[0x0D] = [](CPU& cpu) -> int { return cpu.op_ldi_byte(cpu.ZL); };
    opcodeHandlers[0x0E] = [](CPU& cpu) -> int { return cpu.op_ld_mem(cpu.ZL); };
    opcodeHandlers[0x0F] = [](CPU& cpu) -> int { return cpu.op_ldi_byte(cpu.ZH); };
    opcodeHandlers[0x10] = [](CPU& cpu) -> int { return cpu.op_ld_mem(cpu.ZH); };
    opcodeHandlers[0x11] = [](CPU& cpu) -> int { return cpu.op_ldi_word_X(); };
    opcodeHandlers[0x12] = [](CPU& cpu) -> int { return cpu.op_ldi_word_Y(); };
    opcodeHandlers[0x13] = [](CPU& cpu) -> int { return cpu.op_ldi_word_Z(); };
    opcodeHandlers[0x14] = [](CPU& cpu) -> int { return cpu.op_ldi_word_SP(); };
    opcodeHandlers[0x15] = [](CPU& cpu) -> int { return cpu.op_ldx(cpu.AC); };
    opcodeHandlers[0x16] = [](CPU& cpu) -> int { return cpu.op_ldx(cpu.XH); };
    opcodeHandlers[0x17] = [](CPU& cpu) -> int { return cpu.op_ldx(cpu.YL); };
    opcodeHandlers[0x18] = [](CPU& cpu) -> int { return cpu.op_ldx(cpu.YH); };
    opcodeHandlers[0x19] = [](CPU& cpu) -> int { return cpu.op_ldx(cpu.FR); };
    opcodeHandlers[0x1A] = [](CPU& cpu) -> int { return cpu.op_st_mem(cpu.AC); };
    opcodeHandlers[0x1B] = [](CPU& cpu) -> int { return cpu.op_st_mem(cpu.XH); };
    opcodeHandlers[0x1C] = [](CPU& cpu) -> int { return cpu.op_inth(); };
    opcodeHandlers[0x1D] = [](CPU& cpu) -> int { return cpu.op_st_mem(cpu.YL); };
    opcodeHandlers[0x1E] = [](CPU& cpu) -> int { return cpu.op_st_mem(cpu.YH); };
    opcodeHandlers[0x1F] = [](CPU& cpu) -> int { return cpu.op_st_mem(cpu.FR); };
    opcodeHandlers[0x20] = [](CPU& cpu) -> int { return cpu.op_st_mem(cpu.ZL); };
    opcodeHandlers[0x21] = [](CPU& cpu) -> int { return cpu.op_st_mem(cpu.ZH); };
    opcodeHandlers[0x22] = [](CPU& cpu) -> int { return cpu.op_stx(cpu.AC); };
    opcodeHandlers[0x23] = [](CPU& cpu) -> int { return cpu.op_stx(cpu.XH); };
    opcodeHandlers[0x24] = [](CPU& cpu) -> int { return cpu.op_stx(cpu.YL); };
    opcodeHandlers[0x25] = [](CPU& cpu) -> int { return cpu.op_stx(cpu.YH); };
    opcodeHandlers[0x26] = [](CPU& cpu) -> int { return cpu.op_stx(cpu.FR); };
    opcodeHandlers[0x27] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.XH, cpu.AC);
    };
    opcodeHandlers[0x28] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.YL, cpu.AC);
    };
    opcodeHandlers[0x29] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.YH, cpu.AC);
    };
    opcodeHandlers[0x2A] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.FR, cpu.AC);
    };
    opcodeHandlers[0x2B] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.ZL, cpu.AC);
    };
    opcodeHandlers[0x2C] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.ZH, cpu.AC);
    };
    opcodeHandlers[0x2D] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.AC, cpu.XH);
    };
    opcodeHandlers[0x2E] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.YL, cpu.XH);
    };
    opcodeHandlers[0x2F] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.YH, cpu.XH);
    };
    opcodeHandlers[0x30] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.FR, cpu.XH);
    };
    opcodeHandlers[0x31] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.ZL, cpu.XH);
    };
    opcodeHandlers[0x32] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.ZH, cpu.XH);
    };
    opcodeHandlers[0x33] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.AC, cpu.YL);
    };
    opcodeHandlers[0x34] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.XH, cpu.YL);
    };
    opcodeHandlers[0x35] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.YH, cpu.YL);
    };
    opcodeHandlers[0x36] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.FR, cpu.YL);
    };
    opcodeHandlers[0x37] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.ZL, cpu.YL);
    };
    opcodeHandlers[0x38] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.ZH, cpu.YL);
    };
    opcodeHandlers[0x39] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.AC, cpu.YH);
    };
    opcodeHandlers[0x3A] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.XH, cpu.YH);
    };
    opcodeHandlers[0x3B] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.YL, cpu.YH);
    };
    opcodeHandlers[0x3C] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.FR, cpu.YH);
    };
    opcodeHandlers[0x3D] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.ZL, cpu.YH);
    };
    opcodeHandlers[0x3E] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.ZH, cpu.YH);
    };
    opcodeHandlers[0x3F] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.AC, cpu.FR);
    };
    opcodeHandlers[0x40] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.XH, cpu.FR);
    };
    opcodeHandlers[0x41] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.YL, cpu.FR);
    };
    opcodeHandlers[0x42] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.YH, cpu.FR);
    };
    opcodeHandlers[0x43] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.ZL, cpu.FR);
    };
    opcodeHandlers[0x44] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.ZH, cpu.FR);
    };
    opcodeHandlers[0x45] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.AC, cpu.ZL);
    };
    opcodeHandlers[0x46] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.XH, cpu.ZL);
    };
    opcodeHandlers[0x47] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.YL, cpu.ZL);
    };
    opcodeHandlers[0x48] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.YH, cpu.ZL);
    };
    opcodeHandlers[0x49] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.FR, cpu.ZL);
    };
    opcodeHandlers[0x4A] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.ZH, cpu.ZL);
    };
    opcodeHandlers[0x4B] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.AC, cpu.ZH);
    };
    opcodeHandlers[0x4C] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.XH, cpu.ZH);
    };
    opcodeHandlers[0x4D] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.YL, cpu.ZH);
    };
    opcodeHandlers[0x4E] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.YH, cpu.ZH);
    };
    opcodeHandlers[0x4F] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.FR, cpu.ZH);
    };
    opcodeHandlers[0x50] = [](CPU& cpu) -> int {
        return cpu.op_mov_byte(cpu.ZL, cpu.ZH);
    };
    opcodeHandlers[0x51] = [](CPU& cpu) -> int { return cpu.op_mov_sp_z(); };
    opcodeHandlers[0x52] = [](CPU& cpu) -> int { return cpu.op_mov_z_sp(); };
    opcodeHandlers[0x53] = [](CPU& cpu) -> int { return cpu.op_mov_z_pc(); };
    opcodeHandlers[0x54] = [](CPU& cpu) -> int { return cpu.op_push_byte(cpu.AC); };
    opcodeHandlers[0x55] = [](CPU& cpu) -> int { return cpu.op_push_byte(cpu.XH); };
    opcodeHandlers[0x56] = [](CPU& cpu) -> int { return cpu.op_push_byte(cpu.YL); };
    opcodeHandlers[0x57] = [](CPU& cpu) -> int { return cpu.op_push_byte(cpu.YH); };
    opcodeHandlers[0x58] = [](CPU& cpu) -> int { return cpu.op_push_byte(cpu.FR); };
    opcodeHandlers[0x59] = [](CPU& cpu) -> int { return cpu.op_push_byte(cpu.ZL); };
    opcodeHandlers[0x5A] = [](CPU& cpu) -> int { return cpu.op_push_byte(cpu.ZH); };
    opcodeHandlers[0x5B] = [](CPU& cpu) -> int { return cpu.op_push_word(cpu.getX()); };
    opcodeHandlers[0x5C] = [](CPU& cpu) -> int { return cpu.op_push_word(cpu.getY()); };
    opcodeHandlers[0x5D] = [](CPU& cpu) -> int { return cpu.op_push_word(cpu.getZ()); };
    opcodeHandlers[0x5E] = [](CPU& cpu) -> int { return cpu.op_push_word(cpu.PC); };
    opcodeHandlers[0x5F] = [](CPU& cpu) -> int { return cpu.op_pop_byte(cpu.AC); };
    opcodeHandlers[0x60] = [](CPU& cpu) -> int { return cpu.op_pop_byte(cpu.XH); };
    opcodeHandlers[0x61] = [](CPU& cpu) -> int { return cpu.op_pop_byte(cpu.YL); };
    opcodeHandlers[0x62] = [](CPU& cpu) -> int { return cpu.op_pop_byte(cpu.YH); };
    opcodeHandlers[0x63] = [](CPU& cpu) -> int { return cpu.op_pop_byte(cpu.FR); };
    opcodeHandlers[0x64] = [](CPU& cpu) -> int { return cpu.op_pop_byte(cpu.ZL); };
    opcodeHandlers[0x65] = [](CPU& cpu) -> int { return cpu.op_pop_byte(cpu.ZH); };
    opcodeHandlers[0x66] = [](CPU& cpu) -> int { return cpu.op_pop_x(); };
    opcodeHandlers[0x67] = [](CPU& cpu) -> int { return cpu.op_pop_y(); };
    opcodeHandlers[0x68] = [](CPU& cpu) -> int { return cpu.op_pop_z(); };
    opcodeHandlers[0x69] = [](CPU& cpu) -> int {
        return cpu.op_jmp_cond(!cpu.flagZ());
    };
    opcodeHandlers[0x6A] = [](CPU& cpu) -> int {
        return cpu.op_jmpx_cond(!cpu.flagZ());
    };
    opcodeHandlers[0x6B] = [](CPU& cpu) -> int { return cpu.op_jmp_cond(cpu.flagZ()); };
    opcodeHandlers[0x6C] = [](CPU& cpu) -> int {
        return cpu.op_jmpx_cond(cpu.flagZ());
    };
    opcodeHandlers[0x6D] = [](CPU& cpu) -> int {
        return cpu.op_jmp_cond(!cpu.flagC());
    };
    opcodeHandlers[0x6E] = [](CPU& cpu) -> int {
        return cpu.op_jmpx_cond(!cpu.flagC());
    };
    opcodeHandlers[0x6F] = [](CPU& cpu) -> int { return cpu.op_jmp_cond(cpu.flagC()); };
    opcodeHandlers[0x70] = [](CPU& cpu) -> int {
        return cpu.op_jmpx_cond(cpu.flagZ());
    };
    opcodeHandlers[0x71] = [](CPU& cpu) -> int {
        return cpu.op_jmp_cond(!cpu.flagS());
    };
    opcodeHandlers[0x72] = [](CPU& cpu) -> int {
        return cpu.op_jmpx_cond(!cpu.flagS());
    };
    opcodeHandlers[0x73] = [](CPU& cpu) -> int { return cpu.op_jmp_cond(cpu.flagS()); };
    opcodeHandlers[0x74] = [](CPU& cpu) -> int {
        return cpu.op_jmpx_cond(cpu.flagS());
    };
    opcodeHandlers[0x75] = [](CPU& cpu) -> int { return cpu.op_jmp(); };
    opcodeHandlers[0x76] = [](CPU& cpu) -> int { return cpu.op_jmpx(); };
    opcodeHandlers[0x77] = [](CPU& cpu) -> int {
        return cpu.op_call_cond(!cpu.flagZ());
    };
    opcodeHandlers[0x78] = [](CPU& cpu) -> int {
        return cpu.op_call_cond(cpu.flagZ());
    };
    opcodeHandlers[0x79] = [](CPU& cpu) -> int {
        return cpu.op_call_cond(!cpu.flagC());
    };
    opcodeHandlers[0x7A] = [](CPU& cpu) -> int {
        return cpu.op_call_cond(cpu.flagC());
    };
    opcodeHandlers[0x7B] = [](CPU& cpu) -> int {
        return cpu.op_call_cond(!cpu.flagS());
    };
    opcodeHandlers[0x7C] = [](CPU& cpu) -> int {
        return cpu.op_call_cond(cpu.flagS());
    };
    opcodeHandlers[0x7D] = [](CPU& cpu) -> int { return cpu.op_call(); };
    opcodeHandlers[0x7E] = [](CPU& cpu) -> int {
        return cpu.op_ret_cond(!cpu.flagZ());
    };
    opcodeHandlers[0x7F] = [](CPU& cpu) -> int { return cpu.op_ret_cond(cpu.flagZ()); };
    opcodeHandlers[0x80] = [](CPU& cpu) -> int {
        return cpu.op_ret_cond(!cpu.flagC());
    };
    opcodeHandlers[0x81] = [](CPU& cpu) -> int { return cpu.op_ret_cond(cpu.flagC()); };
    opcodeHandlers[0x82] = [](CPU& cpu) -> int {
        return cpu.op_ret_cond(!cpu.flagS());
    };
    opcodeHandlers[0x83] = [](CPU& cpu) -> int { return cpu.op_ret_cond(cpu.flagS()); };
    opcodeHandlers[0x84] = [](CPU& cpu) -> int { return cpu.op_ret(); };
    opcodeHandlers[0x85] = [](CPU& cpu) -> int { return cpu.op_add(cpu.AC); };
    opcodeHandlers[0x86] = [](CPU& cpu) -> int { return cpu.op_add(cpu.XH); };
    opcodeHandlers[0x87] = [](CPU& cpu) -> int { return cpu.op_add(cpu.YL); };
    opcodeHandlers[0x88] = [](CPU& cpu) -> int { return cpu.op_add(cpu.YH); };
    opcodeHandlers[0x89] = [](CPU& cpu) -> int { return cpu.op_add(cpu.ZL); };
    opcodeHandlers[0x8A] = [](CPU& cpu) -> int { return cpu.op_add(cpu.ZH); };
    opcodeHandlers[0x8B] = [](CPU& cpu) -> int { return cpu.op_addi(); };
    opcodeHandlers[0x8C] = [](CPU& cpu) -> int { return cpu.op_sub(cpu.AC); };
    opcodeHandlers[0x8D] = [](CPU& cpu) -> int { return cpu.op_sub(cpu.XH); };
    opcodeHandlers[0x8E] = [](CPU& cpu) -> int { return cpu.op_sub(cpu.YL); };
    opcodeHandlers[0x8F] = [](CPU& cpu) -> int { return cpu.op_sub(cpu.YH); };
    opcodeHandlers[0x90] = [](CPU& cpu) -> int { return cpu.op_sub(cpu.ZL); };
    opcodeHandlers[0x91] = [](CPU& cpu) -> int { return cpu.op_sub(cpu.ZH); };
    opcodeHandlers[0x92] = [](CPU& cpu) -> int { return cpu.op_subi(); };
    opcodeHandlers[0x93] = [](CPU& cpu) -> int { return cpu.op_nand(cpu.AC); };
    opcodeHandlers[0x94] = [](CPU& cpu) -> int { return cpu.op_nand(cpu.XH); };
    opcodeHandlers[0x95] = [](CPU& cpu) -> int { return cpu.op_nand(cpu.YL); };
    opcodeHandlers[0x96] = [](CPU& cpu) -> int { return cpu.op_nand(cpu.YH); };
    opcodeHandlers[0x97] = [](CPU& cpu) -> int { return cpu.op_nand(cpu.ZL); };
    opcodeHandlers[0x98] = [](CPU& cpu) -> int { return cpu.op_nand(cpu.ZH); };
    opcodeHandlers[0x99] = [](CPU& cpu) -> int { return cpu.op_nandi(); };
    opcodeHandlers[0x9A] = [](CPU& cpu) -> int { return cpu.op_xor(cpu.AC); };
    opcodeHandlers[0x9B] = [](CPU& cpu) -> int { return cpu.op_xor(cpu.XH); };
    opcodeHandlers[0x9C] = [](CPU& cpu) -> int { return cpu.op_xor(cpu.YL); };
    opcodeHandlers[0x9D] = [](CPU& cpu) -> int { return cpu.op_xor(cpu.YH); };
    opcodeHandlers[0x9E] = [](CPU& cpu) -> int { return cpu.op_xor(cpu.ZL); };
    opcodeHandlers[0x9F] = [](CPU& cpu) -> int { return cpu.op_xor(cpu.ZH); };
    opcodeHandlers[0xA0] = [](CPU& cpu) -> int { return cpu.op_xori(); };
    opcodeHandlers[0xA1] = [](CPU& cpu) -> int { return cpu.op_nor(cpu.AC); };
    opcodeHandlers[0xA2] = [](CPU& cpu) -> int { return cpu.op_nor(cpu.XH); };
    opcodeHandlers[0xA3] = [](CPU& cpu) -> int { return cpu.op_nor(cpu.YL); };
    opcodeHandlers[0xA4] = [](CPU& cpu) -> int { return cpu.op_nor(cpu.YH); };
    opcodeHandlers[0xA5] = [](CPU& cpu) -> int { return cpu.op_nor(cpu.ZL); };
    opcodeHandlers[0xA6] = [](CPU& cpu) -> int { return cpu.op_nor(cpu.ZH); };
    opcodeHandlers[0xA7] = [](CPU& cpu) -> int { return cpu.op_nori(); };
    opcodeHandlers[0xA8] = [](CPU& cpu) -> int { return cpu.op_adc(cpu.AC); };
    opcodeHandlers[0xA9] = [](CPU& cpu) -> int { return cpu.op_adc(cpu.XH); };
    opcodeHandlers[0xAA] = [](CPU& cpu) -> int { return cpu.op_adc(cpu.YL); };
    opcodeHandlers[0xAB] = [](CPU& cpu) -> int { return cpu.op_adc(cpu.YH); };
    opcodeHandlers[0xAC] = [](CPU& cpu) -> int { return cpu.op_adc(cpu.ZL); };
    opcodeHandlers[0xAD] = [](CPU& cpu) -> int { return cpu.op_adc(cpu.ZH); };
    opcodeHandlers[0xAE] = [](CPU& cpu) -> int { return cpu.op_adci(); };
    opcodeHandlers[0xAF] = [](CPU& cpu) -> int { return cpu.op_sbb(cpu.AC); };
    opcodeHandlers[0xB0] = [](CPU& cpu) -> int { return cpu.op_sbb(cpu.XH); };
    opcodeHandlers[0xB1] = [](CPU& cpu) -> int { return cpu.op_sbb(cpu.YL); };
    opcodeHandlers[0xB2] = [](CPU& cpu) -> int { return cpu.op_sbb(cpu.YH); };
    opcodeHandlers[0xB3] = [](CPU& cpu) -> int { return cpu.op_sbb(cpu.ZL); };
    opcodeHandlers[0xB4] = [](CPU& cpu) -> int { return cpu.op_sbb(cpu.ZH); };
    opcodeHandlers[0xB5] = [](CPU& cpu) -> int { return cpu.op_sbbi(); };
    opcodeHandlers[0xB6] = [](CPU& cpu) -> int { return cpu.op_inc(cpu.AC); };
    opcodeHandlers[0xB7] = [](CPU& cpu) -> int { return cpu.op_inc(cpu.XH); };
    opcodeHandlers[0xB8] = [](CPU& cpu) -> int { return cpu.op_inc(cpu.YL); };
    opcodeHandlers[0xB9] = [](CPU& cpu) -> int { return cpu.op_inc(cpu.YH); };
    opcodeHandlers[0xBA] = [](CPU& cpu) -> int { return cpu.op_inc(cpu.ZL); };
    opcodeHandlers[0xBB] = [](CPU& cpu) -> int { return cpu.op_inc(cpu.ZH); };
    opcodeHandlers[0xBC] = [](CPU& cpu) -> int { return cpu.op_dec(cpu.AC); };
    opcodeHandlers[0xBD] = [](CPU& cpu) -> int { return cpu.op_dec(cpu.XH); };
    opcodeHandlers[0xBE] = [](CPU& cpu) -> int { return cpu.op_dec(cpu.YL); };
    opcodeHandlers[0xBF] = [](CPU& cpu) -> int { return cpu.op_dec(cpu.YH); };
    opcodeHandlers[0xC0] = [](CPU& cpu) -> int { return cpu.op_dec(cpu.ZL); };
    opcodeHandlers[0xC1] = [](CPU& cpu) -> int { return cpu.op_dec(cpu.ZH); };
    opcodeHandlers[0xC2] = [](CPU& cpu) -> int { return cpu.op_icc(cpu.AC); };
    opcodeHandlers[0xC3] = [](CPU& cpu) -> int { return cpu.op_icc(cpu.XH); };
    opcodeHandlers[0xC4] = [](CPU& cpu) -> int { return cpu.op_icc(cpu.YL); };
    opcodeHandlers[0xC5] = [](CPU& cpu) -> int { return cpu.op_icc(cpu.YH); };
    opcodeHandlers[0xC6] = [](CPU& cpu) -> int { return cpu.op_icc(cpu.ZL); };
    opcodeHandlers[0xC7] = [](CPU& cpu) -> int { return cpu.op_icc(cpu.ZH); };
    opcodeHandlers[0xC8] = [](CPU& cpu) -> int { return cpu.op_dcb(cpu.AC); };
    opcodeHandlers[0xC9] = [](CPU& cpu) -> int { return cpu.op_dcb(cpu.XH); };
    opcodeHandlers[0xCA] = [](CPU& cpu) -> int { return cpu.op_dcb(cpu.YL); };
    opcodeHandlers[0xCB] = [](CPU& cpu) -> int { return cpu.op_dcb(cpu.YH); };
    opcodeHandlers[0xCC] = [](CPU& cpu) -> int { return cpu.op_dcb(cpu.ZL); };
    opcodeHandlers[0xCD] = [](CPU& cpu) -> int { return cpu.op_dcb(cpu.ZH); };
    opcodeHandlers[0xCE] = [](CPU& cpu) -> int { return cpu.op_not(cpu.AC); };
    opcodeHandlers[0xCF] = [](CPU& cpu) -> int { return cpu.op_not(cpu.XH); };
    opcodeHandlers[0xD0] = [](CPU& cpu) -> int { return cpu.op_not(cpu.YL); };
    opcodeHandlers[0xD1] = [](CPU& cpu) -> int { return cpu.op_not(cpu.YH); };
    opcodeHandlers[0xD2] = [](CPU& cpu) -> int { return cpu.op_not(cpu.ZL); };
    opcodeHandlers[0xD3] = [](CPU& cpu) -> int { return cpu.op_not(cpu.ZH); };
    opcodeHandlers[0xD4] = [](CPU& cpu) -> int { return cpu.op_cmp(cpu.AC); };
    opcodeHandlers[0xD5] = [](CPU& cpu) -> int { return cpu.op_cmp(cpu.AC); };
    opcodeHandlers[0xD6] = [](CPU& cpu) -> int { return cpu.op_cmp(cpu.XH); };
    opcodeHandlers[0xD7] = [](CPU& cpu) -> int { return cpu.op_cmp(cpu.YL); };
    opcodeHandlers[0xD8] = [](CPU& cpu) -> int { return cpu.op_cmp(cpu.YH); };
    opcodeHandlers[0xD9] = [](CPU& cpu) -> int { return cpu.op_cmp(cpu.ZL); };
    opcodeHandlers[0xDA] = [](CPU& cpu) -> int { return cpu.op_cmpi(); };
    opcodeHandlers[0xDB] = [](CPU& cpu) -> int { return cpu.op_shl(); };
    opcodeHandlers[0xDC] = [](CPU& cpu) -> int { return cpu.op_shr(); };
    opcodeHandlers[0xDD] = [](CPU& cpu) -> int { return cpu.op_hlt(); };
    for (int i = 0xDD + 1; i <= 0xFF; ++i) {
        opcodeHandlers[i] = [i](CPU& cpu) -> int {
            std::cerr << "No instruction with opcode: " << std::hex << i << std::endl;
            return 0;
        };
    }
}
// OPEARTIONS
int CPU::op_inth() {
    // interrupt handling to be made
    return 11;
}

int CPU::op_ldi_byte(uint8_t& reg) {
    uint8_t value = fetchByte();
    reg = value;
    return 6;
}

int CPU::op_ldi_word_X() {
    uint16_t value = fetchWord();
    setX(value);
    return 7;
}

int CPU::op_ldi_word_Y() {
    uint16_t value = fetchWord();
    setY(value);
    return 7;
}

int CPU::op_ldi_word_Z() {
    uint16_t value = fetchWord();
    setZ(value);
    return 7;
}

int CPU::op_ldi_word_SP() {
    uint16_t value = fetchWord();
    SP = value;
    return 7;
}

int CPU::op_ld_mem(uint8_t& reg) {
    uint16_t addr = fetchWord();
    uint8_t value = readByte(addr);
    reg = value;
    return 10;
}

int CPU::op_ldx(uint8_t& reg) {
    uint16_t addr = getZ();
    uint8_t value = readByte(addr);
    reg = addr;
    return 6;
}

int CPU::op_st_mem(uint8_t reg) {
    uint16_t addr = fetchWord();
    writeByte(addr, reg);
    return 10;
}

int CPU::op_stx(uint8_t reg) {
    uint16_t addr = getZ();
    writeByte(addr, reg);
    return 6;
}
int CPU::op_mov_byte(uint8_t& dest, uint8_t src) {
    dest = src;
    return 4;
}
int CPU::op_mov_sp_z() {
    SP = getZ();
    return 5;
}
int CPU::op_mov_z_pc() {
    setZ(PC);
    return 5;
}
int CPU::op_mov_z_sp() {
    setZ(SP);
    return 5;
}
int CPU::op_push_byte(uint8_t value) {
    pushByte(value);
    return 6;
}

int CPU::op_push_word(uint16_t value) {
    pushWord(value);
    return 7;
}

int CPU::op_pop_byte(uint8_t& dest) {
    uint8_t value = popByte();
    dest = value;
    return 7;
}

int CPU::op_pop_x() {
    uint16_t value = popWord();
    setX(value);
    return 8;
}

int CPU::op_pop_y() {
    uint16_t value = popWord();
    setY(value);
    return 8;
}

int CPU::op_pop_z() {
    uint16_t value = popWord();
    setZ(value);
    return 8;
}

int CPU::op_jmp_cond(bool condition) {
    if (condition) {
        uint16_t target = fetchWord();
        PC = target;
        return 9;
    } else {
        return 2;
    }
}

int CPU::op_jmpx_cond(bool condition) {
    if (condition) {
        PC = getZ();
        return 5;
    } else {
        return 2;
    }
}

int CPU::op_jmp() {
    uint16_t addr = fetchWord();
    PC = addr;
    return 9;
}

int CPU::op_jmpx() {
    PC = getZ();
    return 5;
}

// FETCH INSTRUCTION
uint8_t CPU::fetchByte() {
    uint8_t value = readByte(PC);
    PC += 1;
    return value;
}

uint16_t CPU::fetchWord() {
    uint16_t value = readWord(PC);
    PC += 2;
    return value;
}
int CPU::op_call() {
    uint16_t addr = fetchWord();
    pushWord(PC);
    PC = addr;
    return 13;
}
int CPU::op_call_cond(bool condition) {
    if (condition) {
        uint16_t addr = fetchWord();
        pushWord(PC);
        PC = addr;
        return 13;
    } else {
        return 2;
    }
}

int CPU::op_ret() {
    PC = popWord();
    return 8;
}
int CPU::op_ret_cond(bool condition) {
    if (condition) {
        PC = popWord();
        return 8;
    } else {
        return 2;
    }
}
int CPU::op_add(uint8_t value) {
    int result = AC + value;
    bool carryOut = (result > 0xFF);
    setFlags(result, carryOut);
    AC = result & 0xFF;
    return 5;
}
int CPU::op_addi() {
    uint8_t val = fetchByte();
    int result = AC + val;
    bool carryOut = (result > 0xFF);
    setFlags(result, carryOut);
    AC = result & 0xFF;
    return 7;
}

int CPU::op_sub(uint8_t value) {
    int result = AC - value;
    bool carryOut = (result >= 0);
    setFlags(result, carryOut);
    AC = result & 0xFF;
    return 5;
}
int CPU::op_subi() {
    uint8_t val = fetchByte();
    int result = AC - val;
    bool carryOut = (result >= 0);
    setFlags(result, carryOut);
    AC = result & 0xFF;
    return 7;
}
int CPU::op_adc(uint8_t value) {
    int carryIn = flagC() ? 1 : 0;
    int result = AC + value + carryIn;
    bool carryOut = (result > 0xFF);
    setFlags(result, carryOut);
    AC = result & 0xFF;
    return 5;
}

int CPU::op_adci() {
    int carryIn = flagC() ? 1 : 0;
    uint8_t value = fetchByte();
    int result = AC + value + carryIn;
    bool carryOut = (result > 0xFF);
    setFlags(result, carryOut);
    AC = result & 0xFF;
    return 7;
}

int CPU::op_sbb(uint8_t value) {
    int borrowIn = flagC() ? 0 : 1;
    int result = AC - value - borrowIn;
    bool carryOut = (result >= 0);
    setFlags(result, carryOut);
    AC = result & 0xFF;
    return 5;
}
int CPU::op_sbbi() {
    int borrowIn = flagC() ? 0 : 1;
    uint8_t value = fetchByte();
    int result = AC - value - borrowIn;
    bool carryOut = (result >= 0);
    setFlags(result, carryOut);
    AC = result & 0xFF;
    return 5;
}
int CPU::op_inc(uint8_t& reg) {
    int result = reg + 1;
    bool carryOut = (result > 0xFF);
    setFlags(result, carryOut);
    reg = result & 0xFF;
    return 5;
}

int CPU::op_icc(uint8_t& reg) {
    int carryIn = flagC() ? 1 : 0;
    int result = reg + carryIn;
    bool carryOut = (result > 0xFF);
    setFlags(result, carryOut);
    reg = result & 0xFF;
    return 5;
}
int CPU::op_dec(uint8_t& reg) {
    int result = reg - 1;
    bool carryOut = (result >= 0);
    setFlags(result, carryOut);
    reg = result & 0xFF;
    return 5;
}
int CPU::op_dcb(uint8_t& reg) {
    int borrowIn = flagC() ? 0 : 1;
    int result = reg - borrowIn;
    bool carryOut = (result >= 0);
    setFlags(result, carryOut);
    reg = result & 0xFF;
    return 5;
}

int CPU::op_nand(uint8_t value) {
    uint8_t result8 = ~(AC & value);
    AC = result8;
    setFlags(result8, false);
    return 5;
}
int CPU::op_nandi() {
    uint8_t value = fetchByte();
    uint8_t result8 = ~(AC & value);
    AC = result8;
    setFlags(result8, false);
    return 7;
}
int CPU::op_xor(uint8_t value) {
    uint8_t result8 = AC ^ value;
    AC = result8;
    setFlags(result8, false);
    return 5;
}

int CPU::op_xori() {
    uint8_t value = fetchByte();
    uint8_t result8 = AC ^ value;
    AC = result8;
    setFlags(result8, false);
    return 7;
}

int CPU::op_nor(uint8_t value) {
    uint8_t result8 = ~(AC | value);
    AC = result8;
    setFlags(result8, false);
    return 5;
}
int CPU::op_nori() {
    uint8_t value = fetchByte();
    uint8_t result8 = ~(AC | value);
    AC = result8;
    setFlags(result8, false);
    return 7;
}

int CPU::op_not(uint8_t& reg) {
    reg = ~reg;
    setFlags(reg, false);
    return 5;
}

int CPU::op_cmp(uint8_t value) {
    int result = AC - value;
    bool carryOut = (result >= 0);
    setFlags(result, carryOut);
    return 5;
}
int CPU::op_cmpi() {
    uint8_t value = fetchByte();
    int result = AC - value;
    bool carryOut = (result >= 0);
    setFlags(result, carryOut);
    return 7;
}
int CPU::op_shl() {
    AC = AC << 1;
    setFlags(AC, false);
    return 4;
}
int CPU::op_shr() {
    AC = AC >> 1;
    setFlags(AC, false);
    return 4;
}

// EXECUTE INSTRUCTION
int CPU::executeInstruction() {
    if (halted)
        return 0;                 // if CPU is halted, do nothing
    uint8_t opcode = fetchByte(); // fetch next opcode
    curr_inst_opcode = opcode;
    int cycles = opcodeHandlers[opcode](*this);
    cyclesCount += cycles;
    return cycles;
}

// LOAD PROGRAM
void CPU::loadProgramFromVector(const std::vector<uint8_t>& program) {
    size_t size = program.size();
    for (int i = 0; i < size; i++) {
        memory[i] = program[i];
    }
}

void CPU::loadProgramFromFile(const std::string& programPath) {
    std::ifstream file(programPath, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "Error opening file: " << programPath << "\n";
        return;
    }

    uint8_t byte;
    size_t address = 0;

    while (file.read(reinterpret_cast<char*>(&byte), 1)) {
        if (address >= memory.size()) {
            std::cerr << "Program too large for memory!\n";
            break;
        }
        memory[address++] = byte;
    }

    std::cout << "Loaded " << address << " bytes into memory.\n";
}

// RESET
void CPU::reset() {
    AC = XH = YL = YH = ZL = ZH = FR = 0;
    PC = 0;
    SP = 0xFFFF;
    STEP = 0;
    IR = 0;
    cyclesCount = 0;
    halted = false;
    interruptsEnabled = false;
}
// CONSTRUCTOR
CPU::CPU(const std::string& tablePath) {
    memory.fill(0);
    AC = XH = YL = YH = ZL = ZH = FR = 0;
    PC = 0;
    SP = 0xFFFF;
    interruptsEnabled = false;
    halted = false;
    cyclesCount = 0;
    STEP = 0;
    IR = 0;
    loadInstructionTable(tablePath);
    setupOpcodeHandlers();
}


// Helper function to create a more useful memory dump.
// It shows 'lines' of memory (16 bytes per line) starting around 'startAddr'.
std::string CPU::dumpMemory(uint16_t startAddr, int lines) const {
    std::ostringstream oss;
    oss << std::hex << std::uppercase << std::setfill('0');

    // Align start address to a 16-byte boundary for a cleaner look
    uint16_t addr = startAddr & 0xFFF0;
    // Show a bit of context before the target address if possible
    if (startAddr > 16) addr -= 16;

    for (int i = 0; i < lines; ++i) {
        // Print the memory address for the current line
        oss << "0x" << std::setw(4) << addr << ": ";

        std::string ascii_line;
        // Print 16 bytes in hex
        for (int j = 0; j < 16; ++j) {
            uint16_t current_addr = addr + j;
            if (current_addr < memory.size()) { // Basic bounds check
                uint8_t val = memory[current_addr];
                oss << std::setw(2) << static_cast<int>(val) << " ";
            } else {
                oss << "   "; // Pad if we're past the end of memory
            }
        }

        oss << " \n";

        addr += 16;
        if (addr >= memory.size()) break; // Stop if we run out of memory to display
    }
    return oss.str();
}

std::string CPU::getStatusString() const {
    std::ostringstream oss;
    const int content_width = 34;

    auto format_line = [&](const std::string& content) {
        oss << "│ " << std::left << std::setfill(' ') << std::setw(content_width)
            << content << " │\n";
    };

    const std::string h_border = "┌────────────────────────────────────┐";
    const std::string f_border = "└────────────────────────────────────┘";
    const std::string m_border = "├────────────────────────────────────┤";

    // --- Build Header ---
    oss << h_border << "\n";
    oss << "│              CPU STATE             │\n";
    oss << m_border << "\n";

    // --- Build Register Content ---
    // Use temporary string streams to build the content for each line
    std::ostringstream line_content;

    // PC and SP
    line_content << "PC: 0x" << std::hex << std::uppercase << std::setw(4) << std::setfill('0') << PC
                 << "        SP: 0x" << std::setw(4) << SP;
    format_line(line_content.str());
    oss << m_border << "\n";

    // AC, X, Y, Z Registers
    line_content.str(""); line_content.clear(); // Clear the stream for reuse
    line_content << "AC: 0x" << std::hex << std::uppercase << std::setw(2) << std::setfill('0') << static_cast<int>(AC);
    format_line(line_content.str());

    line_content.str(""); line_content.clear();
    line_content << "X:  0x" << std::hex << std::uppercase << std::setw(4) << std::setfill('0') << getX();
    format_line(line_content.str());

    line_content.str(""); line_content.clear();
    line_content << "Y:  0x" << std::hex << std::uppercase << std::setw(4) << std::setfill('0') << getY();
    format_line(line_content.str());

    line_content.str(""); line_content.clear();
    line_content << "Z:  0x" << std::hex << std::uppercase << std::setw(4) << std::setfill('0') << getZ();
    format_line(line_content.str());
    oss << m_border << "\n";

    // Flags Register
    line_content.str(""); line_content.clear();
    line_content << "FR: " << std::bitset<8>(FR) << " [S:" << flagS()
                 << " Z:" << flagZ() << " C:" << flagC() << "]";
    format_line(line_content.str());
    oss << m_border << "\n";

    // Cycle Count
    line_content.str(""); line_content.clear();
    line_content << "Cycles: " << std::dec << cyclesCount;
    format_line(line_content.str());

    // --- Build Footer ---
    oss << f_border << "\n\n";

    oss << "Memory view near PC:\n";
    oss << dumpMemory(PC, 8);

    return oss.str();
}

void CPU::run(uint64_t max_instructions, DebugVerbosity verbosity) {
    // 1. Print the initial state.
    std::cout << "--- CPU Initial State ---\n";
    std::cout << getStatusString() << std::endl;
    std::cout << "--- Starting Execution ---\n";

    // 2. Main execution loop.
    for (uint64_t i = 0; i < max_instructions; ++i) {
        if (halted) {
            std::cout << "\n🛑 CPU Halted!\n";
            break;
        }

        // Capture state *before* execution for the log.
        const uint16_t addr_of_inst = PC;
        const std::string mnemonic = instructionTable[memory[PC]].mnemonic;

        // Execute the instruction.
        executeInstruction();
        // 3. Log output based on verbosity.
        if (verbosity == DebugVerbosity::TRACE) {
            std::cout << std::uppercase << std::hex;

            std::cout << "[0x" << std::setw(4) << std::setfill('0') << addr_of_inst << "] "
                      << std::left << std::setw(10) << std::setfill(' ') << mnemonic
                      << " -> "
                      << "AC:0x" << std::right << std::setw(2) << std::setfill('0') << int(AC) << ", "
                      << "X:0x"  << std::right << std::setw(4) << std::setfill('0') << getX()  << ", "
                      << "Y:0x"  << std::right << std::setw(4) << std::setfill('0') << getY()  << ", "
                      << "SP:0x" << std::right << std::setw(4) << std::setfill('0') << SP      << ", "
                      << "Flags:" << std::bitset<8>(FR)
                      << std::dec << std::endl;

        }
        else if (verbosity == DebugVerbosity::STEP) {
            // Prints the full state box AND waits for user input.
            std::cout << "\n--- After instruction " << std::dec << (i + 1)
                      << ": " << mnemonic << " ---\n";
            std::cout << getStatusString() << std::endl;
            std::cout << "Press Enter to step, or 'q' then Enter to quit..." << std::flush;
            char input = std::cin.get();
            if (input == 'q') {
                std::cin.ignore(10000, '\n');
                break;
            }
        }
    }

    std::cout << "\n--- Execution Finished ---\n";
    std::cout << getStatusString() << std::endl;
}