cmake_minimum_required(VERSION 3.30)
project(asm_toolchain VERSION 1.0.0 LANGUAGES CXX)
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

add_executable(cpua
        cli/asm_cli.cpp
        ${ASM_SOURCES}
        ${ASM_HEADERS}
)

add_executable(cpul
        cli/ld_cli.cpp
        ${ASM_SOURCES}
        ${ASM_HEADERS}
)

set_target_properties(cpua cpul
	PROPERTIES
	RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

target_include_directories(cpua PRIVATE
        src
        src/asm
        src/common
        src/object_generator
)

target_include_directories(cpul PRIVATE
        src
        src/asm
        src/common
        src/object_generator
)


include(GNUInstallDirs)
install(TARGETS cpua cpul
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

install(FILES ${ASM_HEADERS}
        DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/cpu816/asm
)

set(CPACK_PACKAGE_NAME "asm_toolchain")
set(CPACK_PACKAGE_VENDOR "CPU816 Project Authors")
set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
set(CPACK_GENERATOR "TGZ;ZIP")

include(CPack)

message(STATUS "Configuring asm_toolchain ${PROJECT_VERSION}")
message(STATUS "Build binaries will be placed in: ${CMAKE_BINARY_DIR}/bin")
message(STATUS "Install prefix: ${CMAKE_INSTALL_PREFIX} (override with: cmake --install build --prefix <dir>)")