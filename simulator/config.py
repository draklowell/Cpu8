"""
Configuration and data loading for the debugger and simulator
"""

import csv
import json

PERIOD = 800
INIT_TICKS = 200
STARTUP_TICKS = 200

MODULES = [
    ("netlists/alu_hub.frp", "ALU"),
    ("netlists/core_1.frp", "C1"),
    ("netlists/core_2.frp", "C2"),
    ("netlists/core_3.frp", "C3"),
    ("netlists/interface.frp", "I"),
    ("netlists/program_counter.frp", "PC"),
    ("netlists/register_file_accum.frp", "REG"),
    ("netlists/stack_pointer.frp", "SP"),
]

TABLES_PATH = "../microcode/bin"


def load_microcode_data() -> tuple[dict[int, str], dict[int, str], dict[int, str]]:
    """
    Loads data from microcode used in simulator and debuger wrapper

    Returns:
        tuple[dict[int, str], dict[int, str], dict[int, str]]: Readers, writers and microcode mnemonics
    """
    with open(f"{TABLES_PATH}/components.json", "r") as file:
        components_data = json.load(file)
        readers = {int(key): value for key, value in components_data["readers"].items()}
        writers = {int(key): value for key, value in components_data["writers"].items()}

    with open(f"{TABLES_PATH}/table.csv", "r") as file:
        reader = csv.DictReader(file)
        microcode = {int(row["decOpcode"]): row["mnemonic"] for row in reader}

    return readers, writers, microcode
