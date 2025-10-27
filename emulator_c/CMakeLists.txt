cmake_minimum_required(VERSION 3.15)
project(emulator_c)

set(CMAKE_CXX_STANDARD 20)

add_library(emulator_main SHARED src/emulator.cpp)
add_executable(emulate src/emulate.cpp)

target_include_directories(emulator_main PUBLIC ${CMAKE_SOURCE_DIR}/include)
target_link_libraries(emulate emulator_main)
