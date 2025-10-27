# Installation Guide

## Prerequisites

- CMake 3.xx

### 1. Configuration without installation

```bash
cd asm_toolchain
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

**Створює бінарники в**

```bash
build/bin/cpua
build/bin/cpul
```

**Використання**

```bash
./build/bin/cpua --help
./build/bin/cpul --help
```

### 2. Configuration with installation

```bash
cmake --install build --prefix "$HOME/.local"
```

**Додайте до PATH якщо потрібно (macOS/Linux):**

```bash
export PATH="$HOME/.local/bin:$PATH"
```

**Перевірка:**

```bash
which cpua
which cpul
cpua --help
cpul --help
```

### 3. Uninstallation

```bash
cat build/install_manifest.txt
xargs rm -vf < build/install_manifest.txt
```
