#include "emulator.hpp"

#include <iostream>

int main(int argc, char** argv) {
    if (argc < 3) {
        throw std::runtime_error("Wrong number of arguments.");
        return 1;
    }
    CPU cpu{argv[1]};
    std::cout << cpu.getStatusString() << std::endl;
    cpu.loadProgramFromFile(argv[2]);
    std::cout << cpu.getStatusString() << std::endl;
    cpu.run(20);
    cpu.clear_memory();
    cpu.reset();
    return 0;
}