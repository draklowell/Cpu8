#pragma once

#include <cstdint>

namespace obj
{

    /**
     * @brief Relocation types
     * This enum defines the types of relocations that can be applied to symbols in an object
     * file.
     */
    enum class RelocType : uint8_t
    {
        ABS16
    };
    /**
     * @brief Relocation entry structure
     * This structure represents a relocation entry in an object file, including the section
     * index, offset, relocation type, symbol index, and addend.
     */
    struct RelocEntry
    {
        uint32_t section_index{};
        uint32_t offset{};
        RelocType type;
        uint32_t symbol_index{};
        int32_t addend{0};
    };
}