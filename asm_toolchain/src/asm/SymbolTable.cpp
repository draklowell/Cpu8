// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#include "SymbolTable.hpp"

#include <map>
#include <stdexcept>
#include <utility>
#include <vector>

namespace asmx {
Symbol& SymbolTable::declare(const std::string& name) {
    if (const auto it = map_.find(name); it != map_.end()) {
        return it->second;
    }

    Symbol symbol;
    symbol.name = name;
    symbol.section = SectionType::None;
    symbol.value = 0;
    symbol.bind = SymbolBinding::Local;
    symbol.defined = false;
    auto [instIt, _] = map_.emplace(name, std::move(symbol));
    return instIt->second;
}

Symbol SymbolTable::define(std::string name, SectionType section, uint32_t offset,
                           SymbolBinding binding_type) {
    const auto it = map_.find(name);
    if (it == map_.end()) {
        Symbol symbol;
        symbol.name = std::move(name);
        symbol.section = section;
        symbol.bind = binding_type;
        symbol.defined = true;
        auto [insIt, _] = map_.emplace(symbol.name, symbol);
        return insIt->second;
    }

    Symbol& sym = it->second;
    if (sym.defined) {
        throw std::runtime_error("redifinition pf symbol 1 '" + sym.name + "'");
    }
    sym.section = section;
    sym.value = offset;
    sym.bind = binding_type;
    sym.defined = true;
    return sym;
}

std::optional<Symbol> SymbolTable::fnd(const std::string& name) const {
    const auto it = map_.find(name);
    if (it == map_.end()) {
        return std::nullopt;
    }
    return it->second;
}

std::vector<Symbol> SymbolTable::allSymbols() const {
    std::vector<Symbol> out;
    out.reserve(map_.size());
    for (const auto& kv : map_)
        out.push_back(kv.second);
    return out;
}
} // namespace asmx