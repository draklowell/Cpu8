import os
import platform
import shutil
import subprocess
from pathlib import Path

SYSTEM = platform.system()
DARWIN = "Darwin"


def get_kicad_cli_path() -> str:
    """
    Detects the user system and returns the appropriate path to the kicad-cli executable.

    Returns:
        str: str with the path to kicad-cli exe
    """

    if SYSTEM == DARWIN:
        macos_path = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
        if Path(macos_path).exists():
            return macos_path

    kicad_cli = shutil.which("kicad-cli")
    if kicad_cli:
        return str(kicad_cli)

    return "kicad-cli"


def export(input_path: str, output_path: str):
    schematic = Path(input_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        get_kicad_cli_path(),
        "sch",
        "export",
        "netlist",
        "--format",
        "cadstar",
        "--output",
        str(output),
        str(schematic),
    ]

    env = os.environ.copy()
    if SYSTEM == DARWIN:
        env["FONTCONFIG_FILE"] = "/dev/null"
        env["FONTCONFIG_PATH"] = "/dev/null"

    subprocess.run(
        cmd,
        check=True,
        env=env,
        stderr=subprocess.DEVNULL if SYSTEM == DARWIN else None,
    )


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
