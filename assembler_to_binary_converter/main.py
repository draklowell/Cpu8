import argparse

from constants import JUMP_REGEX, NO_OPPERANDS_REGEX, IMMED_REG_REGEX, LABEL_REGEX, REG_IMMED_REGEX, DOUBLE_REG_REGEX, \
    OPERATIONS


def write_raw_utf(filename: str, codes: list[str]) -> None:
    with open(filename + ".bin", "w", encoding="utf-8") as file:
        for l in codes:
            file.write(l + "\n")


def assembly_to_binary(filename: str) -> list[str]:
    result: list[str] = ["000"]
    labels = {}

    with open(filename, "r", encoding="utf-8") as file:
        i = 1
        for line in file:
            new_op = ""
            line = line.strip()
            if line == "":
                continue

            if re_match := DOUBLE_REG_REGEX.match(line):
                new_op = OPERATIONS[re_match.group(1)] + re_match.group(2) + re_match.group(3)
            elif re_match := REG_IMMED_REGEX.match(line):
                new_op = OPERATIONS[re_match.group(1)] + re_match.group(2) + re_match.group(3)
            elif re_match := IMMED_REG_REGEX.match(line):
                new_op = OPERATIONS[re_match.group(1)] + re_match.group(2) + re_match.group(3)
            elif re_match := NO_OPPERANDS_REGEX.match(line):
                new_op = OPERATIONS[re_match.group(1)] + "00"
            elif re_match := JUMP_REGEX.match(line):
                new_op = OPERATIONS[re_match.group(1)] + labels.get(re_match.group(2), "00")
            elif re_match := LABEL_REGEX.match(line):
                labels[re_match.group(1)] = f"{i:02x}"
                continue

            i += 1

            if new_op == "":
                raise SyntaxError(f"Operation for this line is not defined: {line}")

            result.append(new_op)
    return result


def main():
    parser = argparse.ArgumentParser(
        prog='CPU assembly translator',
        description='Program to translate assembly code of a nibble cpu to binary code',
    )

    parser.add_argument("filename")
    parser.add_argument("-t", "--translate", action="store_true")
    parser.add_argument("-l", "--logisim", action="store_true")

    args = parser.parse_args()

    if args.translate:
        res = assembly_to_binary(args.filename)
        if args.logisim:
            write_raw_utf(args.filename, res)


if __name__ == "__main__":
    main()
