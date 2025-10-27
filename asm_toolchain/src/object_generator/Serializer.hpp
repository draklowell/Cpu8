// This is a personal academic project. Dear PVS-Studio, please check it.
// PVS-Studio Static Code Analyzer for C, C++, C#, and Java: https://pvs-studio.com

#pragma once

#include "ObjectFormat.hpp"

#include <string>

namespace obj {

struct Serializer {
    static void writeToFile(const std::string& path, const ObjectFile& obj);
    static ObjectFile readFromFile(const std::string& path);
};

} // namespace obj