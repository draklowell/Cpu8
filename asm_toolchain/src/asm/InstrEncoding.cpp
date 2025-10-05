// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#include <utility>
#include "InstrEncoding.hpp"

using OT = asmx::OperandType;
using asmx::Reg;

namespace
{
    std::vector<OT> Sig(std::initializer_list<OT> v)
    {
        return {v};
    }
}

namespace asmx
{
    const EncodeTable &EncodeTable::get()
    {
        static EncodeTable instance;
        return instance;
    }

    EncodeTable::EncodeTable()
    {
        auto add_simple = [&](const char *mnemonic, std::vector<OT> signature, const uint8_t opcode, const uint8_t size, const bool reloc = false, const uint8_t imm_offset = 1)
        {
            Key key{std::string(mnemonic), signature};
            table.try_emplace(std::move(key), OpcodeSpecs{opcode, size, signature, reloc, imm_offset});
        };

        auto add_mov = [&](Reg dst, Reg src, const uint8_t opcode)
        {
            mov_[static_cast<int>(dst)][static_cast<int>(src)] = opcode;
        };

        auto add_ldi8 = [&](Reg r, uint8_t opcode)
        {
            ldi8_[static_cast<int>(r)] = opcode;
            add_simple("ldi", Sig({OT::Reg, OT::Imm8}), opcode, 2, false, 1);
        };

        auto add_ldi16 = [&](Reg r, const uint8_t opcode)
        {
            ldi16_[static_cast<int>(r)] = opcode;
            add_simple("ldi", Sig({OT::Imm16}), opcode, 3, false, 1);
        };

        auto add_ldabs16 = [&](Reg r, const uint8_t opcode)
        {
            ld16_[static_cast<int>(r)] = opcode;
            add_simple("ld", Sig({OT::Reg, OT::MemAbs16}), opcode, 3, false, 1);
        };

        auto add_stabs16 = [&](Reg r, const uint8_t opcode)
        {
            st16_[static_cast<int>(r)] = opcode;
            add_simple("st", Sig({OT::MemAbs16, OT::Reg}), opcode, 3, false, 1);
        };

#define ADD_SIMPLE(mnem, sig_vec, opc, sz) add_simple(mnem, sig_vec, opc, sz)
#define ADD_MOV(dst, src, opc) add_mov(dst, src, opc)
#define ADD_LDI8(r, opc) add_ldi8(r, opc)
#define ADD_LDI16(r, opc) add_ldi16(r, opc)
#define ADD_LDABS16(r, opc) add_ldabs16(r, opc)
#define ADD_STABS16(r, opc) add_stabs16(r, opc)

#include "EncodeTable.inc.hpp"

#undef ADD_SIMPLE
#undef ADD_MOV
#undef ADD_LDI8
#undef ADD_LDI16
#undef ADD_LDABS16
#undef ADD_STABS16
    }
    std::optional<OpcodeSpecs> EncodeTable::find(const std::string &mnem,
                                                 const std::vector<OperandType> &sig) const
    {
        const Key k{mnem, sig};
        const auto it = table.find(k);
        if (it == table.end())
            return std::nullopt;
        return it->second;
    }

    uint8_t EncodeTable::movOpcode(Reg dst, Reg src) const { return mov_[static_cast<int>(dst)][static_cast<int>(src)]; }
    uint8_t EncodeTable::ldiImm8Opcode(Reg r) const { return ldi8_[static_cast<int>(r)]; }
    uint8_t EncodeTable::ldiImm16Opcode(Reg r) const { return ldi16_[static_cast<int>(r)]; }
    uint8_t EncodeTable::ldAbs16Opcode(Reg r) const { return ld16_[static_cast<int>(r)]; }
    uint8_t EncodeTable::stAbs16Opcode(Reg r) const { return st16_[static_cast<int>(r)]; }
    const std::unordered_map<Key, OpcodeSpecs, KeyHash> &EncodeTable::entries() const { return table; }
}
