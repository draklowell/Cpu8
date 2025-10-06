// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#include <algorithm>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <type_traits>
#include <variant>
#include <vector>

#include "InstrEncoding.hpp"
#include "Parser.hpp"

namespace
{
    std::string regName(const asmx::Reg reg)
    {
        switch (reg)
        {
        case asmx::Reg::AC:
            return "ac";
        case asmx::Reg::XH:
            return "xh";
        case asmx::Reg::YL:
            return "yl";
        case asmx::Reg::YH:
            return "yh";
        case asmx::Reg::ZL:
            return "zl";
        case asmx::Reg::ZH:
            return "zh";
        case asmx::Reg::FR:
            return "fr";
        case asmx::Reg::SP:
            return "sp";
        case asmx::Reg::PC:
            return "pc";
        case asmx::Reg::X:
            return "x";
        case asmx::Reg::Y:
            return "y";
        case asmx::Reg::Z:
            return "z";
        default:
            return "invalid";
        }
    }

    std::string operandTypeName(const asmx::OperandType type)
    {
        switch (type)
        {
        case asmx::OperandType::None:
            return "None";
        case asmx::OperandType::Reg:
            return "Reg";
        case asmx::OperandType::Imm8:
            return "Imm8";
        case asmx::OperandType::Imm16:
            return "Imm16";
        case asmx::OperandType::Label:
            return "Label";
        case asmx::OperandType::MemAbs16:
            return "MemAbs16";
        }
        return "Unknown";
    }

    std::string signatureToString(const std::vector<asmx::OperandType> &signature)
    {
        if (signature.empty())
            return "-";

        std::string result;
        for (size_t i = 0; i < signature.size(); ++i)
        {
            if (i != 0)
                result += ", ";
            result += operandTypeName(signature[i]);
        }
        return result;
    }

    std::string argumentToString(const asmx::Argument &arg)
    {
        std::ostringstream oss;
        switch (arg.operant_type)
        {
        case asmx::OperandType::None:
            return "-";
        case asmx::OperandType::Reg:
            return regName(arg.reg);
        case asmx::OperandType::Imm8:
            oss << "#0x" << std::hex << std::uppercase << std::setw(2) << std::setfill('0')
                << static_cast<unsigned>(arg.value);
            return oss.str();
        case asmx::OperandType::Imm16:
            oss << "#0x" << std::hex << std::uppercase << std::setw(4) << std::setfill('0')
                << static_cast<unsigned>(arg.value);
            return oss.str();
        case asmx::OperandType::Label:
            return std::string("label:") + arg.label;
        case asmx::OperandType::MemAbs16:
            oss << "[0x" << std::hex << std::uppercase << std::setw(4) << std::setfill('0')
                << static_cast<unsigned>(arg.value) << ']';
            return oss.str();
        }
        return "?";
    }

    void dumpParseResult(const std::string &title, const asmx::ParseResult &result)
    {
        std::cout << "\n=== " << title << " ===\n";
        size_t index = 0;
        for (const auto &line : result.lines)
        {
            const util::SourceLoc *loc = nullptr;
            std::visit([&](const auto &node) { loc = &node.loc; }, line);
            std::cout << std::setw(2) << index++ << ": ";
            if (loc)
            {
                std::cout << loc->file << ':' << loc->pos.line << ':' << loc->pos.col << " -> ";
            }

            std::visit(
                [](const auto &node)
                {
                    using T = std::decay_t<decltype(node)>;
                    if constexpr (std::is_same_v<T, asmx::Label>)
                    {
                        std::cout << "label " << node.name;
                    }
                    else if constexpr (std::is_same_v<T, asmx::Directive>)
                    {
                        std::cout << '.' << node.name;
                        if (!node.args.empty())
                        {
                            std::cout << " args:";
                            for (size_t i = 0; i < node.args.size(); ++i)
                            {
                                if (i != 0)
                                {
                                    std::cout << ',';
                                }
                                std::cout << ' ' << node.args[i];
                            }
                        }
                    }
                    else if constexpr (std::is_same_v<T, asmx::Instruction>)
                    {
                        std::cout << node.mnemonic;
                        if (!node.args.empty())
                        {
                            std::cout << " (";
                            for (size_t i = 0; i < node.args.size(); ++i)
                            {
                                if (i != 0)
                                {
                                    std::cout << ", ";
                                }
                                std::cout << argumentToString(node.args[i]);
                            }
                            std::cout << ')';
                        }
                    }
                },
                line);
            std::cout << '\n';
        }
    }
}

int main()
{
    const auto &table = asmx::EncodeTable::get();
    std::vector<const std::pair<const asmx::Key, asmx::OpcodeSpecs> *> entries;
    entries.reserve(table.entries().size());

    for (const auto &item : table.entries())
    {
        entries.push_back(&item);
    }

    std::sort(entries.begin(), entries.end(), [](const auto *lhs, const auto *rhs)
              { return lhs->second.opcode < rhs->second.opcode; });

    std::cout << "Opcode table (" << entries.size() << " entries)\n";
    for (const auto *entry : entries)
    {
        const auto &key = entry->first;
        const auto &spec = entry->second;

        std::cout << std::uppercase << std::hex << std::setw(2) << std::setfill('0')
                  << static_cast<int>(spec.opcode) << std::dec << std::setfill(' ')
                  << ": " << key.mnemonic
                  << " [" << signatureToString(spec.signature) << "]"
                  << " size=" << static_cast<int>(spec.size);

        if (spec.needs_reloc)
            std::cout << " reloc";
        std::cout << '\n';
    }

    const std::vector<asmx::OperandType> sig = {asmx::OperandType::None};

    if (auto spec = table.find("push-ac", sig))
    {
        std::cout << "0x" << std::hex << +spec->opcode << std::dec << "\n";
        // за бажанням:
        std::cout << "size=" << +spec->size << ", reloc=" << (spec->needs_reloc ? "yes" : "no") << "\n";
    }
    else
    {
        std::cout << "not found\n";
    }

    const std::vector<std::pair<std::string, std::string>> samples = {
        {"control_flow", R"(.text
main:
    ldi x, 0x1234
    mov ac, xh
    cmp yh
    jnz main
    hlt
)"},
        {"data_decls", R"(.data
value:
    .word 0xBEEF
array:
    .byte 1, 2, 3
)"},
    };

    asmx::Parser parser;
    for (const auto &sample : samples)
    {
        try
        {
            auto result = parser.parseText(sample.second, sample.first);
            dumpParseResult(sample.first, result);
        }
        catch (const std::exception &ex)
        {
            std::cerr << "Failed to parse sample '" << sample.first << "': " << ex.what() << "\n";
        }
    }

    return 0;
}