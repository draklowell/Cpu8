// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#include "SectionMerger.hpp"

#include <algorithm>
#include <cstdint>
#include <limits>
#include <stdexcept>

namespace {

uint32_t alignUp(uint32_t value, uint32_t align) {
    if (align <= 1) {
        return value;
    }
    uint32_t remainder = value % align;
    if (remainder == 0) {
        return value;
    }
    uint64_t result = static_cast<uint64_t>(value) + (align - remainder);
    if (result > std::numeric_limits<uint32_t>::max()) {
        throw std::runtime_error("section size overflow");
    }
    return static_cast<uint32_t>(result);
}

const obj::SectionDescription* getSection(const obj::ObjectFile& object, size_t index) {
    if (index < object.sections.size()) {
        return &object.sections[index];
    }
    return nullptr;
}

uint32_t sectionDataSize(const obj::ObjectFile& object, size_t index) {
    const auto* section = getSection(object, index);
    if (section == nullptr) {
        return 0;
    }
    return static_cast<uint32_t>(section->data.size());
}

uint32_t sectionBssSize(const obj::ObjectFile& object, size_t index) {
    const auto* section = getSection(object, index);
    if (section == nullptr) {
        return 0;
    }
    return section->bss_size;
}

} // namespace

namespace link {

MergePlan SectionMerger::plan(const std::vector<obj::ObjectFile>& objects,
                              uint32_t rom_base, uint32_t text_align,
                              uint32_t rodata_align, uint32_t bss_base) {
    MergePlan plan;
    plan.text_offsets.resize(objects.size(), 0);
    plan.rodata_offsets.resize(objects.size(), 0);
    plan.bss_offsets.resize(objects.size(), 0);

    uint32_t text_cursor = 0;
    for (size_t i = 0; i < objects.size(); ++i) {
        const auto& object = objects[i];

        const auto* data_section = getSection(object, 1);
        if (data_section != nullptr && !data_section->data.empty()) {
            throw std::runtime_error("initialized .data not supported");
        }

        text_cursor = alignUp(text_cursor, text_align);
        plan.text_offsets[i] = text_cursor;
        text_cursor += sectionDataSize(object, 0);
    }

    uint32_t text_size = text_cursor;
    uint32_t rodata_base_offset = alignUp(text_size, rodata_align);
    plan.layout.text_base = rom_base;
    plan.layout.text_size = rodata_base_offset;

    uint32_t rodata_cursor = 0;
    for (size_t i = 0; i < objects.size(); ++i) {
        rodata_cursor = alignUp(rodata_cursor, rodata_align);
        plan.rodata_offsets[i] = rodata_cursor;
        rodata_cursor += sectionDataSize(objects[i], 3);
    }

    plan.layout.rodata_base = rom_base + rodata_base_offset;
    plan.layout.rodata_size = rodata_cursor;

    uint32_t bss_cursor = 0;
    for (size_t i = 0; i < objects.size(); ++i) {
        plan.bss_offsets[i] = bss_cursor;
        bss_cursor += sectionBssSize(objects[i], 2);
    }

    plan.layout.bss_base = bss_base;
    plan.layout.bss_size = bss_cursor;

    uint64_t total_rom = static_cast<uint64_t>(plan.layout.text_size) +
                         static_cast<uint64_t>(plan.layout.rodata_size);
    if (total_rom > std::numeric_limits<uint32_t>::max()) {
        throw std::runtime_error("section size overflow");
    }

    return plan;
}

void SectionMerger::mergeBytes(const std::vector<obj::ObjectFile>& objects,
                               const MergePlan& plan, std::vector<uint8_t>& out_text,
                               std::vector<uint8_t>& out_rodata,
                               uint32_t& out_bss_size) {
    out_text.assign(plan.layout.text_size, 0);
    out_rodata.assign(plan.layout.rodata_size, 0);

    for (size_t i = 0; i < objects.size(); ++i) {
        const auto* text_section = getSection(objects[i], 0);
        if (text_section != nullptr && !text_section->data.empty()) {
            const auto offset = plan.text_offsets[i];
            if (offset + text_section->data.size() > out_text.size()) {
                throw std::runtime_error("section size overflow");
            }
            std::copy(text_section->data.begin(), text_section->data.end(),
                      out_text.begin() + offset);
        }

        const auto* rodata_section = getSection(objects[i], 3);
        if (rodata_section != nullptr && !rodata_section->data.empty()) {
            const auto offset = plan.rodata_offsets[i];
            if (offset + rodata_section->data.size() > out_rodata.size()) {
                throw std::runtime_error("section size overflow");
            }
            std::copy(rodata_section->data.begin(), rodata_section->data.end(),
                      out_rodata.begin() + offset);
        }
    }

    out_bss_size = plan.layout.bss_size;
}

} // namespace link
