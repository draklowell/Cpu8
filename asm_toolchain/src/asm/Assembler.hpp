// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com


#pragma once

#include <string>
#include "Parser.hpp"
#include "Pass1.hpp"
#include "Pass2.hpp"

namespace asmx
{
    class Assembler
    {
    public:
        obj::ObjectFile assemble(const std::string &path);
    };
}