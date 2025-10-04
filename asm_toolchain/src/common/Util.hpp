#pragma once

#include <cstdint>
#include <stdexcept>
#include <string>

namespace util
{
    /**
     * Saves position in asm code with error
     */
    struct SourcePos
    {
        uint32_t line{1}, col{1};
    };

    /**
     * Stores full location with error
     * including file and position in code
     */
    struct SourceLoc
    {
        std::string file;
        SourcePos pos;
    };

    struct Error : std::runtime_error
    {
        SourceLoc loc;
        explicit Error(const SourceLoc &l, const std::string &message) : std::runtime_error(message), loc(l) {}
    };
}