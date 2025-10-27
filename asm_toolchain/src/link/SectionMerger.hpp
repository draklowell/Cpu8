// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#pragma once
#include "../object_generator/ObjectFormat.hpp"

#include <vector>
namespace link {
struct Layout {
    // absolute placements inside ROM
    uint32_t text_base, text_size;
    uint32_t rodata_base, rodata_size;
    uint32_t bss_base, bss_size; // in RAM (logical)
};
struct MergePlan {
    // concatenation plans: for each input object, record base offsets
    std::vector<uint32_t> text_offsets;   // size == objects.size()
    std::vector<uint32_t> rodata_offsets; // size == objects.size()
    std::vector<uint32_t> bss_offsets;    // size == objects.size()
    Layout layout;
};
struct SectionMerger {
    static MergePlan plan(const std::vector<obj::ObjectFile>& objects,
                          uint32_t rom_base, uint32_t text_align, uint32_t rodata_align,
                          uint32_t bss_base);
    static void mergeBytes(const std::vector<obj::ObjectFile>& objects,
                           const MergePlan& plan, std::vector<uint8_t>& out_text,
                           std::vector<uint8_t>& out_rodata, uint32_t& out_bss_size);
};
} // namespace link