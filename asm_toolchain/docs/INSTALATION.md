# Installation Guide

## Prerequisites

- CMake 3.xx

### 1. Build without installation

```bash
cd asm_toolchain
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

**Створює бінарники в**

```bash
build/bin/cpua
build/bin/cpul
build/bin/cpu_objdump
```

**Використання**

```bash
./build/bin/cpua --help
./build/bin/cpul --help
./build/bin/cpu_objdump main.o
```

### 2. System-wide installation (requires sudo)

Встановлює в `/usr/local/bin` - PATH вже налаштований автоматично:

```bash
cd asm_toolchain
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local
cmake --build build -j
sudo cmake --install build
```

**Перевірка:**

```bash
which cpua
which cpul
which cpu_objdump
cpua --help
cpul --help
cpu_objdump --help
```

### 3. User-local installation (без sudo)

Встановлює в `$HOME/.local/bin` - потребує додавання до PATH один раз:

```bash
cd asm_toolchain
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$HOME/.local"
cmake --build build -j
cmake --install build
```

**Додайте до PATH (один раз для macOS/Linux):**

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Для bash:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Перевірка:**

```bash
which cpua
which cpul
which cpu_objdump
cpua --help
cpul --help
```

### 4. Uninstallation

**Для user-local installation:**

```bash
cd asm_toolchain
xargs rm -vf < build/install_manifest.txt
```

**Для system-wide installation:**

```bash
cd asm_toolchain
sudo xargs rm -vf < build/install_manifest.txt
```

**Альтернативно (перегляд файлів перед видаленням):**

```bash
cd asm_toolchain
cat build/install_manifest.txt
```
