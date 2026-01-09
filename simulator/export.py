import subprocess
from pathlib import Path


def export(input_path: str, output_path: str):
    schematic = Path(input_path)
    output = Path(output_path)

    cmd = [
        "kicad-cli",
        "sch",
        "export",
        "netlist",
        "--format",
        "cadstar",
        "--output",
        str(output),
        str(schematic),
    ]

    subprocess.run(cmd, check=True)


MODULES = [
    ("../schematics/alu_hub/alu_hub.kicad_sch", "netlists/alu_hub.frp"),
    ("../schematics/core_1/core_1.kicad_sch", "netlists/core_1.frp"),
    ("../schematics/core_2/core_2.kicad_sch", "netlists/core_2.frp"),
    ("../schematics/core_3/core_3.kicad_sch", "netlists/core_3.frp"),
    ("../schematics/interface/interface.kicad_sch", "netlists/interface.frp"),
    ("../schematics/program_counter/pc.kicad_sch", "netlists/program_counter.frp"),
    (
        "../schematics/stack_pointer/step_counter.kicad_sch",
        "netlists/stack_pointer.frp",
    ),
    (
        "../schematics/register_file_accum/register_file_accum.kicad_sch",
        "netlists/register_file_accum.frp",
    ),
]


if __name__ == "__main__":
    for input_path, output_path in MODULES:
        export(input_path, output_path)
