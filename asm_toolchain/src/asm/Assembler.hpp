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
    static void pass1(const ParseResult& result, Pass1State& state,
                      SectionsScratch& scratch);
    obj::ObjectFile assemble(const std::string& path);
};
} // namespace asmx