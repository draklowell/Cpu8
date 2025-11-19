// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#include "ImageWriter.hpp"

#include <cstdint>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace binout {

std::vector<uint8_t> ImageWriter::makeFlatROM(const std::vector<uint8_t>& text,
                                              const std::vector<uint8_t>& rodata,
                                              uint32_t rom_size, uint8_t fill) {
    std::vector<uint8_t> rom;
    rom.reserve(text.size() + rodata.size());
    rom.insert(rom.end(), text.begin(), text.end());
    rom.insert(rom.end(), rodata.begin(), rodata.end());

    if (rom_size != 0U) {
        if (rom.size() > static_cast<std::size_t>(rom_size)) {
            throw std::runtime_error("ROM image exceeds configured size (" +
                                     std::to_string(rom.size()) + " > " +
                                     std::to_string(rom_size) + ")");
        }
        rom.resize(static_cast<std::size_t>(rom_size), fill);
    }

    return rom;
}

void ImageWriter::writeBIN(const std::string& path, const std::vector<uint8_t>& rom) {
    std::ofstream file(path, std::ios::binary);
    if (!file.is_open()) {
        throw std::runtime_error("Unable to open output file: " + path);
    }

    file.write(reinterpret_cast<const char*>(rom.data()),
               static_cast<std::streamsize>(rom.size()));
    if (!file) {
        throw std::runtime_error("Failed to write ROM image to: " + path);
    }
}

} // namespace binout