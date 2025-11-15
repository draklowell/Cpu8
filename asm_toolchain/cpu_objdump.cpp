#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

static void fail(const std::string& message) {
    std::cerr << "Error: " << message << std::endl;
    std::exit(1);
}

static uint8_t readU8(const std::vector<uint8_t>& data, size_t& pos) {
    if (pos + 1 > data.size()) {
        fail("Unexpected end of file while reading u8");
    }
    return data[pos++];
}

static uint16_t readU16(const std::vector<uint8_t>& data, size_t& pos) {
    if (pos + 2 > data.size()) {
        fail("Unexpected end of file while reading u16");
    }
    uint16_t value =
        static_cast<uint16_t>(data[pos]) | static_cast<uint16_t>(data[pos + 1]) << 8U;
    pos += 2;
    return value;
}

static uint32_t readU32(const std::vector<uint8_t>& data, size_t& pos) {
    if (pos + 4 > data.size()) {
        fail("Unexpected end of file while reading u32");
    }
    uint32_t value = static_cast<uint32_t>(data[pos]) |
                     (static_cast<uint32_t>(data[pos + 1]) << 8U) |
                     (static_cast<uint32_t>(data[pos + 2]) << 16U) |
                     (static_cast<uint32_t>(data[pos + 3]) << 24U);
    pos += 4;
    return value;
}

static int16_t readI16(const std::vector<uint8_t>& data, size_t& pos) {
    return static_cast<int16_t>(readU16(data, pos));
}

static int32_t readI32(const std::vector<uint8_t>& data, size_t& pos) {
    return static_cast<int32_t>(readU32(data, pos));
}

struct SectionInfo {
    std::string name;
    uint8_t flags;
    uint32_t dataSize;
    uint32_t bssSize;
    size_t fileOffset;
    bool hasData;
};

struct SymbolInfo {
    std::string name;
    int16_t sectionIndex;
    uint32_t value;
    uint8_t bind;
};

// Relocation entry
// addend - константа, яка додається до адреси символу під час релокації.
// Наприклад, для доступу до елемента масиву: symbol+offset
struct RelocInfo {
    uint8_t sectionIndex; // В якій секції знаходиться місце для патчінгу
    uint16_t offset;      // Зміщення в секції, де потрібно підставити адресу
    uint8_t type;         // Тип релокації (ABS16, тощо)
    uint16_t symbolIndex; // Індекс символу в таблиці символів
    int32_t addend;       // Додаткове зміщення відносно адреси символу
};

static const char* sectionNameFromIndex(uint8_t index) {
    static const char* kNames[] = {".text", ".data", ".bss", ".rodata"};
    const size_t count = sizeof(kNames) / sizeof(kNames[0]);
    if (index >= count) {
        fail("Unsupported section index " + std::to_string(index));
    }
    return kNames[index];
}

static const char* bindingName(uint8_t bind) {
    switch (bind) {
    case 0:
        return "LOCAL";
    case 1:
        return "GLOBAL";
    case 2:
        return "WEAK";
    default:
        return "UNKNOWN";
    }
}

static const char* relocTypeName(uint8_t type) {
    switch (type) {
    case 0:
        return "ABS16";
    default:
        return "UNKNOWN";
    }
}

