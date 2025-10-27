// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#pragma once

#include "Parser.hpp"
#include "Pass1.hpp"
#include "Pass2.hpp"

#include <string>

namespace asmx {
struct SectionsScratch;
class Assembler {
  public:
    static void pass1(const ParseResult& pr, Pass1State& st, SectionsScratch& scratch);

    static void pass2(const ParseResult& pr, const Pass1State& st,
                      const SectionsScratch& scratch, obj::ObjectFile& out);

    static obj::ObjectFile assembleOne(const std::string& text,
                                       const std::string& file = "<input>");
};
} // namespace asmx