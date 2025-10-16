// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#pragma once

#include "../object_generator/ObjectFormat.hpp"

namespace asmx {
struct PendingTextReloc {
    uint32_t offset{};
    std::string symbol;
    util::SourceLoc loc;
};

struct SymbolResolution {
    uint16_t value{0};
    bool needs_reloc{false};
};
} // namespace asmx
