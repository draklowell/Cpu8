// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#include "Assembler.hpp"
#include "Directives.hpp"
#include "InstrEncoding.hpp"

#include <algorithm>
#include <cctype>
#include <iterator>
#include <stdexcept>
#include <string>
#include <variant>
#include <vector>

namespace asmx {
namespace {
uint32_t& selectLocationCounter(Pass1State& state, SectionType section) {
    switch (section) {
    case SectionType::Text:
        return state.lc_text;
    case SectionType::Data:
        return state.lc_data;
    case SectionType::Bss:
        return state.lc_bss;
    case SectionType::RoData:
        return state.lc_rodata;
    case SectionType::None:
        break;
    }
    throw std::logic_error("Invalid section for location counter");
}

[[nodiscard]] std::string toLowerCopy(const std::string& text) {
    std::string lowered;
    lowered.reserve(text.size());
    std::transform(
        text.begin(), text.end(), std::back_inserter(lowered),
        [](const unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
    return lowered;
}

[[nodiscard]] bool mnemonicExists(const EncodeTable& table, const std::string& m) {
    const auto& entries = table.entries();
    return std::any_of(entries.begin(), entries.end(),
                       [&](const auto& p) { return p.first.mnemonic == m; });
}

void syncScratchCounters(const Pass1State& state, SectionsScratch& scratch) {
    scratch.text.lc = state.lc_text;
    scratch.data.lc = state.lc_data;
    scratch.bss.lc = state.lc_bss;
    scratch.rodata.lc = state.lc_rodata;
}
} // namespace
void Assembler::pass1(const ParseResult& result, Pass1State& state,
                      SectionsScratch& scratch) {
    state.current = SectionType::Text;
    state.lc_text = 0;
    state.lc_data = 0;
    state.lc_bss = 0;
    state.lc_rodata = 0;
    state.symbol_table = SymbolTable{};
    scratch = SectionsScratch{};

    const EncodeTable& encode_table = EncodeTable::get();

    for (const Line& line : result.lines) {
        if (const auto* label = std::get_if<Label>(&line)) {
            Symbol& sym = state.symbol_table.declare(label->name);
            if (sym.defined) {
                throw util::Error(label->loc,
                                  "redefinition of symbol '" + label->name + "'");
            }

            sym.section = state.current;
            sym.value = selectLocationCounter(state, state.current);
            sym.defined = true;
        } else if (const auto* directive = std::get_if<Directive>(&line)) {
            Directives::handlePass1(*directive, state, scratch);
        } else if (const auto* inst = std::get_if<Instruction>(&line)) {
            if (state.current != SectionType::Text) {
                throw util::Error(inst->loc,
                                  "instructions are only allowed in .text section");
            }

            std::vector<OperandType> signature;
            signature.reserve(inst->args.size());
            for (const Argument& arg : inst->args) {
                OperandType operand = arg.operant_type;
                if (operand == OperandType::Label) {
                    operand = OperandType::Imm16;
                    state.symbol_table.declare(arg.label);
                } else if (operand == OperandType::MemAbs16 && !arg.label.empty()) {
                    state.symbol_table.declare(arg.label);
                }
                signature.push_back(operand);
            }

            const std::string mnemonic_lower = toLowerCopy(inst->mnemonic);
            const auto specs = encode_table.find(mnemonic_lower, signature);

            if (!specs) {
                if (!mnemonicExists(encode_table, mnemonic_lower)) {
                    throw util::Error(inst->loc,
                                      "unknown instruction '" + inst->mnemonic + "'");
                }
                throw util::Error(inst->loc, "invalid operands for instruction '" +
                                                 inst->mnemonic + "'");
            }

            state.lc_text += specs->size;
            scratch.text.lc = state.lc_text;
        }
    }

    syncScratchCounters(state, scratch);
}

} // namespace asmx