// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com
#include "Serializer.hpp"

#include <array>
#include <cstdint>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace obj {
namespace {

constexpr std::array<const char*, 4> kSectionNames{".text", ".data", ".bss", ".rodata"};
constexpr char kMagic[] = {'C', '8', 'O',
                           '1'}; // C - CPU, 8 - 8/16 bit, 0 - output, 1 - version
constexpr uint16_t kCurrentVersion = 1;

class BinaryWriter {
  public:
    BinaryWriter(std::ostream& stream, std::string path)
        : out(stream), file_path(std::move(path)) {}

    void writeBytes(const void* data, const std::size_t size) const {
        out.write(static_cast<const char*>(data), static_cast<std::streamsize>(size));
        if (!out) {
            throw std::runtime_error("Failed to write to " + file_path);
        }
    }

    void writeU8(const uint8_t value) const { writeBytes(&value, sizeof(value)); }

    void writeU16LE(const uint16_t value) const {
        const char bytes[2] = {static_cast<char>(value & 0xFFU),
                               static_cast<char>((value >> 8U) & 0xFFU)};
        writeBytes(bytes, sizeof(bytes));
    }

    void writeU32LE(const uint32_t value) const {
        const char bytes[4] = {static_cast<char>(value & 0xFFU),
                               static_cast<char>((value >> 8U) & 0xFFU),
                               static_cast<char>((value >> 16U) & 0xFFU),
                               static_cast<char>((value >> 24U) & 0xFFU)};
        writeBytes(bytes, sizeof(bytes));
    }

    void writeI16LE(const int16_t value) const {
        writeU16LE(static_cast<uint16_t>(value));
    }

    void writeI32LE(const int32_t value) const {
        writeU32LE(static_cast<uint32_t>(value));
    }

    void writeMagic() const { writeBytes(kMagic, sizeof(kMagic)); }

  private:
    std::ostream& out;
    std::string file_path;
};

class BinaryReader {
  public:
    BinaryReader(std::istream& stream, std::string path)
        : in(stream), file_path(std::move(path)) {}

    void readBytes(void* data, const std::size_t size) const {
        in.read(static_cast<char*>(data), static_cast<std::streamsize>(size));
        if (in.gcount() != static_cast<std::streamsize>(size)) {
            throw std::runtime_error("Unexpected end of file while reading " +
                                     file_path);
        }
    }

    [[nodiscard]] uint8_t readU8() const {
        uint8_t value = 0;
        readBytes(&value, sizeof(value));
        return value;
    }

    [[nodiscard]] uint16_t readU16LE() const {
        const auto b0 = static_cast<uint16_t>(readU8());
        const auto b1 = static_cast<uint16_t>(readU8());
        return static_cast<uint16_t>((b1 << 8U) | b0);
    }

    [[nodiscard]] uint32_t readU32LE() const {
        const auto b0 = static_cast<uint32_t>(readU8());
        const auto b1 = static_cast<uint32_t>(readU8());
        const auto b2 = static_cast<uint32_t>(readU8());
        const auto b3 = static_cast<uint32_t>(readU8());
        return (b3 << 24U) | (b2 << 16U) | (b1 << 8U) | b0;
    }

    [[nodiscard]] int16_t readI16LE() const {
        return static_cast<int16_t>(readU16LE());
    }

    [[nodiscard]] int32_t readI32LE() const {
        return static_cast<int32_t>(readU32LE());
    }

    void verifyMagic() const {
        char magic[sizeof(kMagic)] = {};
        readBytes(magic, sizeof(magic));
        for (std::size_t i = 0; i < sizeof(kMagic); ++i) {
            if (magic[i] != kMagic[i]) {
                throw std::runtime_error("Invalid object file magic in " + file_path);
            }
        }
    }

  private:
    std::istream& in;
    std::string file_path;
};

std::string sectionNameFromIndex(uint8_t index) {
    if (index >= kSectionNames.size()) {
        throw std::runtime_error("Unsupported section index " + std::to_string(index));
    }
    return std::string{kSectionNames[index]};
}

} // namespace

