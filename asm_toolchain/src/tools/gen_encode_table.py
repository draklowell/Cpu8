"""Generate EncodeTable.inc.hpp from the CSV opcode table."""

import csv
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MovEntry:
    dst: str
    src: str


@dataclass(frozen=True)
class SimpleEntry:
    mnemonic: str
    sig_kind: str  # "none", "imm8", "imm16"


@dataclass(frozen=True)
class SpecialEntry:
    kind: str  # "LDI8", "LDI16", "LDABS16", "STABS16"
    reg: str


class EncodeTableGenerator:
    _BASE_DIR = Path(__file__).resolve().parent
    TABLE = _BASE_DIR / "table.csv"
    OUT = _BASE_DIR.parent / "asm" / "EncodeTable.inc.hpp"

    MOV_RE = re.compile(r"^mov-([^-]+)-([^-]+)$", re.IGNORECASE)
    LDI_RE = re.compile(r"^ldi-([^-]+)-\[(byte|word)\]$", re.IGNORECASE)
    LDABS_RE = re.compile(r"^ld-([^-]+)-\[word\]$", re.IGNORECASE)
    STABS_RE = re.compile(r"^st-\[word]-([^-]+)$", re.IGNORECASE)

    REG_ALIASES = {
        "ac": "AC",
        "xh": "XH",
        "yl": "YL",
        "yh": "YH",
        "zl": "ZL",
        "zh": "ZH",
        "fr": "FR",
        "sp": "SP",
        "pc": "PC",
        "x": "X",
        "y": "Y",
        "z": "Z",
    }

    SIG_STRINGS = {
        "none": "Sig({})",
        "imm8": "Sig({OT::Imm8})",
        "imm16": "Sig({OT::Imm16})",
    }

    SIMPLE_SIZES = {
        "none": 1,
        "imm8": 2,
        "imm16": 3,
    }

    def __init__(self, table_path: Path | None = None, out_path: Path | None = None):
        self.table_path = table_path or self.TABLE
        self.out_path = out_path or self.OUT

    def reg_enum(self, raw: str) -> str:
        key = raw.strip().lower()
        if key not in self.REG_ALIASES:
            raise ValueError(f"Unknown register '{raw}'")
        return f"Reg::{self.REG_ALIASES[key]}"

    def classify(self, mnemonic: str):
        text = mnemonic.strip().lower()
        if not text:
            raise ValueError("Empty mnemonic")

        if match := self.MOV_RE.match(text):
            dst = self.reg_enum(match.group(1))
            src = self.reg_enum(match.group(2))
            return MovEntry(dst=dst, src=src)

        if match := self.LDI_RE.match(text):
            reg = self.reg_enum(match.group(1))
            width = match.group(2).lower()
            if width == "byte":
                return SpecialEntry(kind="LDI8", reg=reg)
            if width == "word":
                return SpecialEntry(kind="LDI16", reg=reg)
            raise ValueError(
                f"Unsupported immediate width '{width}' for mnemonic '{mnemonic}'"
            )

        if match := self.LDABS_RE.match(text):
            reg = self.reg_enum(match.group(1))
            return SpecialEntry(kind="LDABS16", reg=reg)

        if match := self.STABS_RE.match(text):
            reg = self.reg_enum(match.group(1))
            return SpecialEntry(kind="STABS16", reg=reg)

        if text.endswith("-[byte]"):
            base = text[: -len("-[byte]")]
            return SimpleEntry(mnemonic=base, sig_kind="imm8")

        if text.endswith("-[word]"):
            base = text[: -len("-[word]")]
            return SimpleEntry(mnemonic=base, sig_kind="imm16")

        return SimpleEntry(mnemonic=text, sig_kind="none")

    def read_rows(self) -> list[tuple[int, str]]:
        rows: list[tuple[int, str]] = []
        with self.table_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if not row:
                    continue
                mnemonic = (row.get("mnemonic") or "").strip()
                if not mnemonic:
                    continue
                hex_opcode = (row.get("hexOpcode") or "").strip()
                if not hex_opcode:
                    raise ValueError(f"Missing hexOpcode for mnemonic '{mnemonic}'")
                opcode = int(hex_opcode, 16)
                rows.append((opcode, mnemonic))
        rows.sort(key=lambda item: item[0])
        return rows

    def format_line(self, opcode: int, entry) -> str:
        if isinstance(entry, MovEntry):
            return f"ADD_MOV({entry.dst}, {entry.src}, 0x{opcode:02X});"
        if isinstance(entry, SpecialEntry):
            if entry.kind == "LDI8":
                return f"ADD_LDI8({entry.reg}, 0x{opcode:02X});"
            if entry.kind == "LDI16":
                return f"ADD_LDI16({entry.reg}, 0x{opcode:02X});"
            if entry.kind == "LDABS16":
                return f"ADD_LDABS16({entry.reg}, 0x{opcode:02X});"
            if entry.kind == "STABS16":
                return f"ADD_STABS16({entry.reg}, 0x{opcode:02X});"
            raise ValueError(f"Unknown special entry kind '{entry.kind}'")
        if isinstance(entry, SimpleEntry):
            sig = self.SIG_STRINGS[entry.sig_kind]
            size = self.SIMPLE_SIZES[entry.sig_kind]
            return f'ADD_SIMPLE("{entry.mnemonic}", {sig}, 0x{opcode:02X}, {size});'
        raise TypeError(f"Unsupported entry type: {type(entry)!r}")

    def run(self) -> None:
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["// DO NOT EDIT — generated from table.csv", ""]
        for opcode, mnemonic in self.read_rows():
            entry = self.classify(mnemonic)
            lines.append(self.format_line(opcode, entry))
        self.out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    generator = EncodeTableGenerator()
    generator.run()


if __name__ == "__main__":
    main()
