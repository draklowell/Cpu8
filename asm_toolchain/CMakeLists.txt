cmake_minimum_required(VERSION 3.16)
project(asm_toolchain CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(asm_cpu
        asm_cli.cpp
        ld_cli.cpp

        src/asm/Assembler.cpp
        src/asm/Directives.cpp
        src/asm/InstrEncoding.cpp
        src/asm/Parser.cpp
        src/asm/Pass1.cpp
        src/asm/Pass2.cpp
        src/asm/SymbolTable.cpp

        src/binary_generator/ImageWriter.cpp
        src/common/Util.cpp
        src/link/Linker.cpp
        src/link/RelocResolver.cpp
        src/link/SectionMerger.cpp
        src/object_generator/Relocation.cpp
        src/object_generator/Serializer.cpp
        src/asm/RegisterDependent.hpp
)

target_include_directories(asm_cpu PRIVATE
        src
        src/asm
        src/common
        src/object_generator
)
