// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#include <algorithm>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

#include "InstrEncoding.hpp"

namespace
{
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

    return 0;
}
