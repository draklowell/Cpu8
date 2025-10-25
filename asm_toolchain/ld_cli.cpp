#include "binary_generator/ImageWriter.hpp"
#include "link/Linker.hpp"
#include "object_generator/Serializer.hpp"

#include <cstdint>
#include <exception>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

void printUsage() {
    std::cerr << "Usage: ld <out.bin> <in1.o> <in2.o> ..."
                 " [--map <file.map>] [--entry <sym>]"
                 " [--rom-size N] [--rom-fill 0xFF]\n";
}

uint32_t parseUint32(const std::string& value) {
    size_t pos = 0;
    uint32_t result = 0;
    try {
        unsigned long parsed = std::stoul(value, &pos, 0);
        if (pos != value.size()) {
            throw std::runtime_error("Invalid numeric value: '" + value + "'");
        }
        if (parsed > 0xFFFFFFFFUL) {
            throw std::runtime_error("Numeric value out of range: '" + value + "'");
        }
        result = static_cast<uint32_t>(parsed);
    } catch (const std::invalid_argument&) {
        throw std::runtime_error("Invalid numeric value: '" + value + "'");
    } catch (const std::out_of_range&) {
        throw std::runtime_error("Numeric value out of range: '" + value + "'");
    }
    return result;
}

uint8_t parseUint8(const std::string& value) {
    uint32_t parsed = parseUint32(value);
    if (parsed > 0xFFU) {
        throw std::runtime_error("ROM fill byte out of range (0-255): '" + value + "'");
    }
    return static_cast<uint8_t>(parsed);
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        printUsage();
        return 1;
    }

    const std::string output_path = argv[1];

    link::LinkOptions options;
    options.rom_size = 16U * 1024U;
    options.rom_fill = 0xFFU;
    options.entry_symbol = "main";
    options.mapfile = false;

    std::vector<std::string> input_paths;

    for (int i = 2; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--map") {
            if (i + 1 >= argc) {
                std::cerr << "Missing argument for --map\n";
                printUsage();
                return 1;
            }
            options.mapfile = true;
            options.map_path = argv[++i];
        } else if (arg == "--entry") {
            if (i + 1 >= argc) {
                std::cerr << "Missing argument for --entry\n";
                printUsage();
                return 1;
            }
            options.entry_symbol = argv[++i];
        } else if (arg == "--rom-size") {
            if (i + 1 >= argc) {
                std::cerr << "Missing argument for --rom-size\n";
                printUsage();
                return 1;
            }
            try {
                options.rom_size = parseUint32(argv[++i]);
            } catch (const std::exception& ex) {
                std::cerr << ex.what() << "\n";
                return 1;
            }
        } else if (arg == "--rom-fill") {
            if (i + 1 >= argc) {
                std::cerr << "Missing argument for --rom-fill\n";
                printUsage();
                return 1;
            }
            try {
                options.rom_fill = parseUint8(argv[++i]);
            } catch (const std::exception& ex) {
                std::cerr << ex.what() << "\n";
                return 1;
            }
        } else if (!arg.empty() && arg[0] == '-') {
            std::cerr << "Unknown option: " << arg << "\n";
            printUsage();
            return 1;
        } else {
            input_paths.push_back(std::move(arg));
        }
    }

    if (input_paths.empty()) {
        std::cerr << "No input object files provided\n";
        printUsage();
        return 1;
    }

    try {
        std::vector<obj::ObjectFile> objects;
        objects.reserve(input_paths.size());
        for (const auto& path : input_paths) {
            objects.push_back(obj::Serializer::readFromFile(path));
        }

        const link::LinkedImage image = link::Linker::link(objects, options);

        binout::ImageWriter::writeBIN(output_path, image.rom);

        if (options.mapfile) {
            // Map file is already written by the linker using options.map_path
        }

        std::cout << "Linked OK: " << output_path << "\n";
        std::cout << " .text=" << image.text_size << " bytes"
                  << " .rodata=" << image.rodata_size << " bytes"
                  << " .bss=" << image.bss_size << " bytes"
                  << " (ROM=" << image.rom.size() << " bytes)\n";

        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "Link error: " << ex.what() << "\n";
        return 1;
    }
}