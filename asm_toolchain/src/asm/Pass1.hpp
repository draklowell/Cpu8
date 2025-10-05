// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#pragma once

#include <vector>
#include "Parser.hpp"
#include "SymbolTable.hpp"

namespace asmx
{
    /**
     * @brief Pass 1 state structure
     * This structure holds the state information for the first pass of the assembler,
     * including the current section, location counters for each section, and the symbol table.
     */
    struct Pass1State
    {
        SectionType current{SectionType::Text};
        uint32_t lc_text{0}, lc_data{0}, lc_bss{0};
        SymbolTable symbol_table;
    };

    /**
     * @brief Pass 1 output structure
     * This structure holds the output of the first pass of the assembler,
     * including the processed lines and the final state.
     */
    struct Pass1Out
    {
        std::vector<Line> lines;
        Pass1State state;
    };

    /**
     * @brief First pass of the assembler
     * This class implements the first pass of the assembler, which processes the parsed lines,
     * updates the symbol table, and manages section transitions and location counters.
     */
    class Pass1
    {
    public:
        /**
         * @brief Run the first pass of the assembler
         * This method takes the parsed result from the parser and processes it to produce
         * the output for the first pass, including updated lines and the final state.
         * @param parse_res The parsed result from the parser.
         * @return The output of the first pass, including processed lines and state.
         */
        Pass1Out run(const ParseResult &parse_res);
    };
}
