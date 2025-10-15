// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#pragma once

#include <cstdint>

namespace obj {

/**
 * @brief Relocation types
 * This enum defines the types of relocations that can be applied to symbols in an
 * object file.
 */
enum class RelocType : uint8_t { ABS16 };
/**
 * @brief Relocation entry structure
 * This structure represents a relocation entry in an object file, including the section
 * index, offset, relocation type, symbol index, and addend.
 */
struct RelocEntry {
    uint8_t section_index{};
    RelocType type;
    uint16_t offset{};
    uint16_t symbol_index{};
    int16_t addend{0};
};
} // namespace obj