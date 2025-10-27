#include "emulator.hpp"
#include <iostream>
#include <string>

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0]
                  << " <instruction_table.csv> <program.bin> [steps] [verbosity]\n"
                  << "Example:\n"
                  << "  " << argv[0]
                  << " table.csv emu.bin 52 TRACE\n"
                  << "Notes:\n"
                  << "  - Steps default = -1, Verbosity default = TRACE"
                  << "  - If steps = -1, runs until HALT.\n"
                  << "  - Verbosity options: SILENT, STEP, TRACE.\n";
        return 1;
    }

    const std::string tablePath = argv[1];
    const std::string programPath = argv[2];
    const int steps = (argc >= 4) ? std::stoi(argv[3]) : -1;
    const std::string verbosityStr = (argc >= 5) ? argv[4] : "TRACE";

    DebugVerbosity verbosity;
    if (verbosityStr == "SILENT") verbosity = DebugVerbosity::SILENT;
    else if (verbosityStr == "STEP") verbosity = DebugVerbosity::STEP;
    else if (verbosityStr == "TRACE") verbosity = DebugVerbosity::TRACE;
    else {
        std::cerr << "Unknown verbosity: " << verbosityStr
                  << " (use SILENT, STEP, or TRACE)\n";
        return 1;
    }

    try {
        CPU cpu{tablePath};
        cpu.loadProgramFromFile(programPath);
        cpu.run(steps, verbosity);
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << '\n';
        return 1;
    }

    return 0;
}
