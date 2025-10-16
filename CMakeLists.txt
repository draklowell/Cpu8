cmake_minimum_required(VERSION 3.20)
project(Cpu8)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(asm_toolchain/src/asm)
include_directories(asm_toolchain/src/binary_generator)
include_directories(asm_toolchain/src/common)
include_directories(asm_toolchain/src/link)
include_directories(asm_toolchain/src/object_generator)

add_executable(Cpu8
        asm_toolchain/src/asm/Assembler.cpp
        asm_toolchain/src/asm/Assembler.hpp
        asm_toolchain/src/asm/Directives.cpp
        asm_toolchain/src/asm/Directives.hpp
        asm_toolchain/src/asm/InstrEncoding.cpp
        asm_toolchain/src/asm/InstrEncoding.hpp
        asm_toolchain/src/asm/Parser.cpp
        asm_toolchain/src/asm/Parser.hpp
        asm_toolchain/src/asm/Pass1.cpp
        asm_toolchain/src/asm/Pass1.hpp
        asm_toolchain/src/asm/Pass2.cpp
        asm_toolchain/src/asm/Pass2.hpp
        asm_toolchain/src/asm/SymbolTable.cpp
        asm_toolchain/src/asm/SymbolTable.hpp
        asm_toolchain/src/binary_generator/ImageWriter.cpp
        asm_toolchain/src/binary_generator/ImageWriter.hpp
        asm_toolchain/src/common/ByteBuffer.cpp
        asm_toolchain/src/common/ByteBuffer.hpp
        asm_toolchain/src/common/Logger.cpp
        asm_toolchain/src/common/Logger.hpp
        asm_toolchain/src/common/Util.cpp
        asm_toolchain/src/common/Util.hpp
        asm_toolchain/src/link/Linker.cpp
        asm_toolchain/src/link/Linker.hpp
        asm_toolchain/src/link/RelocResolver.cpp
        asm_toolchain/src/link/RelocResolver.hpp
        asm_toolchain/src/link/SectionMerger.cpp
        asm_toolchain/src/link/SectionMerger.hpp
        asm_toolchain/src/object_generator/ObjectFormat.cpp
        asm_toolchain/src/object_generator/ObjectFormat.hpp
        asm_toolchain/src/object_generator/Relocation.cpp
        asm_toolchain/src/object_generator/Relocation.hpp
        asm_toolchain/src/object_generator/Serializer.cpp
        asm_toolchain/src/object_generator/Serializer.hpp
        asm_toolchain/src/asm_cli.cpp
        asm_toolchain/src/ld_cli.cpp
        asm_toolchain/main.cpp)