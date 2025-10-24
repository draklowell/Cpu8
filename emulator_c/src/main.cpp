#include "emulator.hpp"

#include <iostream>

int main(int argc, char** argv) {

    CPU cpu{"/home/luka/study/pok/Cpu8/emulator_c/instructions/table.csv"};
    cpu.loadProgramFromFile("/home/luka/study/pok/Cpu8/emulator_c/code_programs/emu.bin");
    cpu.run(52, DebugVerbosity::TRACE);
    return 0;
}