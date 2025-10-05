#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from pathlib import Path

class EncodeTableGenerator:
    TABLE = Path("table.txt")
    OUT   = Path("../asm/EncodeTable.inc.hpp")
    LINE_RE = re.compile(r"^\s*([0-9A-Fa-f]{2})\s*:\s*([^\s].*?)\s*$")

    REG_ALIASES = {
        "ac":"AC", "xh":"XH", "yl":"YL", "yh":"YH", "zl":"ZL", "zh":"ZH", "fr":"FR",
        "sp":"SP", "pc":"PC",
        "x":"X", "y":"Y", "z":"Z",
    }

    @staticmethod
    def reg_enum(s: str) -> str:
        s = s.strip().lower()
        if s not in EncodeTableGenerator.REG_ALIASES:
            raise ValueError(f"Unknown register '{s}'")
        return f"Reg::{EncodeTableGenerator.REG_ALIASES[s]}"

    @staticmethod
    def sig_none():
        return "Sig({OT::None})"

    @staticmethod
    def sig_imm8():
        return "Sig({OT::Imm8})"

    @staticmethod
    def sig_imm16():
        return "Sig({OT::Imm16})"

    @staticmethod
    def sig_memabs16():
        return "Sig({OT::MemAbs16})"

    @staticmethod
    def parse_table_line(line: str):
        m = EncodeTableGenerator.LINE_RE.match(line)
        if not m:
            return None
        opc_hex = m.group(1)
        mnem = m.group(2).strip()
        opcode = int(opc_hex, 16)
        return opcode, mnem

    def classify(opcode: int, mnem: str):
        """
        Повертає tuple виду:
          ("LDI8", reg)
          ("LDI16", reg)
          ("LDABS16", reg)
          ("STABS16", reg)
          ("MOV", dst, src)
          ("SIMPLE", mnem, sig_kind)   # sig_kind: "none"|"imm8"|"imm16"
        """
        s = mnem.lower()

        # 1) mov-dst-src
        if s.startswith("mov-"):
            parts = s.split("-")
            if len(parts) == 3:
                dst, src = parts[1], parts[2]
                return ("MOV", EncodeTableGenerator.reg_enum(dst), EncodeTableGenerator.reg_enum(src))
            else:
                raise ValueError(f"Bad mov mnemonic: {mnem}")

        # 2) ldi-REG-[byte] / ldi-REG-[word]
        if s.startswith("ldi-"):
            if s.endswith("[byte]"):
                reg = s[len("ldi-") : -len("-[byte]")]
                return ("LDI8", EncodeTableGenerator.reg_enum(reg))
            if s.endswith("[word]"):
                reg = s[len("ldi-") : -len("-[word]")]
                return ("LDI16", EncodeTableGenerator.reg_enum(reg))

        # 3) ld-REG-[word]  -> load from absolute 16-bit address
        if s.startswith("ld-") and s.endswith("[word]"):
            reg = s[len("ld-") : -len("-[word]")]
            return ("LDABS16", EncodeTableGenerator.reg_enum(reg))

        # 4) st-[word]-REG  -> store to absolute 16-bit address
        if s.startswith("st-[word]-"):
            reg = s[len("st-[word]-") :]
            return ("STABS16", EncodeTableGenerator.reg_enum(reg))

        # 5) будь-що інше: визначимо наявність [byte]/[word] для сигнатури
        if "[byte]" in s:
            base = s.replace("-[byte]", "")
            return ("SIMPLE", base, "imm8")
        if "[word]" in s:
            base = s.replace("-[word]", "")
            return ("SIMPLE", base, "imm16")

        # 6) дефолт — без аргументів
        return ("SIMPLE", s, "none")

    @staticmethod
    def procces():
        EncodeTableGenerator.OUT.parent.mkdir(parents=True, exist_ok=True)
        lines_out = []
        lines_out.append("// DO NOT EDIT — generated from table.txt\n")

        with EncodeTableGenerator.TABLE.open("r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw or raw.startswith("#") or raw.startswith("//"):
                    continue
                parsed = EncodeTableGenerator.parse_table_line(raw)
                if not parsed:
                    continue
                opcode, mnem = parsed
                kind = EncodeTableGenerator.classify(opcode, mnem)

                if kind[0] == "MOV":
                    _, dst, src = kind
                    lines_out.append(f"ADD_MOV({dst}, {src}, 0x{opcode:02X});")
                elif kind[0] == "LDI8":
                    _, reg = kind
                    lines_out.append(f"ADD_LDI8({reg}, 0x{opcode:02X});")
                elif kind[0] == "LDI16":
                    _, reg = kind
                    lines_out.append(f"ADD_LDI16({reg}, 0x{opcode:02X});")
                elif kind[0] == "LDABS16":
                    _, reg = kind
                    lines_out.append(f"ADD_LDABS16({reg}, 0x{opcode:02X});")
                elif kind[0] == "STABS16":
                    _, reg = kind
                    lines_out.append(f"ADD_STABS16({reg}, 0x{opcode:02X});")
                elif kind[0] == "SIMPLE":
                    _, base_mnem, sigk = kind
                    if sigk == "imm8":
                        lines_out.append(f'ADD_SIMPLE("{base_mnem}", {EncodeTableGenerator.sig_imm8()}, 0x{opcode:02X}, 2);')
                    elif sigk == "imm16":
                        lines_out.append(f'ADD_SIMPLE("{base_mnem}", {EncodeTableGenerator.sig_imm16()}, 0x{opcode:02X}, 3);')
                    else:
                        lines_out.append(f'ADD_SIMPLE("{base_mnem}", {EncodeTableGenerator.sig_none()}, 0x{opcode:02X}, 1);')
                else:
                    raise RuntimeError("unknown kind")

        with EncodeTableGenerator.OUT.open("w", encoding="utf-8") as f:
            f.write("\n".join(lines_out) + "\n")

if __name__ == "__main__":
    etg = EncodeTableGenerator()
    etg.procces()
