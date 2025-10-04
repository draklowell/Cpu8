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