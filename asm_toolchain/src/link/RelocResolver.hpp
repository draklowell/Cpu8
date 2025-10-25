// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#pragma once
#include "../object_generator/ObjectFormat.hpp"
#include "SectionMerger.hpp"

#include <unordered_map>

namespace link {
struct ResolvedSym {
    int32_t section_index; // -1 undefined
    uint32_t abs_addr;
    uint8_t bind;
};
class RelocResolver {
  public:
    // Build a unified symbol table, enforce ODR, resolve absolute addresses.
    static std::unordered_map<std::string, ResolvedSym>
    buildGlobalSymtab(const std::vector<obj::ObjectFile>& objects,
                      const MergePlan& plan);

    static void apply(const std::vector<obj::ObjectFile>& objects,
                      const MergePlan& plan,
                      const std::unordered_map<std::string, ResolvedSym>& gsym,
                      std::vector<uint8_t>& text, std::vector<uint8_t>& rodata);
};
} // namespace link