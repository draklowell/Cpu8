#pragma once

#include <string>
#include <variant>
#include <vector>
#include <../common/Util.hpp>
#include "InstrEncoding.hpp"

namespace asmx
{

    /**
     * @brief Token kinds for assembly parsing
     * This enum defines the different kinds of tokens that can be encountered while parsing assembly code.
     */
    enum class TokenKind
    {
        Ident,
        Number,
        LBracket,
        RBracket,
        Comma,
        Colon,
        Dot,
        NewLine,
        Eof
    };

    /**
     * @brief Token structure
     * This structure represents a token in the assembly code, including its kind, text, and
     * source location.
     */
    struct Token
    {
        TokenKind kind;
        std::string text;
        util::SourceLoc loc;
    };

    /**
     * @brief Label structure
     * This structure represents a label in assembly code, including its name, attributes, and source location.
     * @note Labels can have attributes that modify their behavior or provide additional information.
     */
    struct Label
    {
        std::string name;
        std::vector<std::string> attrs;
        util::SourceLoc loc;
    };

    /**
     * @brief Directive structure
     * This structure represents a directive in assembly code, including its name, arguments, and source location.
     */
    struct Directive
    {
        std::string name;
        std::vector<std::string> args;
        util::SourceLoc loc;
    };

    /**
     * @brief Instruction argument structure
     * This structure represents an argument for an assembly instruction, which can be a register,
     * immediate value, label, or memory address.
     */
    struct Instruction
    {
        std::string mnemonic;
        std::vector<Argument> args;
        util::SourceLoc loc;
    };

    /**
     * @brief Line variant type
     * This variant type can hold either a Label, Directive, or Instruction, representing a line in assembly code.
     */
    using Line = std::variant<Label, Directive, Instruction>;

    /**
     * @brief Parse result structure
     * This structure holds the result of parsing assembly code, which is a vector of lines.
     */
    struct ParseResult
    {
        std::vector<Line> lines;
    };

    /**
     * @brief Assembly parser class
     * This class provides methods to tokenize and parse assembly code into a structured format.
     */
    class Parser
    {
        /**
         * @brief
         */
        std::vector<Token> len(const std::string &text, const std::string &file);

        /**
         * @brief Parse tokens into structured lines
         * This method takes a vector of tokens and parses them into a structured format,
         * returning a ParseResult containing the parsed lines.
         * @param tokens A vector of tokens to be parsed.
         * @return A ParseResult containing the parsed lines.
         */
        ParseResult parse(const std::vector<Token> &tokens);

    public:
        /**
         * @brief Parse assembly file
         * This method reads an assembly file from the specified path, tokenizes its content,
         * and parses it into a structured format, returning a ParseResult.
         * @param path The file path of the assembly file to be parsed.
         * @return A ParseResult containing the parsed lines from the assembly file.
         */
        ParseResult parseFile(const std::string &path);
    };
}