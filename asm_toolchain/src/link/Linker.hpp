// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#pragma once
#include "../object_generator/ObjectFormat.hpp"

#include <string>
#include <vector>

namespace link {

struct LinkOptions {
    uint32_t rom_base = 0x0000;    // start addr for ROM
    uint32_t rom_size = 16 * 1024; // bytes
    uint8_t rom_fill = 0xFF;       // fill byte
    uint32_t text_align = 1;       // simple alignment
    uint32_t rodata_align = 1;
    uint32_t bss_base = 0x4000; // informational for map
    std::string entry_symbol = "main";
    bool mapfile = true;
    std::string map_path = "a.map";
};

struct LinkedImage {
    uint32_t text_base = 0, text_size = 0;
    std::vector<uint8_t> rom;
    uint32_t rodata_base = 0, rodata_size = 0;
    uint32_t bss_base = 0, bss_size = 0;
    std::vector<obj::SymbolDescription> final_symbols;
};

class Linker {
  public:
    static LinkedImage link(const std::vector<obj::ObjectFile>& objects,
                            const LinkOptions& opt);
};

} // namespace link