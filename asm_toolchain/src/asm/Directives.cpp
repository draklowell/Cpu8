
// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#include "Directives.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <iterator>
#include <sstream>
#include <stdexcept>
#include <string_view>
#include <unordered_map>

namespace asmx {
namespace {
constexpr uint8_t kSectionExec  = 0x01;
constexpr uint8_t kSectionWrite = 0x02;
constexpr uint8_t kSectionRead  = 0x04;

struct PendingReloc {
    uint8_t         section_index{};
    uint16_t        offset{};
    std::string     symbol;
    util::SourceLoc loc;
};

[[nodiscard]] std::string normaliseDirectiveName(const std::string& raw) {
    std::string lowered;
    lowered.reserve(raw.size());
    for (char c : raw) {
        lowered.push_back(
            static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
    }
    if (!lowered.empty() && lowered.front() == '.') {
        lowered.erase(lowered.begin());
    }
    return lowered;
}

[[nodiscard]] bool isStringLiteral(const std::string& token) {
    return token.size() >= 2U && token.front() == '"' && token.back() == '"';
}

[[nodiscard]] bool isValidIdentifier(const std::string& text) {
    if (text.empty()) {
        return false;
    }

    const char c0 = text.front();
    if (!(std::isalpha(static_cast<unsigned char>(c0)) || c0 == '_')) {
        return false;
    }

    return std::all_of(std::next(text.begin()), text.end(), [](char ch) {
        return std::isalnum(static_cast<unsigned char>(ch)) || ch == '_' || ch == '.';
    });
}

[[nodiscard]] std::vector<uint8_t> decodeStringLiteral(const std::string&     token,
                                                       const util::SourceLoc& loc) {
    if (!isStringLiteral(token)) {
        throw util::Error(loc, "string literal expected");
    }

    std::vector<uint8_t> bytes;
    bytes.reserve(token.size());

    for (std::size_t i = 1; i + 1 < token.size(); ++i) {
        const char ch = token[i];
        if (ch != '\\') {
            bytes.push_back(static_cast<uint8_t>(ch));
            continue;
        }

        if (i + 1 >= token.size() - 1) {
            throw util::Error(loc, "unterminated escape sequence in string literal");
        }

        const char esc = token[++i];
        switch (esc) {
        case '\\':
        case '\"':
            bytes.push_back(static_cast<uint8_t>(esc));
            break;
        case 'n':
            bytes.push_back('\n');
            break;
        case 't':
            bytes.push_back('\t');
            break;
        case 'r':
            bytes.push_back('\r');
            break;
        case '0':
            bytes.push_back('\0');
            break;
        default:
            throw util::Error(loc, "unsupported escape sequence in string literal");
        }
    }

    return bytes;
}

[[nodiscard]] uint64_t parseIntegerLiteral(const std::string&     text,
                                           const util::SourceLoc& loc) {
    if (text.empty()) {
        throw util::Error(loc, "invalid numeric literal ''");
    }

    if (text.front() == '-' || text.front() == '+') {
        throw util::Error(loc, "negative values are not supported in directives");
    }

    int         base   = 10;
    std::size_t prefix = 0;
    if (text.size() > 2 && text[0] == '0' && (text[1] == 'x' || text[1] == 'X')) {
        base   = 16;
        prefix = 2;
    } else if (text.size() > 2 && text[0] == '0' &&
               (text[1] == 'b' || text[1] == 'B')) {
        base   = 2;
        prefix = 2;
    }

    if (prefix >= text.size()) {
        throw util::Error(loc, "invalid numeric literal '" + text + "'");
    }

    const std::string_view digits{text.data() + prefix, text.size() - prefix};
    if (digits.empty()) {
        throw util::Error(loc, "invalid numeric literal '" + text + "'");
    }

    uint64_t value = 0;
    for (char c : digits) {
        int digit = -1;
        if (std::isdigit(static_cast<unsigned char>(c))) {
            digit = c - '0';
        } else if (base == 16 && std::isxdigit(static_cast<unsigned char>(c))) {
            digit = std::tolower(static_cast<unsigned char>(c)) - 'a' + 10;
        } else {
            throw util::Error(loc, "invalid numeric literal '" + text + "'");
        }

        if (digit >= base) {
            throw util::Error(loc, "invalid numeric literal '" + text + "'");
        }

        value = value * static_cast<uint64_t>(base) + static_cast<uint64_t>(digit);
    }

    return value;
}

[[nodiscard]] std::string formatHex(uint64_t value) {
    std::ostringstream oss;
    oss << "0x" << std::hex << std::uppercase << value;
    return oss.str();
}

[[nodiscard]] uint16_t parseWordValue(const std::string&     text,
                                      const util::SourceLoc& loc,
                                      const char*            directive) {
    const uint64_t value = parseIntegerLiteral(text, loc);
    if (value > 0xFFFFu) {
        throw util::Error(loc, "value " + formatHex(value) + " is out of range for " +
                                   directive);
    }
    return static_cast<uint16_t>(value);
}

[[nodiscard]] uint8_t parseByteValue(const std::string&     text,
                                     const util::SourceLoc& loc) {
    const uint64_t value = parseIntegerLiteral(text, loc);
    if (value > 0xFFu) {
        throw util::Error(loc,
                          "value " + formatHex(value) + " is out of range for .byte");
    }
    return static_cast<uint8_t>(value);
}

SectionBuffer& selectBuffer(SectionsScratch& scratch, SectionType section) {
    switch (section) {
    case SectionType::Text:
        return scratch.text;
    case SectionType::Data:
        return scratch.data;
    case SectionType::Bss:
        return scratch.bss;
    case SectionType::RoData:
        return scratch.rodata;
    case SectionType::None:
        break;
    }
    throw std::logic_error("invalid section for buffer selection");
}

[[nodiscard]] const SectionBuffer& selectBuffer(const SectionsScratch& scratch,
                                                SectionType            section) {
    switch (section) {
    case SectionType::Text:
        return scratch.text;
    case SectionType::Data:
        return scratch.data;
    case SectionType::Bss:
        return scratch.bss;
    case SectionType::RoData:
        return scratch.rodata;
    case SectionType::None:
        break;
    }
    throw std::logic_error("invalid section for buffer selection");
}

uint32_t& selectLocationCounter(Pass1State& state, SectionType section) {
    switch (section) {
    case SectionType::Text:
        return state.lc_text;
    case SectionType::Data:
        return state.lc_data;
    case SectionType::Bss:
        return state.lc_bss;
    case SectionType::RoData:
        return state.lc_rodata;
    case SectionType::None:
        break;
    }
    throw std::logic_error("invalid section for location counter");
}

[[nodiscard]] int32_t sectionIndexFromType(SectionType section) {
    switch (section) {
    case SectionType::Text:
        return 0;
    case SectionType::Data:
        return 1;
    case SectionType::Bss:
        return 2;
    case SectionType::RoData:
        return 3;
    case SectionType::None:
        return -1;
    }
    return -1;
}

void appendBytes(std::vector<uint8_t>& dest, const std::vector<uint8_t>& src) {
    dest.insert(dest.end(), src.begin(), src.end());
}
} // namespace

void Directives::handlePass1(const Directive& dir, Pass1State& st,
                             SectionsScratch& scratch) {
    const std::string directive = normaliseDirectiveName(dir.name);

    auto ensureArgs = [&dir](bool condition, const std::string& message) {
        if (!condition) {
            throw util::Error(dir.loc, message);
        }
    };

    if (directive == "text" || directive == "code") {
        st.current = SectionType::Text;
        return;
    }
    if (directive == "data") {
        st.current = SectionType::Data;
        return;
    }
    if (directive == "bss") {
        st.current = SectionType::Bss;
        return;
    }
    if (directive == "rodata") {
        st.current = SectionType::RoData;
        return;
    }

    if (directive == "globl" || directive == "global") {
        ensureArgs(!dir.args.empty(), "symbol name expected after .globl");
        for (const std::string& name : dir.args) {
            ensureArgs(isValidIdentifier(name),
                       "invalid symbol name '" + name + "' in .globl");
            Symbol& sym = st.symbol_table.declare(name);
            sym.bind    = SymbolBinding::Global;
        }
        return;
    }

    if (directive == "extern") {
        ensureArgs(!dir.args.empty(), "symbol name expected after .extern");
        for (const std::string& name : dir.args) {
            ensureArgs(isValidIdentifier(name),
                       "invalid symbol name '" + name + "' in .extern");
            Symbol& sym = st.symbol_table.declare(name);
            sym.bind    = SymbolBinding::Global;
            sym.defined = false;
            sym.section = SectionType::None;
            sym.value   = 0;
        }
        return;
    }

    if (st.current == SectionType::Bss &&
        (directive == "byte" || directive == "word" || directive == "ascii" ||
         directive == "asciz")) {
        throw util::Error(dir.loc, "." + directive + " is not allowed in .bss section");
    }

    SectionBuffer& buffer = selectBuffer(scratch, st.current);
    uint32_t&      lc     = selectLocationCounter(st, st.current);

    if (directive == "byte") {
        ensureArgs(!dir.args.empty(), ".byte expects at least one argument");
        DataItem item;
        item.kind = DataItem::Kind::Byte;
        item.loc  = dir.loc;

        for (const std::string& arg : dir.args) {
            if (isStringLiteral(arg)) {
                auto bytes = decodeStringLiteral(arg, dir.loc);
                appendBytes(item.bytes, bytes);
            } else {
                try {
                    item.bytes.push_back(parseByteValue(arg, dir.loc));
                } catch (const util::Error& err) {
                    const std::string_view msg{err.what()};
                    if (msg.find("out of range") != std::string_view::npos) {
                        throw;
                    }
                    throw util::Error(dir.loc, "expected number or string in .byte");
                }
            }
        }

        lc += static_cast<uint32_t>(item.bytes.size());
        buffer.lc = lc;
        buffer.items.push_back(std::move(item));
        return;
    }

    if (directive == "word") {
        ensureArgs(!dir.args.empty(), ".word expects at least one argument");
        DataItem item;
        item.kind = DataItem::Kind::Word;
        item.loc  = dir.loc;
        item.words.reserve(dir.args.size());

        for (const std::string& arg : dir.args) {
            if (isStringLiteral(arg)) {
                throw util::Error(dir.loc, ".word does not accept string literals");
            }

            if (isValidIdentifier(arg)) {
                st.symbol_table.declare(arg);
                item.words.emplace_back(arg);
            } else {
                try {
                    item.words.emplace_back(parseWordValue(arg, dir.loc, ".word"));
                } catch (const util::Error& err) {
                    const std::string_view msg{err.what()};
                    if (msg.find("out of range") != std::string_view::npos) {
                        throw;
                    }
                    throw util::Error(dir.loc, "unknown token in .word: '" + arg + "'");
                }
            }
        }

        lc += static_cast<uint32_t>(item.words.size() * 2U);
        buffer.lc = lc;
        buffer.items.push_back(std::move(item));
        return;
    }

    if (directive == "ascii" || directive == "asciz") {
        ensureArgs(!dir.args.empty(),
                   std::string(".") + directive + " expects a string literal");
        DataItem item;
        item.kind =
            directive == "ascii" ? DataItem::Kind::Ascii : DataItem::Kind::Asciz;
        item.loc = dir.loc;

        for (const std::string& arg : dir.args) {
            if (!isStringLiteral(arg)) {
                throw util::Error(dir.loc, std::string(".") + directive +
                                               " expects a string literal");
            }
            appendBytes(item.bytes, decodeStringLiteral(arg, dir.loc));
        }

        if (directive == "asciz") {
            item.bytes.push_back(0x00);
        }

        lc += static_cast<uint32_t>(item.bytes.size());
        buffer.lc = lc;
        buffer.items.push_back(std::move(item));
        return;
    }

    throw util::Error(dir.loc, "unknown directive '" + dir.name + "'");
}

void Directives::emitPass2(const SectionsScratch& scratch, const SymbolTable& symtab,
                           obj::ObjectFile& out) {
    out.sections.clear();
    out.symbols.clear();
    out.reloc_entries.clear();

    out.sections.resize(4);
    auto& text = out.sections[0];
    text.name  = ".text";
    text.flags = static_cast<uint8_t>(kSectionExec | kSectionRead);

    auto& data = out.sections[1];
    data.name  = ".data";
    data.flags = static_cast<uint8_t>(kSectionRead | kSectionWrite);

    auto& bss    = out.sections[2];
    bss.name     = ".bss";
    bss.flags    = static_cast<uint8_t>(kSectionRead | kSectionWrite);
    bss.bss_size = selectBuffer(scratch, SectionType::Bss).lc;

    auto& rodata = out.sections[3];
    rodata.name  = ".rodata";
    rodata.flags = static_cast<uint8_t>(kSectionRead);

    std::vector<PendingReloc> pending_relocs;

    auto emitSection = [&](const SectionBuffer& buf, obj::SectionDescription& desc,
                           uint8_t section_index) {
        for (const DataItem& item : buf.items) {
            switch (item.kind) {
            case DataItem::Kind::Byte:
            case DataItem::Kind::Ascii:
            case DataItem::Kind::Asciz:
                appendBytes(desc.data, item.bytes);
                break;
            case DataItem::Kind::Word: {
                std::size_t base_offset = desc.data.size();
                desc.data.resize(desc.data.size() + item.words.size() * 2U);
                for (std::size_t idx = 0; idx < item.words.size(); ++idx) {
                    const auto& entry  = item.words[idx];
                    uint8_t*    target = desc.data.data() + base_offset + idx * 2U;
                    if (std::holds_alternative<uint16_t>(entry)) {
                        const uint16_t value = std::get<uint16_t>(entry);
                        target[0] = static_cast<uint8_t>((value >> 8U) & 0xFFU);
                        target[1] = static_cast<uint8_t>(value & 0xFFU);
                    } else {
                        target[0] = 0;
                        target[1] = 0;
                        pending_relocs.push_back(
                            PendingReloc{section_index,
                                         static_cast<uint16_t>(base_offset + idx * 2U),
                                         std::get<std::string>(entry), item.loc});
                    }
                }
                break;
            }
            default:
                break;
            }
        }
    };

    emitSection(selectBuffer(scratch, SectionType::Text), text, 0);
    emitSection(selectBuffer(scratch, SectionType::Data), data, 1);
    emitSection(selectBuffer(scratch, SectionType::RoData), rodata, 3);

    // Produce the symbol table in deterministic alphabetical order.
    std::vector<Symbol> symbols = symtab.allSymbols();
    std::sort(symbols.begin(), symbols.end(),
              [](const Symbol& a, const Symbol& b) { return a.name < b.name; });

    out.symbols.reserve(symbols.size());
    std::unordered_map<std::string, uint16_t> symbol_indices;
    symbol_indices.reserve(symbols.size());

    for (std::size_t i = 0; i < symbols.size(); ++i) {
        const Symbol& sym           = symbols[i];
        const int32_t section_index = sectionIndexFromType(sym.section);

        obj::SymbolDescription desc;
        desc.name          = sym.name;
        desc.section_index = section_index;
        desc.value         = sym.value;
        desc.bind          = static_cast<uint8_t>(sym.bind);

        if (section_index >= 0) {
            desc.value = sym.value;
        } else {
            desc.value = 0;
        }

        out.symbols.push_back(std::move(desc));
        symbol_indices.emplace(sym.name, static_cast<uint16_t>(i));
    }

    for (const PendingReloc& rel : pending_relocs) {
        auto it = symbol_indices.find(rel.symbol);
        if (it == symbol_indices.end()) {
            throw util::Error(rel.loc,
                              "undefined symbol '" + rel.symbol + "' in relocation");
        }

        obj::RelocEntry entry;
        entry.section_index = rel.section_index;
        entry.offset        = rel.offset;
        entry.type          = obj::RelocType::ABS16;
        entry.symbol_index  = it->second;
        entry.addend        = 0;
        out.reloc_entries.push_back(entry);
    }
}
} // namespace asmx
