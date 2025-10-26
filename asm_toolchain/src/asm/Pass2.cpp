// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#include "Assembler.hpp"
#include "Directives.hpp"
#include "InstrEncoding.hpp"
#include "RegisterDependent.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <variant>
#include <vector>

namespace asmx {
namespace {
[[nodiscard]] bool sameLocation(const util::SourceLoc& lhs,
                                const util::SourceLoc& rhs) {
    return lhs.file == rhs.file && lhs.pos.line == rhs.pos.line &&
           lhs.pos.col == rhs.pos.col;
}

[[nodiscard]] std::string toLowerCopy(const std::string& text) {
    std::string lowered;
    lowered.reserve(text.size());
    std::transform(
        text.begin(), text.end(), std::back_inserter(lowered),
        [](unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
    return lowered;
}

[[nodiscard]] std::string normaliseDirectiveName(const std::string& raw) {
    std::string lowered;
    lowered.reserve(raw.size());
    for (char ch : raw) {
        lowered.push_back(
            static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));
    }
    if (!lowered.empty() && lowered.front() == '.') {
        lowered.erase(lowered.begin());
    }
    return lowered;
}
constexpr uint16_t kRamBaseAddress = 0x4000;

[[nodiscard]] uint32_t sectionBaseAddress(const Pass1State& st, SectionType section) {
    switch (section) {
    case SectionType::Text:
        return 0u;
    case SectionType::RoData:
        return st.lc_text;
    case SectionType::Data:
        return st.lc_text + st.lc_rodata;
    case SectionType::Bss:
        return kRamBaseAddress;
    case SectionType::None:
        break;
    }
    return 0u;
}

[[nodiscard]] SymbolResolution resolveSymbolReference(const Pass1State& st,
                                                      const SymbolTable& symtab,
                                                      const std::string& name,
                                                      const util::SourceLoc& loc) {
    const auto sym_opt = symtab.fnd(name);
    if (!sym_opt) {
        throw util::Error(loc, "undefined symbol '" + name + "'");
    }

    const Symbol& sym = *sym_opt;
    if (!sym.defined) {
        if (sym.bind == SymbolBinding::Local) {
            throw util::Error(loc, "undefined symbol '" + name + "'");
        }
        return SymbolResolution{0u, true};
    }

    const uint32_t base = sectionBaseAddress(st, sym.section);
    const uint64_t absolute = base + static_cast<uint64_t>(sym.value);
    if (absolute > 0xFFFFu) {
        throw util::Error(loc,
                          "address for symbol '" + name + "' exceeds 16-bit range");
    }
    const bool relocatable =
    sym.section == SectionType::Text || sym.section == SectionType::RoData ||
    sym.section == SectionType::Data || sym.section == SectionType::Bss;

    return SymbolResolution{static_cast<uint16_t>(absolute & 0xFFFFu), relocatable};
}

void emitDataItemIntoText(const Pass1State& st, const DataItem& item,
                          const SymbolTable& symtab, std::vector<uint8_t>& text_bytes,
                          std::vector<PendingTextReloc>& relocations) {
    switch (item.kind) {
    case DataItem::Kind::Byte:
    case DataItem::Kind::Ascii:
    case DataItem::Kind::Asciz:
        text_bytes.insert(text_bytes.end(), item.bytes.begin(), item.bytes.end());
        break;
    case DataItem::Kind::Word: {
        for (const auto& word_entry : item.words) {
            const auto value_offset = static_cast<uint32_t>(text_bytes.size());
            uint16_t value = 0;
            bool needs_reloc = false;
            if (std::holds_alternative<uint16_t>(word_entry)) {
                value = std::get<uint16_t>(word_entry);
            } else {
                const auto& symbol_name = std::get<std::string>(word_entry);
                const auto resolved =
                    resolveSymbolReference(st, symtab, symbol_name, item.loc);
                value = resolved.value;
                needs_reloc = resolved.needs_reloc;
                if (needs_reloc) {
                    relocations.push_back(
                        PendingTextReloc{value_offset, symbol_name, item.loc});
                }
            }
            text_bytes.push_back(static_cast<uint8_t>((value >> 8U) & 0xFFU));
            text_bytes.push_back(static_cast<uint8_t>(value & 0xFFU));
        }
        break;
    }
    default:
        break;
    }
}

const DataItem* matchTextItem(const SectionsScratch& scratch, std::size_t& index,
                              const util::SourceLoc& loc) {
    if (index >= scratch.text.items.size()) {
        return nullptr;
    }
    const DataItem& candidate = scratch.text.items[index];
    if (!sameLocation(candidate.loc, loc)) {
        return nullptr;
    }
    ++index;
    return &candidate;
}
std::vector<OperandType> buildSignature(const Instruction& instruction) {
    std::vector<OperandType> signature;
    signature.reserve(instruction.args.size());
    for (const auto& a : instruction.args) {
        auto type = a.operant_type;
        if (type == OperandType::Label) {
            type = OperandType::Imm16;
        }
        signature.push_back(type);
    }
    return signature;
}
uint8_t pickOpcode(const EncodeTable& table, const Instruction& instruction) {
    const std::string mnem = toLowerCopy(instruction.mnemonic);
    const auto signature = buildSignature(instruction);

    if (isRegisterDependentMnemonic(mnem, signature)) {
        if (mnem == "mov") {
            const Reg dst = instruction.args[0].reg;
            const Reg src = instruction.args[1].reg;
            return table.movOpcode(dst, src);
        }
        if (mnem == "ldi") {
            const Reg r = instruction.args[0].reg;
            if (signature[1] == OperandType::Imm8) {
                return table.ldiImm8Opcode(r);
            }
            return table.ldiImm16Opcode(r);
        }
        if (mnem == "ld") {
            const Reg r = instruction.args[0].reg;
            return table.ldAbs16Opcode(r);
        }
        if (mnem == "st") {
            const Reg reg = instruction.args[1].reg;
            return table.stAbs16Opcode(reg);
        }
        throw util::Error(instruction.loc, "Undefined register dependent mnemonic");
    }
    const auto specs = table.find(mnem, signature);
    if (!specs) {
        throw util::Error(instruction.loc, "invalid operands for instruction '" +
                                               instruction.mnemonic + "'");
    }
    return specs->opcode;
}
} // namespace

void Assembler::pass2(const ParseResult& pr, const Pass1State& st,
                      const SectionsScratch& scratch, obj::ObjectFile& out) {
    const EncodeTable& table = EncodeTable::get();

    std::vector<uint8_t> text_bytes;
    text_bytes.reserve(st.lc_text);
    std::vector<PendingTextReloc> pending_text_relocs;

    SectionType current_section = SectionType::Text;
    std::size_t text_item_index = 0;

    for (const Line& line : pr.lines) {
        if (std::holds_alternative<Label>(line)) {
            continue;
        }

        if (const auto* directive = std::get_if<Directive>(&line)) {
            const std::string normalized = normaliseDirectiveName(directive->name);
            if (normalized == "text" || normalized == "code") {
                current_section = SectionType::Text;
            } else if (normalized == "data") {
                current_section = SectionType::Data;
            } else if (normalized == "bss") {
                current_section = SectionType::Bss;
            } else if (normalized == "rodata") {
                current_section = SectionType::RoData;
            }

            if (current_section == SectionType::Text) {
                if (const DataItem* item =
                        matchTextItem(scratch, text_item_index, directive->loc)) {
                    emitDataItemIntoText(st, *item, st.symbol_table, text_bytes,
                                         pending_text_relocs);
                }
            }
            continue;
        }

        const auto* inst = std::get_if<Instruction>(&line);
        if (inst == nullptr) {
            continue;
        }

        if (current_section != SectionType::Text) {
            continue;
        }

        const std::string mnemonic_lower = toLowerCopy(inst->mnemonic);
        const bool implicit_candidate = isImplicitRegMnemonic(mnemonic_lower);
        const auto compound = makeImplicitRegKey(mnemonic_lower, *inst);
        if (compound) {
            const auto specs = table.find(*compound, std::vector<OperandType>{});
            if (!specs) {
                throw util::Error(inst->loc,
                                  "unknown instruction variant '" + *compound + "'");
            }

            const std::size_t inst_start = text_bytes.size();
            text_bytes.push_back(specs->opcode);
            const std::size_t emitted = text_bytes.size() - inst_start;
            if (emitted != specs->size) {
                throw std::logic_error("instruction size mismatch during pass2");
            }
            continue;
        }

        if (implicit_candidate) {
            throw util::Error(inst->loc, "invalid operands for instruction '" +
                                             inst->mnemonic +
                                             "' — expected exactly one register");
        }

        std::vector<OperandType> signature;
        signature.reserve(inst->args.size());
        for (const Argument& arg : inst->args) {
            OperandType operand = arg.operant_type;
            if (operand == OperandType::Label) {
                operand = OperandType::Imm16;
            }
            signature.push_back(operand);
        }

        auto specs = table.find(mnemonic_lower, signature);
        uint8_t size = 0;
        if (specs) {
            size = specs->size;
        } else if (auto s = inferRegisterDependentSize(mnemonic_lower, signature)) {
            size = *s;
        } else {
            throw util::Error(inst->loc, "invalid operands for instruction '" +
                                             inst->mnemonic + "'");
        }

        const std::size_t inst_start = text_bytes.size();
        const uint8_t opcode = pickOpcode(table, *inst);
        text_bytes.push_back(opcode);

        for (const Argument& arg : inst->args) {
            switch (arg.operant_type) {
            case OperandType::Reg:
                break;
            case OperandType::Imm8:
                text_bytes.push_back(static_cast<uint8_t>(arg.value & 0xFFU));
                break;
            case OperandType::Imm16: {
                text_bytes.push_back(static_cast<uint8_t>((arg.value >> 8U) & 0xFFU));
                text_bytes.push_back(static_cast<uint8_t>(arg.value & 0xFFU));
                break;
            }
            case OperandType::Label: {
                const auto reloc_offset = static_cast<uint32_t>(text_bytes.size());
                const auto resolved =
                    resolveSymbolReference(st, st.symbol_table, arg.label, inst->loc);
                if (resolved.needs_reloc) {
                    pending_text_relocs.push_back(
                        PendingTextReloc{reloc_offset, arg.label, inst->loc});
                }
                text_bytes.push_back(
                    static_cast<uint8_t>((resolved.value >> 8U) & 0xFFU));
                text_bytes.push_back(static_cast<uint8_t>(resolved.value & 0xFFU));
                break;
            }
            case OperandType::MemAbs16: {
                const auto reloc_offset = static_cast<uint32_t>(text_bytes.size());
                if (!arg.label.empty()) {
                    const auto resolved = resolveSymbolReference(st, st.symbol_table,
                                                                 arg.label, inst->loc);
                    if (resolved.needs_reloc) {
                        pending_text_relocs.push_back(
                            PendingTextReloc{reloc_offset, arg.label, inst->loc});
                    }
                    text_bytes.push_back(
                        static_cast<uint8_t>((resolved.value >> 8U) & 0xFFU));
                    text_bytes.push_back(static_cast<uint8_t>(resolved.value & 0xFFU));
                } else {
                    text_bytes.push_back(
                        static_cast<uint8_t>((arg.value >> 8U) & 0xFFU));
                    text_bytes.push_back(static_cast<uint8_t>(arg.value & 0xFFU));
                }
                break;
            }
            case OperandType::None:
                break;
            default:
                break;
            }
        }

        const std::size_t emitted = text_bytes.size() - inst_start;
        if (emitted != size) {
            throw std::logic_error("instruction size mismatch during pass2");
        }
    }

    if (text_item_index != scratch.text.items.size()) {
        throw std::logic_error("text directive bookkeeping mismatch in pass2");
    }

    if (text_bytes.size() != st.lc_text) {
        throw std::logic_error("text section size mismatch after pass2 emission");
    }

    Directives::emitPass2(scratch, st.symbol_table, out);

    auto& text_section = out.sections[0];
    text_section.data = text_bytes;

    std::vector<obj::RelocEntry> retained_relocs;
    retained_relocs.reserve(out.reloc_entries.size());
    for (const obj::RelocEntry& entry : out.reloc_entries) {
        if (entry.section_index != 0) {
            retained_relocs.push_back(entry);
        }
    }
    out.reloc_entries.swap(retained_relocs);

    std::unordered_map<std::string, uint16_t> symbol_indices;
    symbol_indices.reserve(out.symbols.size());
    for (std::size_t i = 0; i < out.symbols.size(); ++i) {
        symbol_indices.emplace(out.symbols[i].name, static_cast<uint16_t>(i));
    }

    for (const PendingTextReloc& reloc : pending_text_relocs) {
        const auto it = symbol_indices.find(reloc.symbol);
        if (it == symbol_indices.end()) {
            throw util::Error(reloc.loc,
                              "undefined symbol '" + reloc.symbol + "' in relocation");
        }

        if (reloc.offset > 0xFFFFu) {
            throw std::logic_error("text relocation offset exceeds 16 bits");
        }

        obj::RelocEntry entry{};
        entry.section_index = 0;
        entry.type = obj::RelocType::ABS16;
        entry.offset = static_cast<uint16_t>(reloc.offset);
        entry.symbol_index = it->second;
        entry.addend = 0;
        out.reloc_entries.push_back(entry);
    }
}
} // namespace asmx
