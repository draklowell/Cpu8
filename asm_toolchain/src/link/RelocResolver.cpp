// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#include "RelocResolver.hpp"

#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>
#include <sstream>
#include <unordered_map>
#include <vector>

namespace {

const obj::SectionDescription* getSection(const obj::ObjectFile& object, std::size_t index) {
    if (index < object.sections.size()) {
        return &object.sections[index];
    }
    return nullptr;
}

std::string sectionNameFromIndex(int32_t index) {
    switch (index) {
    case 0:
        return ".text";
    case 1:
        return ".data";
    case 2:
        return ".bss";
    case 3:
        return ".rodata";
    default:
        return "<invalid>";
    }
}

std::string toUpperHex(uint32_t value) {
    std::ostringstream oss;
    oss << std::hex << std::uppercase << value;
    return oss.str();
}

uint32_t sectionLogicalSize(const obj::ObjectFile& object, int32_t index) {
    const auto* section = getSection(object, static_cast<std::size_t>(index));
    if (section == nullptr) {
        return 0;
    }
    if (index == 2) {
        return section->bss_size;
    }
    return static_cast<uint32_t>(section->data.size());
}

link::ResolvedSym resolveDefinedSymbol(const obj::ObjectFile& object,
                                       std::size_t object_index,
                                       const obj::SymbolDescription& symbol,
                                       const link::MergePlan& plan) {
    if (symbol.section_index < 0) {
        return link::ResolvedSym{-1, 0, symbol.bind};
    }

    const uint32_t value = symbol.value;
    if (const uint32_t logical_size = sectionLogicalSize(object, symbol.section_index); value > logical_size) {
        throw std::runtime_error("Symbol '" + symbol.name + "' offset 0x" + toUpperHex(value) +
                                 " exceeds section " +
                                 sectionNameFromIndex(symbol.section_index) + " size 0x" +
                                 toUpperHex(logical_size));
    }

    uint64_t base = 0;
    switch (symbol.section_index) {
    case 0: {
        base = static_cast<uint64_t>(plan.layout.text_base) + plan.text_offsets[object_index];
        break;
    }
    case 2: {
        base = static_cast<uint64_t>(plan.layout.bss_base) + plan.bss_offsets[object_index];
        break;
    }
    case 3: {
        base = static_cast<uint64_t>(plan.layout.rodata_base) + plan.rodata_offsets[object_index];
        break;
    }
    case 1:
        throw std::runtime_error("Initialized .data section is not supported for symbol '" +
                                 symbol.name + "'");
    default:
        throw std::runtime_error("Symbol '" + symbol.name + "' located in unsupported section");
    }

    const uint64_t absolute = base + value;
    if (absolute > std::numeric_limits<uint32_t>::max()) {
        throw std::runtime_error("Symbol '" + symbol.name + "' address overflow");
    }

    return link::ResolvedSym{symbol.section_index, static_cast<uint32_t>(absolute), symbol.bind};
}

link::ResolvedSym resolveSymbolForReloc(const obj::ObjectFile& object,
                                        std::size_t object_index,
                                        const obj::SymbolDescription& symbol,
                                        const link::MergePlan& plan,
                                        const std::unordered_map<std::string, link::ResolvedSym>& gsym) {
    if (symbol.section_index >= 0) {
        return resolveDefinedSymbol(object, object_index, symbol, plan);
    }

    const auto it = gsym.find(symbol.name);
    if (it == gsym.end() || it->second.section_index < 0) {
        throw std::runtime_error("Undefined symbol '" + symbol.name + "' referenced in relocation");
    }
    return it->second;
}

} // namespace

namespace link {

std::unordered_map<std::string, ResolvedSym>
RelocResolver::buildGlobalSymtab(const std::vector<obj::ObjectFile>& objects,
                                 const MergePlan& plan) {
    std::unordered_map<std::string, ResolvedSym> table;

    for (std::size_t obj_index = 0; obj_index < objects.size(); ++obj_index) {
        const auto& object = objects[obj_index];
        for (const auto& symbol : object.symbols) {
            if (symbol.section_index >= 0) {
                const auto resolved = resolveDefinedSymbol(object, obj_index, symbol, plan);

                if (symbol.bind == 0) {
                    continue; // local definition
                }

                auto it = table.find(symbol.name);
                if (it != table.end()) {
                    if (it->second.section_index >= 0) {
                        throw std::runtime_error("Multiple definition of symbol '" + symbol.name + "'");
                    }
                    it->second = resolved;
                } else {
                    table.emplace(symbol.name, resolved);
                }
            } else if (symbol.bind != 0) {
                auto [it, inserted] = table.emplace(symbol.name, ResolvedSym{-1, 0, symbol.bind});
                if (!inserted && it->second.section_index >= 0) {
                    // definition already recorded; keep it
                }
            }
        }
    }

    for (const auto& [name, sym] : table) {
        if (sym.section_index < 0) {
            throw std::runtime_error("Undefined symbol '" + name + "'");
        }
    }

    return table;
}

void RelocResolver::apply(const std::vector<obj::ObjectFile>& objects,
                          const MergePlan& plan,
                          const std::unordered_map<std::string, ResolvedSym>& gsym,
                          std::vector<uint8_t>& text,
                          std::vector<uint8_t>& rodata) {
    for (std::size_t obj_index = 0; obj_index < objects.size(); ++obj_index) {
        const auto& object = objects[obj_index];

        for (const auto& reloc : object.reloc_entries) {
            if (reloc.symbol_index >= object.symbols.size()) {
                throw std::runtime_error("Relocation references invalid symbol index");
            }

            const auto& symbol = object.symbols[reloc.symbol_index];
            const auto section_index = reloc.section_index;
            if (section_index != 0 && section_index != 3) {
                throw std::runtime_error("Relocation for symbol '" + symbol.name +
                                         "' uses unsupported section index " +
                                         std::to_string(section_index));
            }

            const auto resolved = resolveSymbolForReloc(object, obj_index, symbol, plan, gsym);

            if (reloc.type != obj::RelocType::ABS16) {
                throw std::runtime_error("Unsupported relocation type for symbol '" + symbol.name + "'");
            }

            std::vector<uint8_t>* target = nullptr;
            std::size_t base_offset = 0;
            if (section_index == 0) {
                target = &text;
                base_offset = plan.text_offsets[obj_index];
            } else {
                target = &rodata;
                base_offset = plan.rodata_offsets[obj_index];
            }

            const std::size_t patch_offset = base_offset + reloc.offset;
            if (patch_offset + 1 >= target->size()) {
                throw std::runtime_error("Relocation for symbol '" + symbol.name +
                                         "' writes outside section bounds");
            }

            const int64_t relocated_value = static_cast<int64_t>(resolved.abs_addr) + reloc.addend;
            if (relocated_value < 0 || relocated_value > std::numeric_limits<uint16_t>::max()) {
                throw std::runtime_error("Relocation result out of range for symbol '" + symbol.name + "'");
            }

            const auto value16 = static_cast<uint16_t>(relocated_value);
            (*target)[patch_offset] = static_cast<uint8_t>((value16 >> 8) & 0xFF);
            (*target)[patch_offset + 1] = static_cast<uint8_t>(value16 & 0xFF);
        }
    }
}

} // namespace link