void Serializer::writeToFile(const std::string& path, const ObjectFile& obj) {
    std::ofstream out(path, std::ios::binary);
    if (!out.is_open()) {
        throw std::runtime_error("Unable to open file for writing: " + path);
    }

    const BinaryWriter writer(out, path);

    if (obj.sections.size() > std::numeric_limits<uint16_t>::max()) {
        throw std::runtime_error("Too many sections to serialize");
    }
    if (obj.symbols.size() > std::numeric_limits<uint16_t>::max()) {
        throw std::runtime_error("Too many symbols to serialize");
    }
    if (obj.reloc_entries.size() > std::numeric_limits<uint16_t>::max()) {
        throw std::runtime_error("Too many relocations to serialize");
    }

    if (obj.sections.size() > kSectionNames.size()) {
        throw std::runtime_error("Unsupported number of sections: " +
                                 std::to_string(obj.sections.size()));
    }

    writer.writeMagic();
    writer.writeU16LE(kCurrentVersion);
    writer.writeU16LE(static_cast<uint16_t>(obj.sections.size()));
    writer.writeU16LE(static_cast<uint16_t>(obj.symbols.size()));
    writer.writeU16LE(static_cast<uint16_t>(obj.reloc_entries.size()));

    for (std::size_t i = 0; i < obj.sections.size(); ++i) {
        const auto& section = obj.sections[i];
        if (i >= kSectionNames.size()) {
            throw std::runtime_error("Unsupported section index " + std::to_string(i));
        }

        if (section.data.size() > std::numeric_limits<uint32_t>::max()) {
            throw std::runtime_error("Section data too large to serialize");
        }
        if (section.bss_size > std::numeric_limits<uint32_t>::max()) {
            throw std::runtime_error("Section BSS size too large to serialize");
        }

        writer.writeU8(static_cast<uint8_t>(i));
        writer.writeU8(section.flags);
        writer.writeU32LE(static_cast<uint32_t>(section.data.size()));
        writer.writeU32LE(section.bss_size);

        if (i == 2) {
            if (!section.data.empty()) {
                throw std::runtime_error(".bss section must not contain data");
            }
        } else if (!section.data.empty()) {
            writer.writeBytes(section.data.data(), section.data.size());
        }
    }

    for (const auto& symbol : obj.symbols) {
        if (symbol.name.size() > std::numeric_limits<uint16_t>::max()) {
            throw std::runtime_error("Symbol name too long to serialize");
        }

        if (symbol.section_index < std::numeric_limits<int16_t>::min() ||
            symbol.section_index > std::numeric_limits<int16_t>::max()) {
            throw std::runtime_error("Symbol section index out of range");
        }

        writer.writeU16LE(static_cast<uint16_t>(symbol.name.size()));
        if (!symbol.name.empty()) {
            writer.writeBytes(symbol.name.data(), symbol.name.size());
        }
        writer.writeI16LE(static_cast<int16_t>(symbol.section_index));
        writer.writeU32LE(symbol.value);
        writer.writeU8(symbol.bind);
    }

    for (const auto& reloc : obj.reloc_entries) {
        writer.writeU8(reloc.section_index);
        writer.writeU16LE(reloc.offset);
        writer.writeU8(static_cast<uint8_t>(reloc.type));
        writer.writeU16LE(reloc.symbol_index);
        writer.writeI32LE(static_cast<int32_t>(reloc.addend));
    }
}

ObjectFile Serializer::readFromFile(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in.is_open()) {
        throw std::runtime_error("Unable to open file for reading: " + path);
    }

    BinaryReader reader(in, path);
    reader.verifyMagic();
    const uint16_t version = reader.readU16LE();
    if (version != kCurrentVersion) {
        throw std::runtime_error("Unsupported object file version: " +
                                 std::to_string(version));
    }

    const uint16_t section_count = reader.readU16LE();
    const uint16_t symbol_count = reader.readU16LE();
    const uint16_t reloc_count = reader.readU16LE();

    if (section_count > kSectionNames.size()) {
        throw std::runtime_error("Unsupported section count in object file");
    }

    ObjectFile result;
    result.sections.reserve(section_count);

    for (uint16_t i = 0; i < section_count; ++i) {
        const uint8_t index = reader.readU8();
        if (index != i) {
            throw std::runtime_error("Section indices out of order in object file");
        }
        SectionDescription section;
        section.name = sectionNameFromIndex(index);
        section.flags = reader.readU8();
        const uint32_t size = reader.readU32LE();
        section.bss_size = reader.readU32LE();
        section.align = 1;

        if (index != 2) {
            section.data.resize(size);
            if (size > 0) {
                reader.readBytes(section.data.data(), size);
            }
        } else {
            if (size != 0) {
                throw std::runtime_error(".bss section must not contain data");
            }
        }

        result.sections.push_back(std::move(section));
    }

    result.symbols.reserve(symbol_count);
    for (uint16_t i = 0; i < symbol_count; ++i) {
        const uint16_t name_len = reader.readU16LE();
        std::string name;
        if (name_len > 0) {
            name.resize(name_len);
            reader.readBytes(name.data(), name_len);
        }

        const int16_t section_index = reader.readI16LE();
        const uint32_t value = reader.readU32LE();
        const uint8_t bind = reader.readU8();

        SymbolDescription symbol{name, static_cast<int32_t>(section_index), value,
                                 bind};
        result.symbols.push_back(std::move(symbol));
    }

    result.reloc_entries.reserve(reloc_count);
    for (uint16_t i = 0; i < reloc_count; ++i) {
        RelocEntry reloc{};
        reloc.section_index = reader.readU8();
        reloc.offset = reader.readU16LE();
        const uint8_t raw_type = reader.readU8();
        reloc.symbol_index = reader.readU16LE();
        const int32_t addend = reader.readI32LE();

        if (raw_type != static_cast<uint8_t>(RelocType::ABS16)) {
            throw std::runtime_error("Unsupported relocation type: " +
                                     std::to_string(raw_type));
        }
        reloc.type = static_cast<RelocType>(raw_type);

        if (addend < std::numeric_limits<int16_t>::min() ||
            addend > std::numeric_limits<int16_t>::max()) {
            throw std::runtime_error("Relocation addend out of range");
        }
        reloc.addend = static_cast<int16_t>(addend);

        result.reloc_entries.push_back(reloc);
    }

    return result;
}

} // namespace obj