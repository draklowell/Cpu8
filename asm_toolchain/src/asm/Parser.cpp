// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#include "Parser.hpp"

#include <cctype>
#include <fstream>
#include <iomanip>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <utility>

namespace asmx {
namespace {
[[nodiscard]] bool isIdentStart(const char ch) noexcept {
    return std::isalpha(static_cast<unsigned char>(ch)) != 0 || ch == '_';
}

[[nodiscard]] bool isIdentChar(const char ch) noexcept {
    return std::isalnum(static_cast<unsigned char>(ch)) != 0 || ch == '_' || ch == '.';
}

[[nodiscard]] util::SourceLoc makeLoc(const std::string& file, const uint32_t line,
                                      const uint32_t col) {
    return util::SourceLoc{file, util::SourcePos{line, col}};
}

[[nodiscard]] std::string toLower(std::string text) {
    for (char& ch : text) {
        ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
    }
    return text;
}

[[nodiscard]] bool isEightBitRegister(const Reg reg) noexcept {
    switch (reg) {
    case Reg::AC:
    case Reg::XH:
    case Reg::YL:
    case Reg::YH:
    case Reg::ZL:
    case Reg::ZH:
    case Reg::FR:
        return true;
    default:
        return false;
    }
}

[[nodiscard]] bool isSixteenBitRegister(const Reg reg) noexcept {
    switch (reg) {
    case Reg::X:
    case Reg::Y:
    case Reg::Z:
    case Reg::SP:
    case Reg::PC:
        return true;
    default:
        return false;
    }
}

[[nodiscard]] std::string registerName(const Reg reg) {
    switch (reg) {
    case Reg::AC:
        return "ac";
    case Reg::XH:
        return "xh";
    case Reg::YL:
        return "yl";
    case Reg::YH:
        return "yh";
    case Reg::ZL:
        return "zl";
    case Reg::ZH:
        return "zh";
    case Reg::FR:
        return "fr";
    case Reg::SP:
        return "sp";
    case Reg::PC:
        return "pc";
    case Reg::X:
        return "x";
    case Reg::Y:
        return "y";
    case Reg::Z:
        return "z";
    default:
        return "invalid";
    }
}

[[nodiscard]] std::string formatImmediateValue(const uint16_t value,
                                               const unsigned width) {
    std::ostringstream oss;
    oss << "0x" << std::uppercase << std::hex << std::setw(width) << std::setfill('0')
        << static_cast<unsigned>(value);
    return oss.str();
}

void adjustImmediateArgument(Instruction& instr, const size_t position,
                             const util::SourceLoc& loc) {
    if (position >= instr.args.size()) {
        return;
    }

    auto& arg = instr.args[position];
    if (arg.operant_type != OperandType::Imm16) {
        return;
    }

    const auto mnemonicLower = toLower(instr.mnemonic);
    bool       allowImm8     = false;
    bool       allowImm16    = false;

    const auto& entries = EncodeTable::get().entries();
    for (const auto& entry : entries) {
        if (entry.first.mnemonic != mnemonicLower) {
            continue;
        }
        if (position >= entry.first.signature.size()) {
            continue;
        }

        const auto expected = entry.first.signature[position];
        if (expected == OperandType::Imm8) {
            allowImm8 = true;
        } else if (expected == OperandType::Imm16) {
            allowImm16 = true;
        }
    }

    if (!allowImm8 && !allowImm16) {
        return;
    }

    const auto value = arg.value;

    if (!allowImm16) {
        if (value > 0xFF) {
            std::ostringstream msg;
            msg << "Immediate value " << formatImmediateValue(value, 2)
                << " does not fit into 8-bit operand of instruction '" << mnemonicLower
                << "'";
            throw util::Error(loc, msg.str());
        }
        arg.operant_type = OperandType::Imm8;
        return;
    }

    if (!allowImm8) {
        arg.operant_type = OperandType::Imm16;
        return;
    }

    if (mnemonicLower == "ldi" && position == 1 && !instr.args.empty() &&
        instr.args[0].operant_type == OperandType::Reg) {
        const auto targetReg = instr.args[0].reg;
        if (isEightBitRegister(targetReg)) {
            if (value > 0xFF) {
                std::ostringstream msg;
                msg << "Immediate value " << formatImmediateValue(value, 2)
                    << " does not fit into 8-bit register '" << registerName(targetReg)
                    << "'";
                throw util::Error(loc, msg.str());
            }
            arg.operant_type = OperandType::Imm8;
            return;
        }
        if (isSixteenBitRegister(targetReg)) {
            arg.operant_type = OperandType::Imm16;
            return;
        }
    }

    if (value <= 0xFF) {
        arg.operant_type = OperandType::Imm8;
    } else {
        arg.operant_type = OperandType::Imm16;
    }
}

void pushToken(std::vector<Token>& tokens, const TokenKind kind, std::string tokenText,
               const std::string& file, const uint32_t tokenLine,
               const uint32_t tokenCol) {
    tokens.push_back(
        Token{kind, std::move(tokenText), makeLoc(file, tokenLine, tokenCol)});
}

[[nodiscard]] bool isHorizontalWhitespace(const char ch) noexcept {
    return ch == ' ' || ch == '\t';
}

[[nodiscard]] bool tryConsumeLineMarker(const std::string& text, size_t& index,
                                        std::string& currentFile, uint32_t& line) {
    size_t       i    = index;
    const size_t size = text.size();

    while (i < size && isHorizontalWhitespace(text[i])) {
        ++i;
    }

    if (i >= size || text[i] != '#') {
        return false;
    }

    ++i; // skip '#'

    while (i < size && isHorizontalWhitespace(text[i])) {
        ++i;
    }

    if (i >= size || std::isdigit(static_cast<unsigned char>(text[i])) == 0) {
        throw util::Error(makeLoc(currentFile, line, 1),
                          "Invalid line marker: expected line number");
    }

    uint64_t parsedLine = 0;
    while (i < size && std::isdigit(static_cast<unsigned char>(text[i])) != 0) {
        parsedLine = parsedLine * 10 + static_cast<uint64_t>(text[i] - '0');
        if (parsedLine > std::numeric_limits<uint32_t>::max()) {
            throw util::Error(makeLoc(currentFile, line, 1),
                              "Line marker line number is out of range");
        }
        ++i;
    }

    while (i < size && isHorizontalWhitespace(text[i])) {
        ++i;
    }

    if (i >= size || text[i] != '"') {
        throw util::Error(makeLoc(currentFile, line, 1),
                          "Invalid line marker: expected file path");
    }

    ++i; // skip opening quote
    std::string path;
    while (i < size && text[i] != '"') {
        const char ch = text[i];
        if (ch == '\\') {
            if (i + 1 >= size) {
                throw util::Error(makeLoc(currentFile, line, 1),
                                  "Invalid line marker: unterminated escape sequence");
            }
            ++i;
            path.push_back(text[i]);
            ++i;
            continue;
        }
        if (ch == '\n' || ch == '\r') {
            throw util::Error(makeLoc(currentFile, line, 1),
                              "Invalid line marker: unterminated file path");
        }
        path.push_back(ch);
        ++i;
    }

    if (i >= size) {
        throw util::Error(makeLoc(currentFile, line, 1),
                          "Invalid line marker: unterminated file path");
    }

    ++i; // skip closing quote

    while (i < size && text[i] != '\n' && text[i] != '\r') {
        ++i;
    }

    if (i < size) {
        if (text[i] == '\r') {
            ++i;
            if (i < size && text[i] == '\n') {
                ++i;
            }
        } else if (text[i] == '\n') {
            ++i;
        }
    }

    currentFile = std::move(path);
    line        = static_cast<uint32_t>(parsedLine);
    index       = i;
    return true;
}
[[nodiscard]] uint32_t parseNumber(const Token& token) {
    const auto& text = token.text;
    if (text.empty()) {
        throw util::Error(token.loc, "Empty number literal");
    }

    const size_t text_size = text.size();
    uint32_t     value     = 0;
    if (text_size >= 2 && (text[0] == '0') && (text[1] == 'x' || text[1] == 'X')) {
        if (text_size == 2) {
            throw util::Error(token.loc, "Hex literal requires digits after 0x");
        }
        for (size_t i = 2; i < text_size; i++) {
            const char ch = text[i];
            value <<= 4;
            if (ch >= '0' && ch <= '9') {
                value += static_cast<uint32_t>(ch - '0');
            } else if (ch >= 'a' && ch <= 'f') {
                value += static_cast<uint32_t>(10 + ch - 'a');
            } else if (ch >= 'A' && ch <= 'F') {
                value += static_cast<uint32_t>(10 + ch - 'A');
            } else {
                throw util::Error(token.loc, "Invalid hexadecimal digit in literal");
            }
        }
    } else if (text_size >= 2 && (text[0] == '0') &&
               (text[1] == 'b' || text[1] == 'B')) {
        if (text_size == 2) {
            throw util::Error(token.loc, "Binary literal requires digits after 0b");
        }

        for (size_t i = 2; i < text_size; i++) {
            const char ch = text[i];
            value <<= 1;
            if (ch == '0') {
                continue;
            }
            if (ch == '1') {
                value++;
                continue;
            }
            throw util::Error(token.loc, "Invalid binary digit in literal");
        }
    } else {
        for (const char ch : text) {
            if (ch < '0' || ch > '9') {
                throw util::Error(token.loc, "Invalid decimal digit in literal");
            }
            value = value * 10 + static_cast<uint32_t>(ch - '0');
        }
    }
    return value;
}

[[nodiscard]] Reg parseRegisterName(const std::string& name) {
    const auto lower = toLower(name);

    if (lower == "ac") {
        return Reg::AC;
    }
    if (lower == "xh") {
        return Reg::XH;
    }
    if (lower == "yl") {
        return Reg::YL;
    }
    if (lower == "yh") {
        return Reg::YH;
    }
    if (lower == "zl") {
        return Reg::ZL;
    }
    if (lower == "zh") {
        return Reg::ZH;
    }
    if (lower == "fr") {
        return Reg::FR;
    }
    if (lower == "sp") {
        return Reg::SP;
    }
    if (lower == "pc") {
        return Reg::PC;
    }
    if (lower == "x") {
        return Reg::X;
    }
    if (lower == "y") {
        return Reg::Y;
    }
    if (lower == "z") {
        return Reg::Z;
    }
    return Reg::Invalid;
}

[[nodiscard]] Argument parseArgument(const std::vector<Token>& line, size_t& index) {
    if (index >= line.size()) {
        throw std::logic_error("parseArgument called out of range");
    }
    const Token& token = line[index];
    Argument     arg;

    if (token.kind == TokenKind::Ident) {
        if (const auto reg = parseRegisterName(token.text); reg != Reg::Invalid) {
            arg.operant_type = OperandType::Reg;
            arg.reg          = reg;
            ++index;
            return arg;
        }
        arg.operant_type = OperandType::Label;
        arg.label        = token.text;
        ++index;
        return arg;
    }

    if (token.kind == TokenKind::Number) {
        const auto value = parseNumber(token);
        if (value > 0xFFFF) {
            throw util::Error(token.loc, "Immediate value is out of range");
        }

        arg.value        = static_cast<uint16_t>(value);
        arg.operant_type = value <= 0xFF ? OperandType::Imm8 : OperandType::Imm16;
        ++index;
        return arg;
    }

    if (token.kind == TokenKind::LBracket) {
        const auto startLoc = token.loc;
        ++index;
        if (index >= line.size()) {
            throw util::Error(startLoc, "Expected expression inside memory reference");
        }

        const auto& inner    = line[index];
        bool        hasLabel = false;
        uint32_t    value    = 0;

        if (inner.kind == TokenKind::Number) {
            value = parseNumber(inner);
            if (value > 0xFFFF) {
                throw util::Error(inner.loc, "Memory reference value is out of range");
            }
            ++index;
        } else if (inner.kind == TokenKind::Ident) {
            if (const auto reg = parseRegisterName(inner.text); reg != Reg::Invalid) {
                throw util::Error(
                    inner.loc,
                    "Registers are not allowed inside absolute memory references");
            }
            arg.label = inner.text;
            hasLabel  = true;
            ++index;
        } else {
            throw util::Error(inner.loc,
                              "Expected number or label inside memory reference");
        }

        if (index >= line.size() || line[index].kind != TokenKind::RBracket) {
            throw util::Error(startLoc, "Expected closing bracket in memory reference");
        }
        ++index;

        arg.operant_type = OperandType::MemAbs16;
        if (!hasLabel) {
            arg.value = static_cast<uint16_t>(value);
        }
        return arg;
    }
    throw util::Error(token.loc, "Unexpected token in argument-_- Try again");
}
} // namespace
std::vector<Token> Parser::lex(const std::string& text, const std::string& file) {
    std::vector<Token> tokens;
    tokens.reserve(text.size() / 2);

    uint32_t    line        = 1;
    uint32_t    col         = 1;
    std::string currentFile = file;
    bool        atLineStart = true;

    size_t i = 0;
    while (i < text.size()) {
        if (atLineStart && tryConsumeLineMarker(text, i, currentFile, line)) {
            col         = 1;
            atLineStart = true;
            continue;
        }

        const char ch = text[i];
        if (ch == '\r') {
            const auto locCol = col;
            if (i + 1 < text.size() && text[i + 1] == '\n') {
                ++i;
            }
            ++i;
            pushToken(tokens, TokenKind::NewLine, "", currentFile, line, locCol);
            ++line;
            col         = 1;
            atLineStart = true;
            continue;
        }
        if (ch == '\n') {
            const auto locCol = col;
            ++i;
            pushToken(tokens, TokenKind::NewLine, "", currentFile, line, locCol);
            ++line;
            col         = 1;
            atLineStart = true;
            continue;
        }
        if (ch == ' ' || ch == '\t' || ch == '\v' || ch == '\f') {
            ++i;
            ++col;
            continue;
        }
        if (ch == ';') {
            atLineStart = false;
            while (i < text.size() && text[i] != '\n') {
                ++i;
            }
            continue;
        }
        if (ch == '/' && i + 1 < text.size() && text[i + 1] == '/') {
            atLineStart = false;
            i += 2;
            while (i < text.size() && text[i] != '\n') {
                ++i;
            }
            continue;
        }

        if (ch == '[') {
            pushToken(tokens, TokenKind::LBracket, "[", currentFile, line, col);
            ++i;
            ++col;
            atLineStart = false;
            continue;
        }

        if (ch == ']') {
            pushToken(tokens, TokenKind::RBracket, "]", currentFile, line, col);
            ++i;
            ++col;
            atLineStart = false;
            continue;
        }
        if (ch == ',') {
            pushToken(tokens, TokenKind::Comma, ",", currentFile, line, col);
            ++i;
            ++col;
            atLineStart = false;
            continue;
        }
        if (ch == ':') {
            pushToken(tokens, TokenKind::Colon, ":", currentFile, line, col);
            ++i;
            ++col;
            atLineStart = false;
            continue;
        }
        if (ch == '.') {
            pushToken(tokens, TokenKind::Dot, ".", currentFile, line, col);
            ++i;
            ++col;
            atLineStart = false;
            continue;
        }
        if (isIdentStart(ch)) {
            const auto   startCol = col;
            const size_t start    = i;
            ++i;
            ++col;
            while (i < text.size() && isIdentChar(text[i])) {
                ++i;
                ++col;
            }
            pushToken(tokens, TokenKind::Ident, text.substr(start, i - start),
                      currentFile, line, startCol);
            atLineStart = false;
            continue;
        }
        if (std::isdigit(static_cast<unsigned char>(ch)) != 0) {
            const auto   startCol = col;
            const size_t start    = i;
            ++i;
            ++col;
            while (i < text.size() &&
                   (std::isalnum(static_cast<unsigned char>(text[i]))) != 0) {
                ++i;
                ++col;
            }
            pushToken(tokens, TokenKind::Number, text.substr(start, i - start),
                      currentFile, line, startCol);
            atLineStart = false;
            continue;
        }
        throw util::Error(makeLoc(currentFile, line, col),
                          "Unexpected character in input");
    }
    pushToken(tokens, TokenKind::Eof, "", currentFile, line, col);
    return tokens;
}

ParseResult Parser::parse(const std::vector<Token>& tokens) {
    ParseResult result;

    size_t index = 0;
    while (index < tokens.size()) {
        const auto& tok = tokens[index];
        if (tok.kind == TokenKind::Eof) {
            break;
        }
        if (tok.kind == TokenKind::NewLine) {
            ++index;
            continue;
        }

        std::vector<Token> lineTokens;
        while (index < tokens.size() && tokens[index].kind != TokenKind::NewLine &&
               tokens[index].kind != TokenKind::Eof) {
            lineTokens.push_back(tokens[index]);
            ++index;
        }

        if (index < tokens.size() && tokens[index].kind == TokenKind::NewLine) {
            ++index;
        }
        if (lineTokens.empty()) {
            continue;
        }

        const Token& first = lineTokens.front();
        if (first.kind == TokenKind::Ident) {
            if (lineTokens.size() >= 2 && lineTokens[1].kind == TokenKind::Colon) {
                if (lineTokens.size() != 2) {
                    throw util::Error(lineTokens[2].loc,
                                      "Unexpected tokens after label definition");
                }
                Label label;
                label.name = first.text;
                label.loc  = first.loc;
                result.lines.emplace_back(std::move(label));
                continue;
            }
            Instruction instr;
            instr.mnemonic = first.text;
            instr.loc      = first.loc;

            size_t argIndex  = 1;
            bool   needComma = false;
            while (argIndex < lineTokens.size()) {
                const auto& current = lineTokens[argIndex];
                if (current.kind == TokenKind::Comma) {
                    if (!needComma) {
                        throw util::Error(current.loc,
                                          "Unexpected comma in argument list");
                    }
                    needComma = false;
                    ++argIndex;
                    continue;
                }
                if (needComma) {
                    throw util::Error(current.loc, "Missing comma between arguments");
                }
                instr.args.push_back(parseArgument(lineTokens, argIndex));
                const auto& consumedTok = lineTokens[argIndex - 1];
                adjustImmediateArgument(instr, instr.args.size() - 1, consumedTok.loc);
                needComma = true;
            }
            if (!instr.args.empty() && !needComma) {
                const auto& lastTok = lineTokens.back();
                throw util::Error(lastTok.loc, "Trailing comma in argument list");
            }
            result.lines.emplace_back(std::move(instr));
            continue;
        }
        if (first.kind == TokenKind::Dot) {
            if (lineTokens.size() < 2 || lineTokens[1].kind != TokenKind::Ident) {
                throw util::Error(first.loc, "Directive name expected after '.'");
            }
            Directive dir;
            dir.name = lineTokens[1].text;
            dir.loc  = first.loc;

            size_t argIndex    = 2;
            bool   expectValue = false;
            while (argIndex < lineTokens.size()) {
                const auto& cur = lineTokens[argIndex];
                if (cur.kind == TokenKind::Comma) {
                    if (!expectValue) {
                        throw util::Error(cur.loc,
                                          "Unexpected comma in directive arguments");
                    }
                    expectValue = false;
                    ++argIndex;
                    continue;
                }

                if (cur.kind == TokenKind::Number) {
                    auto value = parseNumber(cur);
                    dir.args.push_back(std::to_string(value));
                } else if (cur.kind == TokenKind::Ident) {
                    dir.args.push_back(cur.text);
                } else {
                    throw util::Error(cur.loc,
                                      "Unexpected token in directive arguments");
                }
                ++argIndex;
                expectValue = true;
            }
            if (!dir.args.empty() && !expectValue) {
                const auto& lastTok = lineTokens.back();
                throw util::Error(lastTok.loc, "Trailing comma in directive arguments");
            }
            result.lines.emplace_back(std::move(dir));
            continue;
        }
        throw util::Error(first.loc, "Unexpected token at start of line");
    }
    return result;
}

ParseResult Parser::parseText(const std::string& text, const std::string& file) {
    const std::vector<Token> tokens = lex(text, file);
    return parse(tokens);
}

ParseResult Parser::parseFile(const std::string& path) {
    std::ifstream input(path);
    if (!input) {
        throw std::runtime_error("Failed to open file: " + path);
    }

    std::ostringstream ss;
    ss << input.rdbuf();

    const std::vector<Token> tokens = lex(ss.str(), path);
    return parse(tokens);
}

} // namespace asmx
