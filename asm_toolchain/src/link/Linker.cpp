// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#include "Linker.hpp"

#include "../binary_generator/ImageWriter.hpp"
#include "RelocResolver.hpp"
#include "SectionMerger.hpp"

#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

namespace {

std::string bindToString(uint8_t bind) {
    switch (bind) {
    case 0:
        return "LOCAL";
    case 1:
        return "GLOBAL";
    case 2:
        return "WEAK";
    default:
        return "UNKNOWN";
    }
}

} // namespace

namespace link {

LinkedImage Linker::link(const std::vector<obj::ObjectFile>& objects,
                         const LinkOptions& opt) {
    const auto plan = SectionMerger::plan(objects, opt.rom_base, opt.text_align,
                                          opt.rodata_align, opt.bss_base);

    std::vector<uint8_t> merged_text;
    std::vector<uint8_t> merged_rodata;
    uint32_t merged_bss_size = 0;
    SectionMerger::mergeBytes(objects, plan, merged_text, merged_rodata, merged_bss_size);

    const auto gsym = RelocResolver::buildGlobalSymtab(objects, plan);
    RelocResolver::apply(objects, plan, gsym, merged_text, merged_rodata);

    LinkedImage image;
    image.rom = binout::ImageWriter::makeFlatROM(merged_text, merged_rodata,
                                                 opt.rom_size, opt.rom_fill);
    image.text_base = plan.layout.text_base;
    image.text_size = plan.layout.text_size;
    image.rodata_base = plan.layout.rodata_base;
    image.rodata_size = plan.layout.rodata_size;
    image.bss_base = plan.layout.bss_base;
    image.bss_size = merged_bss_size;

    image.final_symbols.reserve(gsym.size());
    for (const auto& [name, sym] : gsym) {
        if (sym.section_index >= 0) {
            image.final_symbols.push_back(obj::SymbolDescription{
                name, sym.section_index, sym.abs_addr, sym.bind});
        }
    }

    std::sort(image.final_symbols.begin(), image.final_symbols.end(),
              [](const obj::SymbolDescription& lhs, const obj::SymbolDescription& rhs) {
                  if (lhs.value != rhs.value) {
                      return lhs.value < rhs.value;
                  }
                  return lhs.name < rhs.name;
              });

    const auto entry_it = gsym.find(opt.entry_symbol);
    if (entry_it == gsym.end() || entry_it->second.section_index < 0) {
        throw std::runtime_error("Entry symbol '" + opt.entry_symbol + "' is undefined");
    }

    const auto& entry_sym = entry_it->second;
    if (entry_sym.section_index != 0 && entry_sym.section_index != 3) {
        throw std::runtime_error("Entry symbol '" + opt.entry_symbol +
                                 "' must reside in ROM (.text or .rodata)");
    }

    const auto rom_min = static_cast<uint64_t>(opt.rom_base);
    if (const uint64_t rom_max = rom_min + image.rom.size(); static_cast<uint64_t>(entry_sym.abs_addr) < rom_min ||
                                                             static_cast<uint64_t>(entry_sym.abs_addr) >= rom_max) {
        throw std::runtime_error("Entry symbol '" + opt.entry_symbol +
                                 "' lies outside the generated ROM image");
    }

    if (opt.mapfile) {
        std::ofstream map(opt.map_path);
        if (!map.is_open()) {
            throw std::runtime_error("Unable to open map file: " + opt.map_path);
        }

        map << "ROM layout:\n";
        map << ".text base=0x" << std::uppercase << std::hex << std::setfill('0')
            << std::setw(4) << image.text_base << std::dec << std::nouppercase
            << std::setfill(' ') << " size=" << image.text_size << "\n";
        map << ".rodata base=0x" << std::uppercase << std::hex << std::setfill('0')
            << std::setw(4) << image.rodata_base << std::dec << std::nouppercase
            << std::setfill(' ') << " size=" << image.rodata_size << "\n";
        map << "RAM layout:\n";
        map << ".bss base=0x" << std::uppercase << std::hex << std::setfill('0')
            << std::setw(4) << image.bss_base << std::dec << std::nouppercase
            << std::setfill(' ') << " size=" << image.bss_size << "\n";
        map << "Symbols:\n";

        for (const auto& sym : image.final_symbols) {
            map << "0x" << std::uppercase << std::hex << std::setfill('0')
                << std::setw(4) << sym.value << std::dec << std::nouppercase
                << std::setfill(' ')
                << ' ' << bindToString(sym.bind) << ' ' << sym.name << "\n";
        }

        if (!map) {
            throw std::runtime_error("Failed to write map file: " + opt.map_path);
        }
    }

    return image;
}

} // namespace link