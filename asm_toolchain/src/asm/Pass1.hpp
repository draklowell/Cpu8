// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#pragma once

#include "Parser.hpp"
#include "SymbolTable.hpp"

#include <vector>

namespace asmx {
/**
 * @brief Pass 1 state structure
 * This structure holds the state information for the first pass of the assembler,
 * including the current section, location counters for each section, and the symbol
 * table.
 */
struct Pass1State {
    SectionType current{SectionType::Text};
    uint32_t lc_text{0}, lc_data{0}, lc_bss{0}, lc_rodata{0};
    SymbolTable symbol_table;
};

/**
 * @brief Pass 1 output structure
 * This structure holds the output of the first pass of the assembler,
 * including the processed lines and the final state.
 */
struct Pass1Out {
    std::vector<Line> lines;
    Pass1State state;
};

} // namespace asmx
