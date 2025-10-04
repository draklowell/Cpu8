#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace asmx
{
    /**
     * @brief Register enumeration
     *
     * This enum class defines various CPU registers used in assembly instructions.
     * The registers are categorized by their bit-width (8-bit, 16-bit) and include
     * some aliases for convenience.
     *
     * @note The `Invalid` entry is used to represent an invalid or uninitialized register.
     * @note Flags register (FR) is treated as a 3-bit register for specific operations.
     */
    enum class Reg : uint8_t
    {
        // 8-bit registers
        AC,
        XH,
        YL,
        YH,
        ZL,
        ZH,
        FR,
        // 16-bit registers
        SP,
        PC,
        // Aliases
        X,
        Y,
        Z,

        Invalid
    };

    /**
     * @brief Operand type enumeration
     * This enum class defines the types of operands that can be used in assembly instructions.
     */
    enum class OperandType : uint8_t
    {
        None,
        Reg,
        Imm8,
        Imm16,
        Label,
        MemAbs16,
    };

    /**
     * @brief Instruction argument structure
     *
     * This structure represents an argument for an assembly instruction.
     * It can hold different types of operands, including registers, immediate values,
     * and labels. The type of operand is specified by the `operant_type` field.
     *
     * @note The `value` field is used for immediate values (8-bit or 16-bit).
     * @note The `label` field is used for label operands.
     * @note The `reg` field is used for register operands.
     */
    struct Argument
    {
        OperandType operant_type{OperandType::None};
        uint16_t value{0};
        std::string label;
        Reg reg{Reg::Invalid};
    };

    /**
     * @brief Instruction encoding structure
     *
     * This structure defines the encoding specifications for an assembly instruction.
     * It includes the opcode, size, operand signature, relocation requirement,
     * and immediate value offset.
     *
     * @note The `opcode` field represents the instruction's opcode.
     * @note The `size` field indicates the size of the instruction in bytes.
     * @note The `signature` field is a vector of operand types that define the instruction's operands.
     * @note The `needs_reloc` field indicates whether the instruction requires relocation.
     * @note The `imm_offset` field specifies the offset for immediate values within the instruction.
     */
    struct OpcodeSpecs
    {
        uint8_t opcode{0};
        uint8_t size{1};
        std::vector<OperandType> signature;
        bool needs_reloc{false};
        uint8_t imm_offset{1};
    };

    /**
     * @brief Key structure for instruction encoding lookup
     *
     * This structure serves as a key for looking up instruction encodings in a hash table.
     * It consists of the instruction mnemonic and its operand signature.
     *
     * @note The `mnemonic` field represents the instruction's mnemonic (e.g., "MOV", "ADD").
     * @note The `signature` field is a vector of operand types that define the instruction's operands.
     * @note The equality operator (`operator==`) is overridden to compare two keys based on their mnemonic and signature.
     */
    struct Key
    {
        std::string mnemonic;
        std::vector<OperandType> signature;

        bool operator==(const Key &other) const
        {
            return mnemonic == other.mnemonic && signature == other.signature;
        }
    };

    /**
     * @brief Hash function for Key structure
     * This struct provides a hash function for the Key structure, enabling its use in unordered containers.
     * The hash is computed based on the mnemonic and operand signature.
     * @note The hash function combines the hash of the mnemonic with the hashes of each operand type in the signature.
     */
    struct KeyHash
    {
        size_t operator()(const Key &key) const noexcept
        {
            size_t h = std::hash<std::string>{}(key.mnemonic);
            for (auto a : key.signature)
            {
                h = h * 131 + static_cast<size_t>(a);
            }
            return h;
        }
    };

    /**
     * @brief Instruction encoding table
     *
     * This class manages a table of instruction encodings, allowing for efficient lookup
     * of opcode specifications based on instruction mnemonics and operand signatures.
     * It also provides methods to retrieve specific opcodes for common instructions like MOV and LDI.
     *
     * @note The class is implemented as a singleton, with a private constructor and a static `get` method.
     * @note The `find` method allows for searching the table for a specific instruction encoding.
     * @note The class includes precomputed opcode tables for certain instructions to optimize performance.
     */
    class EncodeTable
    {
        EncodeTable();
        std::unordered_map<Key, OpcodeSpecs, KeyHash> table;

        uint8_t mov_[static_cast<int>(Reg::Invalid)][static_cast<int>(Reg::Invalid)]{};
        uint8_t ldi8_[static_cast<int>(Reg::Invalid)]{}, ldi16_[static_cast<int>(Reg::Invalid)]{};
        uint8_t ld16_[static_cast<int>(Reg::Invalid)]{}, st16_[static_cast<int>(Reg::Invalid)]{};

    public:
        static const EncodeTable &get();
        [[nodiscard]] auto find(const std::string &mnem, const std::vector<OperandType> &sig) const -> std::optional<OpcodeSpecs>;
        [[nodiscard]] uint8_t movOpcode(Reg dst, Reg src) const;
        [[nodiscard]] uint8_t ldiImm8Opcode(Reg r) const;
        [[nodiscard]] uint8_t ldiImm16Opcode(Reg r) const;
        [[nodiscard]] uint8_t ldAbs16Opcode(Reg r) const;
        [[nodiscard]] uint8_t stAbs16Opcode(Reg r) const;
    };
}