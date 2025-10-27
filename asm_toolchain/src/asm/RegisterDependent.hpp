// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#pragma once

#include "InstrEncoding.hpp"
#include "Parser.hpp"

#include <optional>
#include <string>
#include <string_view>
#include <unordered_set>
#include <vector>

namespace asmx {
namespace detail {
inline bool isMovRegReg(const std::string& mnemonic_lower,
                        const std::vector<OperandType>& signature) {
    return mnemonic_lower == "mov" && signature.size() == 2 &&
           signature[0] == OperandType::Reg && signature[1] == OperandType::Reg;
}

inline bool isLdiRegImm8(const std::string& mnemonic_lower,
                         const std::vector<OperandType>& signature) {
    return mnemonic_lower == "ldi" && signature.size() == 2 &&
           signature[0] == OperandType::Reg && signature[1] == OperandType::Imm8;
}

inline bool isLdiRegImm16(const std::string& mnemonic_lower,
                          const std::vector<OperandType>& signature) {
    return mnemonic_lower == "ldi" && signature.size() == 2 &&
           signature[0] == OperandType::Reg && signature[1] == OperandType::Imm16;
}

inline bool isLdRegMemAbs16(const std::string& mnemonic_lower,
                            const std::vector<OperandType>& signature) {
    return mnemonic_lower == "ld" && signature.size() == 2 &&
           signature[0] == OperandType::Reg && signature[1] == OperandType::MemAbs16;
}

inline bool isStMemAbs16Reg(const std::string& mnemonic_lower,
                            const std::vector<OperandType>& signature) {
    return mnemonic_lower == "st" && signature.size() == 2 &&
           signature[0] == OperandType::MemAbs16 && signature[1] == OperandType::Reg;
}
} // namespace detail

inline bool isRegisterDependentMnemonic(const std::string& mnemonic_lower,
                                        const std::vector<OperandType>& signature) {
    using namespace detail;
    return isMovRegReg(mnemonic_lower, signature) ||
           isLdiRegImm8(mnemonic_lower, signature) ||
           isLdiRegImm16(mnemonic_lower, signature) ||
           isLdRegMemAbs16(mnemonic_lower, signature) ||
           isStMemAbs16Reg(mnemonic_lower, signature);
}

inline std::string regToTokenLower(Reg r) {
    switch (r) {
    case Reg::AC:
        return "ac";
    case Reg::XH:
        return "xh";
    case Reg::YL:
        return "yl";
    case Reg::YH:
        return "yh";
    case Reg::FR:
        return "fr";
    case Reg::ZL:
        return "zl";
    case Reg::ZH:
        return "zh";
    case Reg::SP:
        return "sp";
    case Reg::PC:
        return "pc";
    case Reg::X:
        return "x";
    case Reg::Y:
        return "y";
    case Reg::Z:
        return "z";
    case Reg::Invalid:
        break;
    }
    return "";
}

inline bool isImplicitRegMnemonic(std::string_view mnemonic_lower) {
    static const std::unordered_set<std::string_view> mnemonics = {
        "push", "pop", "add", "sub", "nand", "xor", "nor", "adc", "sbb",
        "inc",  "dec", "icc", "dcb", "not",  "cmp", "ldx", "stx"};
    return mnemonics.count(mnemonic_lower) != 0;
}

inline std::optional<std::string> makeImplicitRegKey(std::string_view mnemonic_lower,
                                                     const Instruction& inst) {
    if (!isImplicitRegMnemonic(mnemonic_lower)) {
        return std::nullopt;
    }
    if (inst.args.size() != 1 || inst.args[0].operant_type != OperandType::Reg) {
        return std::nullopt;
    }

    const std::string reg_token = regToTokenLower(inst.args[0].reg);
    if (reg_token.empty()) {
        return std::nullopt;
    }

    std::string compound;
    compound.reserve(mnemonic_lower.size() + 1 + reg_token.size());
    compound.append(mnemonic_lower.data(), mnemonic_lower.size());
    compound.push_back('-');
    compound.append(reg_token);
    return compound;
}

inline std::optional<uint8_t>
inferRegisterDependentSize(const std::string& mnemonic_lower,
                           const std::vector<OperandType>& signature) {
    using namespace detail;
    if (isMovRegReg(mnemonic_lower, signature)) {
        return 1;
    }
    if (isLdiRegImm8(mnemonic_lower, signature)) {
        return 2;
    }
    if (isLdiRegImm16(mnemonic_lower, signature) ||
        isLdRegMemAbs16(mnemonic_lower, signature) ||
        isStMemAbs16Reg(mnemonic_lower, signature)) {
        return 3;
    }
    return std::nullopt;
}
} // namespace asmx
