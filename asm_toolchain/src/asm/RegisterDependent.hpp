// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#pragma once

#include "InstrEncoding.hpp"

#include <optional>
#include <string>
#include <vector>

namespace asmx {
namespace detail {
inline bool isMovRegReg(const std::string& mnemonic_lower,
                        const std::vector<OperandType>& signature) {
    return mnemonic_lower == "mov" && signature.size() == 2 &&
           signature[0] == OperandType::Reg &&
           signature[1] == OperandType::Reg;
}

inline bool isLdiRegImm8(const std::string& mnemonic_lower,
                         const std::vector<OperandType>& signature) {
    return mnemonic_lower == "ldi" && signature.size() == 2 &&
           signature[0] == OperandType::Reg &&
           signature[1] == OperandType::Imm8;
}

inline bool isLdiRegImm16(const std::string& mnemonic_lower,
                          const std::vector<OperandType>& signature) {
    return mnemonic_lower == "ldi" && signature.size() == 2 &&
           signature[0] == OperandType::Reg &&
           signature[1] == OperandType::Imm16;
}

inline bool isLdRegMemAbs16(const std::string& mnemonic_lower,
                            const std::vector<OperandType>& signature) {
    return mnemonic_lower == "ld" && signature.size() == 2 &&
           signature[0] == OperandType::Reg &&
           signature[1] == OperandType::MemAbs16;
}

inline bool isStMemAbs16Reg(const std::string& mnemonic_lower,
                            const std::vector<OperandType>& signature) {
    return mnemonic_lower == "st" && signature.size() == 2 &&
           signature[0] == OperandType::MemAbs16 &&
           signature[1] == OperandType::Reg;
}
} // namespace detail

inline bool isRegisterDependentMnemonic(
    const std::string& mnemonic_lower,
    const std::vector<OperandType>& signature) {
    using namespace detail;
    return isMovRegReg(mnemonic_lower, signature) ||
           isLdiRegImm8(mnemonic_lower, signature) ||
           isLdiRegImm16(mnemonic_lower, signature) ||
           isLdRegMemAbs16(mnemonic_lower, signature) ||
           isStMemAbs16Reg(mnemonic_lower, signature);
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
