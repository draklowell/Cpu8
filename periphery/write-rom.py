import argparse

SIZE = 10240


def main(args: argparse.Namespace):
    with open(args.file, "rb") as file:
        data = file.read()

    if len(data) < SIZE:
        print(f"Warning: File size is less than {SIZE}. Padding with 0xFF.")
        data += b"\xFF" * (SIZE - len(data))
    elif len(data) > SIZE:
        if not all(b == 0xFF for b in data[SIZE:]):
            print(
                f"Error: File size exceeds {SIZE} and contains non-0xFF bytes beyond {SIZE}."
            )
            return

        print(f"Warning: File size exceeds {SIZE}. Truncating to {SIZE}.")
        data = data[:SIZE]
    with open("ROMData.h", "w") as file:
        print("Generating ROMData.h...")
        file.write(
            f"#include <avr/pgmspace.h>\nconst uint8_t memoryRO[{SIZE}] PROGMEM = {{\n"
        )

        for i in range(0, SIZE, 16):
            print(f"Writing block {i // 16 + 1}/{SIZE // 16}\r", end="")
            line = ", ".join(f"0x{byte:02X}" for byte in data[i : i + 16])

            if i + 16 >= SIZE:
                file.write(f"    {line}\n")
            else:
                file.write(f"    {line},\n")

        file.write("};\n")
        print("\nSuccessfully generated ROMData.h")


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Programmer for CPU816")
    parser.add_argument("file", help="BIN file to write to the CPU816 ROM")
    args = parser.parse_args()
    main(args)
