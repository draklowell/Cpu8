#include "asm/Assembler.hpp"
#include "asm/Directives.hpp"
#include "asm/Parser.hpp"
#include "asm/Pass1.hpp"
#include "binary_generator/ImageWriter.hpp"
#include "common/Util.hpp"
#include "object_generator/Serializer.hpp"

#include <array>
#include <cstdint>
#include <cstdio>
#include <exception>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

void printUsage() {
    std::cout << "Usage: asm_cli [options] <input.asm> [output]\n"
                 "Options:\n"
                 "  -o <file>         Output path (bin or obj)\n"
                 "  --object          Emit relocatable object (.o)\n"
                 "  --no-preprocess   Do not run external preprocessor\n"
                 "  --verbose         Print section size summary\n"
                 "  --help            Show this help message\n";
}

std::string runPreprocessor(const std::string& path) {
    std::string command = "cpp -E \"" + path + "\"";
    FILE* pipe = popen(command.c_str(), "r");
    if (!pipe) {
        throw std::runtime_error("Failed to invoke preprocessor: cpp");
    }

    std::string output;
    std::array<char, 4096> buffer{};
    std::size_t bytes_read = 0;
    while ((bytes_read = std::fread(buffer.data(), 1, buffer.size(), pipe)) > 0U) {
        output.append(buffer.data(), bytes_read);
    }

    const int status = pclose(pipe);
    if (status != 0) {
        throw std::runtime_error("Preprocessor failed for file: " + path);
    }

    return output;
}

std::string determineOutputPath(const std::vector<std::string>& positional,
                                const std::string& explicitOutput) {
    if (!explicitOutput.empty()) {
        return explicitOutput;
    }
    if (positional.size() >= 2) {
        return positional[1];
    }
    return std::string();
}

} // namespace

int main(int argc, char** argv) {
    bool emitObject = false;
    bool runCpp = true;
    bool verbose = false;
    std::string outputPath;
    std::vector<std::string> positional;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--help") {
            printUsage();
            return 0;
        } else if (arg == "--object") {
            emitObject = true;
        } else if (arg == "--no-preprocess") {
            runCpp = false;
        } else if (arg == "--verbose") {
            verbose = true;
        } else if (arg == "-o") {
            if (i + 1 >= argc) {
                std::cerr << "Missing argument after -o\n";
                printUsage();
                return 1;
            }
            outputPath = argv[++i];
        } else if (!arg.empty() && arg[0] == '-' && arg != "-") {
            std::cerr << "Unknown option: " << arg << "\n";
            printUsage();
            return 1;
        } else {
            positional.push_back(arg);
        }
    }

    if (positional.empty()) {
        std::cerr << "Input file is required\n";
        printUsage();
        return 1;
    }

    const std::string inputPath = positional.front();
    outputPath = determineOutputPath(positional, outputPath);

    if (outputPath.empty()) {
        std::cerr << "Output file is required\n";
        printUsage();
        return 1;
    }

    try {
        asmx::ParseResult parsed;
        if (runCpp) {
            const std::string preprocessed = runPreprocessor(inputPath);
            parsed = asmx::Parser::parseText(preprocessed, inputPath);
        } else {
            parsed = asmx::Parser::parseFile(inputPath);
        }

        asmx::Pass1State state;
        asmx::SectionsScratch scratch;
        asmx::Assembler::pass1(parsed, state, scratch);

        obj::ObjectFile object;
        asmx::Assembler::pass2(parsed, state, scratch, object);

        const auto textSize =
            object.sections.size() > 0 ? object.sections[0].data.size() : 0U;
        const auto rodataSize =
            object.sections.size() > 3 ? object.sections[3].data.size() : 0U;

        if (emitObject) {
            obj::Serializer::writeToFile(outputPath, object);
            std::cout << "Assembled successfully: " << outputPath << "\n";
            if (verbose) {
                std::cout << "   .text size: " << textSize
                          << " bytes, .rodata size: " << rodataSize << " bytes\n";
                std::cout << "   Total ROM image: " << (textSize + rodataSize)
                          << " bytes\n";
            }
            return 0;
        }

        if (!object.reloc_entries.empty()) {
            throw std::runtime_error(
                "Relocations present; use the linker or --object output");
        }

        constexpr uint32_t kRomSize = 16U * 1024U;
        constexpr uint8_t kRomFill = 0xFFU;

        const auto& textSection = object.sections[0];
        const auto& rodataSection = object.sections[3];
        std::vector<uint8_t> rom = binout::ImageWriter::makeFlatROM(
            textSection.data, rodataSection.data, kRomSize, kRomFill);
        binout::ImageWriter::writeBIN(outputPath, rom);

        std::cout << "Assembled successfully: " << outputPath << "\n";
        if (verbose) {
            std::cout << "   .text size: " << textSize
                      << " bytes, .rodata size: " << rodataSize << " bytes\n";
            std::cout << "   Total ROM image: " << rom.size() << " bytes\n";
        }

        return 0;
    } catch (const util::Error& err) {
        std::cerr << "Assembler error at " << err.loc.file << ':' << err.loc.pos.line
                  << ':' << err.loc.pos.col << " -> " << err.what() << "\n";
        return 1;
    } catch (const std::runtime_error& ex) {
        std::cerr << "Error: " << ex.what() << "\n";
        return 1;
    } catch (const std::exception& ex) {
        std::cerr << "Unexpected failure: " << ex.what() << "\n";
        return 1;
    }
}