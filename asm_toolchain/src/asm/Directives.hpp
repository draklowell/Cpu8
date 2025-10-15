// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#pragma once

#include "../object_generator/ObjectFormat.hpp"
#include "Parser.hpp"
#include "Pass1.hpp"
#include "SymbolTable.hpp"

#include <cstdint>
#include <string>
#include <variant>
#include <vector>
namespace asmx {
/**
 *@brief  Captures a single directive payload recorded during pass 1.
 *
 */
struct DataItem {
    enum class Kind {
        Byte,
        Word,
        Ascii,
        Asciz,
        SectionSwitch,
        Globl,
        Extern,
    };

    Kind kind{Kind::Byte};
    // For .byte, .ascii + z
    std::vector<uint8_t> bytes;

    // Identifiers mentioned by directive (.globl/.extern)
    std::vector<std::string> idents;

    // Represents 2 byte elemenets can be immediate 16 bit or symbol reference.
    std::vector<std::variant<uint16_t, std::string>> words;

    util::SourceLoc loc;
};

/**
 * @brief Section-local staging buffer used during pass1.
 */
struct SectionBuffer {
    std::vector<DataItem> items;
    uint32_t lc{0};
};

/**
 * @brief  Separated Buffers for every data section
 */
struct SectionsScratch {
    SectionBuffer text;
    SectionBuffer data;
    SectionBuffer bss;
    SectionBuffer rodata;
};

/**
 *@brief  Directive manager used by pass1 pass2
 */
class Directives {
    /**
     * @brief Consume a directive during pass 1.
     *
     * Updates the pass-1 state (current section and location counters),
     * records any data payloads in @p scratch and declares symbols when
     * required.
     */
    static void handlePass1(const Directive& dir, Pass1State& st,
                            SectionsScratch& scratch);

    /**
     * @brief Emit the bytes and relocarions for pass 2.
     */
    static void emitPass2(const SectionsScratch& scratch, const SymbolTable& symtab,
                          obj::ObjectFile& out);
};
} // namespace asmx