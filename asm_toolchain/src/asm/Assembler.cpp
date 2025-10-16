// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#include "Assembler.hpp"

#include "Directives.hpp"

namespace asmx {
obj::ObjectFile Assembler::assembleOne(const std::string& text,
                                       const std::string& file) {
    ParseResult pr = Parser::parseText(text, file);

    Pass1State st{};
    SectionsScratch scratch{};
    pass1(pr, st, scratch);

    obj::ObjectFile of;
    pass2(pr, st, scratch, of);
    return of;
}

} // namespace asmx