static void printHexField(uint32_t value, int width) {
    std::cout << std::setw(width) << std::showbase << std::hex << value;
    std::cout << std::dec << std::noshowbase;
}

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "Usage: cpu8-objdump <object-file>" << std::endl;
        return 1;
    }

    const char* path = argv[1];
    std::ifstream input(path, std::ios::binary);
    if (!input) {
        std::cerr << "Failed to open file: " << path << std::endl;
        return 1;
    }

    input.seekg(0, std::ios::end);
    std::streampos fileSize = input.tellg();
    if (fileSize < 12) {
        fail("File too small to contain object header");
    }
    input.seekg(0, std::ios::beg);

    std::vector<uint8_t> data(static_cast<size_t>(fileSize));
    if (!input.read(reinterpret_cast<char*>(data.data()), data.size())) {
        fail("Failed to read file contents");
    }

    size_t pos = 0;
    const char expectedMagic[4] = {'C', '8', 'O', '1'};
    for (int i = 0; i < 4; ++i) {
        if (data[pos + i] != static_cast<uint8_t>(expectedMagic[i])) {
            fail("Invalid magic number in object file");
        }
    }
    pos += 4;

    const uint16_t version = readU16(data, pos);
    if (version != 1) {
        fail("Unsupported version: " + std::to_string(version));
    }
    const uint16_t sectionCount = readU16(data, pos);
    const uint16_t symbolCount = readU16(data, pos);
    const uint16_t relocCount = readU16(data, pos);

    std::vector<SectionInfo> sections;
    sections.reserve(sectionCount);
    for (uint16_t i = 0; i < sectionCount; ++i) {
        const uint8_t index = readU8(data, pos);
        if (index != i) {
            fail("Section indices out of order: expected " + std::to_string(i) +
                 ", found " + std::to_string(index));
        }
        SectionInfo info{};
        info.name = sectionNameFromIndex(index);
        info.flags = readU8(data, pos);
        info.dataSize = readU32(data, pos);
        info.bssSize = readU32(data, pos);
        info.hasData = info.dataSize > 0;
        if (info.hasData) {
            if (pos + info.dataSize > data.size()) {
                fail("Section data exceeds file size for section " + std::to_string(i));
            }
            info.fileOffset = pos;
            pos += info.dataSize;
        } else {
            info.fileOffset = 0;
        }
        sections.push_back(info);
    }

    std::vector<SymbolInfo> symbols;
    symbols.reserve(symbolCount);
    for (uint16_t i = 0; i < symbolCount; ++i) {
        const uint16_t nameLen = readU16(data, pos);
        if (pos + nameLen > data.size()) {
            fail("Symbol name extends past end of file");
        }
        std::string name;
        if (nameLen > 0) {
            name.assign(reinterpret_cast<const char*>(&data[pos]), nameLen);
            pos += nameLen;
        }
        const int16_t sectionIndex = readI16(data, pos);
        const uint32_t value = readU32(data, pos);
        const uint8_t bind = readU8(data, pos);
        symbols.push_back(SymbolInfo{name, sectionIndex, value, bind});
    }

    std::vector<RelocInfo> relocs;
    relocs.reserve(relocCount);
    for (uint16_t i = 0; i < relocCount; ++i) {
        RelocInfo info{};
        info.sectionIndex = readU8(data, pos);
        info.offset = readU16(data, pos);
        info.type = readU8(data, pos);
        info.symbolIndex = readU16(data, pos);
        info.addend = readI32(data, pos);
        if (info.sectionIndex >= sections.size()) {
            fail("Relocation references invalid section index: " +
                 std::to_string(info.sectionIndex));
        }
        if (info.symbolIndex >= symbols.size()) {
            fail("Relocation references invalid symbol index: " +
                 std::to_string(info.symbolIndex));
        }
        if (info.addend < -32768 || info.addend > 32767) {
            fail("Relocation addend out of range for entry " + std::to_string(i));
        }
        relocs.push_back(info);
    }

    std::cout << "Object Header:\n";
    std::cout << "  Magic: C8O1\n";
    std::cout << "  Version: " << version << "\n";
    std::cout << "  Section count: " << sectionCount << "\n";
    std::cout << "  Symbol count: " << symbolCount << "\n";
    std::cout << "  Relocation count: " << relocCount << "\n";

    std::cout << "\nSections:\n";
    std::cout << "  [Index] " << std::left << std::setw(12) << "Name" << std::right
              << std::setw(10) << "Flags" << std::setw(12) << "DataSize"
              << std::setw(12) << "BSSSize" << std::setw(12) << "FileOff" << "\n";
    for (size_t i = 0; i < sections.size(); ++i) {
        const SectionInfo& sec = sections[i];
        std::cout << "  [" << std::right << std::setw(5) << i << "] ";
        std::cout << std::left << std::setw(12) << sec.name << std::right;
        printHexField(sec.flags, 10);
        std::cout << std::setw(12) << sec.dataSize;
        std::cout << std::setw(12) << sec.bssSize;
        if (sec.hasData) {
            std::cout << std::setw(12) << sec.fileOffset;
        } else {
            std::cout << std::setw(12) << "-";
        }
        std::cout << "\n";
    }

    std::cout << "\nSymbols:\n";
    std::cout << "  [Index] " << std::left << std::setw(20) << "Name" << std::right
              << std::setw(12) << "Section" << std::setw(12) << "Value" << std::setw(12)
              << "Bind" << "\n";
    for (size_t i = 0; i < symbols.size(); ++i) {
        const SymbolInfo& sym = symbols[i];
        std::cout << "  [" << std::right << std::setw(5) << i << "] ";
        std::cout << std::left << std::setw(20) << sym.name << std::right;
        std::cout << std::setw(12) << static_cast<int>(sym.sectionIndex);
        std::cout << std::setw(12) << sym.value;
        std::cout << std::setw(12) << bindingName(sym.bind) << "\n";
    }

    std::cout << "\nRelocations:\n";
    std::cout << "  [Index] " << std::right << std::setw(12) << "Section"
              << std::setw(12) << "Offset" << std::setw(12) << "Type" << std::setw(12)
              << "Symbol" << std::setw(12) << "Addend"
              << "  " << std::left << "Name" << "\n";
    for (size_t i = 0; i < relocs.size(); ++i) {
        const RelocInfo& rel = relocs[i];
        const SymbolInfo& sym = symbols[rel.symbolIndex];
        std::cout << "  [" << std::right << std::setw(5) << i << "] ";
        std::cout << std::setw(12) << static_cast<int>(rel.sectionIndex);
        std::cout << std::setw(12) << rel.offset;
        std::cout << std::setw(12) << relocTypeName(rel.type);
        std::cout << std::setw(12) << rel.symbolIndex;
        std::cout << std::setw(12) << rel.addend;
        std::cout << "  " << std::left << sym.name << "\n";
    }

    return 0;
}