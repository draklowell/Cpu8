// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#pragma once

#include "Pass1.hpp"
#include "../obj_gen/ObjectFormat.hpp"

namespace asmx
{
    /**
     * @brief Second pass of the assembler
     * This class implements the second pass of the assembler, which takes the output from
     * the first pass and generates the final object file.
     */
    class Pass2
    {
    public:
        /**
         * @brief Run the second pass of the assembler
         * This method takes the output from the first pass and processes it to produce
         * the final object file.
         * @param in The output from the first pass of the assembler.
         * @return The generated object file.
         */
        obj::ObjectFile run(const Pass1Out &in);
    };
}
