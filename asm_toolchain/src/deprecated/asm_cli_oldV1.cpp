// This is a personal academic project. Dear PVS-Studio, please check it.
// Simple single-file assembler frontend (two-pass -> flat binary)

#include "asm/Assembler.hpp"
#include "asm/Directives.hpp"
#include "asm/Parser.hpp"
#include "asm/Pass1.hpp"
#include "object_generator/ObjectFormat.hpp"

#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace asmx;

static std::string readFile(const std::string& path) {
    std::ifstream ifs(path);
    if (!ifs.is_open()) {
        throw std::runtime_error("Cannot open file: " + path);
    }
    std::ostringstream ss;
    ss << ifs.rdbuf();
    return ss.str();
}

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "Usage: asm_cli <input.asm> <output.bin>\n";
        return 1;
    }

    const std::string inputPath = argv[1];
    const std::string outputPath = argv[2];

    try {
        // 1) Read source
        std::string source = readFile(inputPath);

        // 2) Parse
        ParseResult parsed = Parser::parseText(source, inputPath);

        // 3) Pass 1 — collect symbols and sections
        Pass1State state;
        SectionsScratch scratch;
        Assembler::pass1(parsed, state, scratch);

        // 4) Pass 2 — generate object file
        obj::ObjectFile objectFile;
        Assembler::pass2(parsed, state, scratch, objectFile);

        // 5) We only support single-file ROM output (no linker)
        //    => relocations not allowed
        if (!objectFile.reloc_entries.empty()) {
            std::cerr << "Error: relocations found, linking required.\n";
            return 1;
        }

        // 6) Build flat ROM: .text + .rodata
        const auto& text = objectFile.sections[0];
        const auto& rodata = objectFile.sections[3];
        std::vector<uint8_t> rom;
        rom.insert(rom.end(), text.data.begin(), text.data.end());
        rom.insert(rom.end(), rodata.data.begin(), rodata.data.end());

        // 7) Optionally pad ROM to 16 KiB (if your CPU ROM = 16 KiB)
        const size_t ROM_SIZE = 16 * 1024;
        if (rom.size() > ROM_SIZE) {
            std::cerr << "Error: ROM image exceeds 16 KiB!\n";
            return 1;
        }
        rom.resize(ROM_SIZE, 0xFF); // pad with 0xFF (typical empty ROM value)

        // 8) Write binary file
        std::ofstream ofs(outputPath, std::ios::binary);
        if (!ofs.is_open()) {
            throw std::runtime_error("Cannot open output: " + outputPath);
        }
        ofs.write(reinterpret_cast<const char*>(rom.data()),
                  static_cast<std::streamsize>(rom.size()));
        ofs.close();

        std::cout << "Assembled successfully: " << outputPath << "\n";
        std::cout << "   .text size: " << text.data.size()
                  << " bytes, .rodata size: " << rodata.data.size() << " bytes\n";
        std::cout << "   Total ROM image: " << rom.size() << " bytes\n";

        return 0;

    } catch (const util::Error& err) {
        std::cerr << "Assembler error at " << err.loc.file << ":" << err.loc.pos.line
                  << ":" << err.loc.pos.col << " -> " << err.what() << "\n";
        return 1;
    } catch (const std::exception& e) {
        std::cerr << "Fatal: " << e.what() << "\n";
        return 1;
    }
}
