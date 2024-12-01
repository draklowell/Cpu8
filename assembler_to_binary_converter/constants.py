import re

OPERATIONS = {
    "mvr": "0",
    "mvd": "1",
    "mva": "2",
    "mvf": "3",
    "nand": "4",
    "ret": "5",
    "sub": "6",
    "io_int": "7",
    "halt": "8",
    "add": "9",
    "iop": "b",
    "jeq": "c",
    "jls": "d",
    "jle": "e",
    "jne": "f",
}

DOUBLE_REG_REGEX = re.compile(r"\s*(mvr|mva|mvf|nand|sub|add|)\s+r([0-7])\s*,\s*r([0-7])\s*\#*.*")
REG_IMMED_REGEX = re.compile(r"\s*(mvd)\s+r([0-7])\s*,\s*([0-9a-f])\s*\#*.*")
IMMED_REG_REGEX = re.compile(r"\s*(iop)\s+([0-9a-f])\s*,\s*r([0-7])\s*\#*.*")
NO_OPPERANDS_REGEX = re.compile(r"\s*(ret|io_int|halt)\#*.*")
JUMP_REGEX = re.compile(r"\s*(jeq|jle|jls|jne)\s+([a-zA-Z][a-zA-Z0-9_]*)\#*.*")
LABEL_REGEX = re.compile(r"([a-zA-Z][a-zA-Z0-9_]*):")
