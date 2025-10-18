#ifndef EMULATOR_C_EMULATOR_HPP
#define EMULATOR_C_EMULATOR_HPP
#include <array>
#include <cstdint>
#include <functional>
#include <string>

struct Instruction {
    uint8_t opcode;
    std::string mnemonic;
    int maxCycles;
    int minCycles;
};

class CPU {
  private:
    std::array<uint8_t, 65536> memory{};
    uint8_t AC, XH, YL, YH, ZL, ZH, FR;
    uint16_t PC, SP;
    uint64_t cyclesCount;
    bool interruptsEnabled;
    bool halted;
    Instruction instructionTable[256];
    std::array<std::function<int(CPU&)>, 256> opcodeHandlers;
    uint8_t STEP;
    uint8_t IR;

    // LOAD INSTRUCTION TABLE
    void loadInstructionTable(const std::string& file);
    // OPCODEHANDLER TABLE
    void setupOpcodeHandlers();

  public:
    // constructor and reset
    explicit CPU(const std::string& tablePath);
    void reset();

    // GETTERS AND SETTERS
    // PC
    uint16_t getPC() const { return PC; }
    void setPC(const uint16_t value) { PC = value; }

    // SP
    uint16_t getSP() const { return SP; }
    void setSP(const uint16_t value) { SP = value; }

    // X(XH | AC)
    uint16_t getX() const { return (static_cast<uint16_t>(XH) << 8) | AC; }
    void setX(const uint16_t value) {
        XH = (value >> 8) & 0xFF;
        AC = value & 0xFF;
    }

    // Y(YH | YL)
    uint16_t getY() const { return (static_cast<uint16_t>(YH) << 8) | YL; }
    void setY(const uint16_t value) {
        YH = (value >> 8) & 0xFF;
        YL = value & 0xFF;
    }

    // Z(ZH | ZL)
    uint16_t getZ() const { return (static_cast<uint16_t>(ZH) << 8) | ZL; }
    void setZ(const uint16_t value) {
        ZH = (value >> 8) & 0xFF;
        ZL = value & 0xFF;
    }

    // Flags
    void setFlags(int result, bool carryFlag);
    bool flagZ() const { return (FR & 0x01) != 0; } // Zero flag (bit0)
    bool flagC() const {
        return (FR & 0x02) == 0;
    } // Carry flag (bit1 inverted: return true if FR bit1 is 0)
    bool flagS() const { return (FR & 0x04) != 0; } // Sign flag (bit2)

    // MEMORY ACCESS
    // read
    uint8_t readByte(const uint16_t addr) const { return memory[addr]; }

    uint16_t readWord(const uint16_t addr) const {
        uint8_t hi = readByte(addr);
        uint8_t lo = readByte(addr + 1);
        return (static_cast<uint16_t>(hi) << 8) | lo;
    }
    // write
    void writeByte(const uint16_t addr, const uint8_t value) { memory[addr] = value; }

    void writeWord(const uint16_t addr, const uint16_t value) {
        uint8_t hi = value >> 8;
        uint8_t lo = value & 0xFF;
        writeByte(addr, hi);
        writeByte(addr + 1, lo);
    }

    // STACK LOGIC
    void pushByte(uint8_t val);
    uint8_t popByte();
    void pushWord(uint16_t val);
    uint16_t popWord();

    // FETCHING INSTRUCTION
    uint8_t fetchByte();
    uint16_t fetchWord();

    // INSTRUCTION EXECUTION
    int executeInstruction();

    // OPERATIONS
    // CONTROL
    int op_nop() { return 3; }
    int op_hlt() {
        halted = true;
        return 1;
    }
    int op_inte() {
        interruptsEnabled = true;
        return 4;
    };
    int op_intd() {
        interruptsEnabled = false;
        return 4;
    }
    int op_inth();
    // LOAD
    int op_ldi_byte(uint8_t& reg);
    int op_ldi_word_SP();
    int op_ldi_word_X();
    int op_ldi_word_Y();
    int op_ldi_word_Z();
    int op_ld_mem(uint8_t& reg);
    int op_ldx(uint8_t& reg);
    // STORE
    int op_st_mem(uint8_t reg);
    int op_stx(uint8_t reg);
    // MOVE
    int op_mov_byte(uint8_t& dest, uint8_t src);
    int op_mov_sp_z();
    int op_mov_z_sp();
    int op_mov_z_pc();
    // STACK
    int op_push_byte(uint8_t value);
    int op_push_word(uint16_t value);
    int op_pop_byte(uint8_t& dest);
    int op_pop_x();
    int op_pop_y();
    int op_pop_z();
    // JUMP AND CALL
    int op_jmp_cond(bool condition);
    int op_jmpx_cond(bool condition);
    int op_jmp();
    int op_jmpx();

    int op_call();
    int op_call_cond(bool condition);
    int op_ret();
    int op_ret_cond(bool condition);

    // ARITHMETIC AND LOGIC
    // arithmetic
    int op_add(uint8_t value);
    int op_addi();
    int op_adc(uint8_t value);
    int op_adci();
    int op_sub(uint8_t value);
    int op_subi();
    int op_sbb(uint8_t value);
    int op_sbbi();
    int op_inc(uint8_t& reg);
    int op_dec(uint8_t& reg);
    int op_icc(uint8_t& reg);
    int op_dcb(uint8_t& reg);
    // logical
    int op_nand(uint8_t value);
    int op_nandi();
    int op_xor(uint8_t value);
    int op_xori();
    int op_nor(uint8_t value);
    int op_nori();
    int op_not(uint8_t& reg);
    int op_cmp(uint8_t value);
    int op_cmpi();

    // SHIFTS
    int op_shl();
    int op_shr();
    void loadProgramFromVector(const std::vector<uint8_t>& program);

    void loadProgramFromFile(const std::string& programPath);

    std::string getStatusString() const;

    void run(uint64_t halt_after = -1);
    void clear_memory() { memory.fill(0); };
};
#endif // EMULATOR_C_EMULATOR_HPP