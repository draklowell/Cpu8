// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#pragma once

#include <optional>
#include <string>
#include <unordered_map>

namespace asmx {
/**
 * @brief Symbol binding enumeration
 * This enum defines the binding types for symbols in the symbol table.
 * - Local: The symbol is local to the current module.
 * - Global: The symbol is global and can be referenced from other modules.
 * - Weak: The symbol is weakly defined and can be overridden by other definitions.
 */
enum class SymbolBinding : uint8_t { Local, Global, Weak };

/**
 * @brief Section type enumeration
 * This enum defines the types of sections in an assembly program.
 * - Text: The section contains executable code.
 * - Data: The section contains initialized data.
 * - Bss: The section contains uninitialized data.
 * - None: The symbol is not associated with any section.
 */
enum class SectionType : uint8_t { Text, Data, Bss, None, RoData };

/**
 * @brief Symbol structure
 * This structure represents a symbol in the symbol table, including its name, section,
 * value (address or offset), binding type, and whether it is defined.
 */
struct Symbol {
    std::string name;
    SectionType section{SectionType::None};
    uint32_t value{0};
    SymbolBinding bind{SymbolBinding::Local};
    bool defined{false};
};

/**
 * @brief Symbol table class
 * This class manages a symbol table, allowing for the declaration, definition,
 * and lookup of symbols.
 */
class SymbolTable {
    std::unordered_map<std::string, Symbol> map_;

  public:
    /**
     * @brief Declare a symbol
     * This method declares a symbol in the symbol table. If the symbol already exists,
     * it returns a reference to the existing symbol. Otherwise, it creates a new symbol
     * with the given name and returns a reference to it.
     * @param name The name of the symbol to declare.
     * @return A reference to the declared symbol.
     * @note If the symbol is already defined, it will not be redefined.
     */
    Symbol& declare(const std::string& name);
    /**
     * @brief Define a symbol
     * This method defines a symbol in the symbol table with the given name, section,
     * offset, and binding type. If the symbol already exists and is defined, it throws
     * an error. Otherwise, it creates or updates the symbol with the provided
     * information.
     * @param name The name of the symbol to define.
     * @param section The section type of the symbol (Text, Data, Bss, None).
     * @param offset The value (address or offset) of the symbol.
     * @param binding_type The binding type of the symbol (Local, Global, Weak). Default
     * is Local.
     * @return The defined symbol.
     * @throws std::runtime_error if the symbol is already defined.
     */
    Symbol define(std::string name, SectionType section, uint32_t offset,
                  SymbolBinding binding_type = SymbolBinding::Local);
    [[nodiscard]] std::optional<Symbol> fnd(const std::string& name) const;

    std::vector<Symbol> allSymbols();
};
} // namespace asmx