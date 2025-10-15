// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#pragma once

#include "Relocation.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace obj {
/**
 * @brief Section description structure
 * This structure represents a section in an object file, including its name, flags,
 * alignment, data, and size of uninitialized data (BSS).
 */
struct SectionDescription {
    std::string name; // ".text",".data",".bss"
    uint8_t flags{0}; // 1=EXEC,2=WRITE,4=READ
    uint8_t align{1};
    std::vector<uint8_t> data;
    uint32_t bss_size{0};
};

/**
 * @brief Symbol description structure
 * This structure represents a symbol in an object file, including its name, section
 * index, value (offset within the section), and binding type.
 */
struct SymbolDescription {
    std::string name;
    int32_t section_index; // -1 = UNDEF
    uint32_t value;        // offset in section
    uint8_t bind;          // 0=Local,1=Global,2=Weak
};

/**
 * @brief Object file structure
 * This structure represents an object file, containing its sections, symbols, and
 * relocation entries.
 */
struct ObjectFile {
    std::vector<SectionDescription> sections; // [0]=.text, [1]=.data, [2]=.bss
    std::vector<SymbolDescription> symbols;
    std::vector<RelocEntry> reloc_entries;
};
} // namespace obj