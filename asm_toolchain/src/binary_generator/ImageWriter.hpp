// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#pragma once
#include <cstdint>
#include <string>
#include <vector>
namespace binout {
struct ImageWriter {
    // Compose flat ROM image: [text][rodata] padded to rom_size with fill.
    static std::vector<uint8_t> makeFlatROM(const std::vector<uint8_t>& text,
                                            const std::vector<uint8_t>& rodata,
                                            uint32_t rom_size, uint8_t fill);
    static void writeBIN(const std::string& path, const std::vector<uint8_t>& rom);
};
} // namespace binout