cmake_minimum_required(VERSION 3.16)
project(asm_toolchain CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(ASM_SOURCES
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

        src/object_generator/Serializer.cpp
)

set(ASM_HEADERS
        src/asm/RegisterDependent.hpp
)

add_executable(asm_cpu
        asm_cli.cpp
        ${ASM_SOURCES}
        ${ASM_HEADERS}
)

add_executable(ld_cpu
        ld_cli.cpp
        ${ASM_SOURCES}
        ${ASM_HEADERS}
)

target_include_directories(asm_cpu PRIVATE
        src
        src/asm
        src/common
        src/object_generator
)

target_include_directories(ld_cpu PRIVATE
        src
        src/asm
        src/common
        src/object_generator
)
