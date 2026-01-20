import argparse
import csv
import datetime

import vcd.writer

VARIABLES = {
    "debug/clk": ("logic", 1),
    "debug/data": ("logic", 8),
    "debug/state": ("logic", 8),
    "debug/pcinc": ("logic", 1),
    "debug/not_scclear": ("logic", 1),
    "debug/not_instread": ("logic", 1),
    "debug/not_enable": ("logic", 1),
    "debug/direction": ("logic", 1),
    "interface/clk": ("logic", 1),
    "interface/data": ("logic", 8),
    "interface/address": ("logic", 16),
    "interface/not_read": ("logic", 1),
    "interface/not_write": ("logic", 1),
}


def main(debug_path: str, interface_path: str, merged_path: str):
    with open(debug_path, "r") as file:
        reader = csv.DictReader(file)
        debug_data = []
        debug_first_clk = -1
        for row in reader:
            record = {
                "time": int(row["time"]),
                "debug/clk": int(row["clk"]),
                "debug/data": int(row["data"]),
                "debug/state": int(row["state"]),
                "debug/pcinc": int(row["pcinc"]),
                "debug/not_scclear": int(row["not_scclear"]),
                "debug/not_instread": int(row["not_instread"]),
                "debug/not_enable": int(row["not_enable"]),
                "debug/direction": int(row["direction"]),
            }
            debug_data.append(record)
            if record["debug/clk"] and debug_first_clk == -1:
                debug_first_clk = record["time"]

        if debug_first_clk == -1:
            raise ValueError("Debug file has no clock signal")

    with open(interface_path, "r") as file:
        reader = csv.DictReader(file)
        interface_data = []
        interface_first_clk = -1
        for row in reader:
            record = {
                "time": int(row["time"]),
                "interface/clk": int(row["clk"]),
                "interface/data": int(row["data"]),
                "interface/address": int(row["address"]),
                "interface/not_read": int(row["not_read"]),
                "interface/not_write": int(row["not_write"]),
            }
            interface_data.append(record)
            if record["interface/clk"] and interface_first_clk == -1:
                interface_first_clk = record["time"]

        if interface_first_clk == -1:
            raise ValueError("Interface file has no clock signal")

    data = []

    for row in debug_data:
        row["time"] -= debug_first_clk
        if row["time"] < 0:
            continue

        data.append(row)

    for row in interface_data:
        row["time"] -= interface_first_clk
        if row["time"] < 0:
            continue

        data.append(row)

    data.sort(key=lambda x: x["time"])

    with open(merged_path, "w") as file:
        writer = vcd.writer.VCDWriter(
            file,
            timescale="1 us",
            date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        variables = {}
        for var_name, (var_type, var_size) in VARIABLES.items():
            scope, name = var_name.split("/")
            variables[var_name] = writer.register_var(
                scope, name, var_type, size=var_size
            )

        current_values = {var_name: None for var_name in VARIABLES.keys()}
        for row in data:
            time = row["time"]
            for var_name, value in row.items():
                if var_name == "time":
                    continue
                if current_values[var_name] != value:
                    writer.change(variables[var_name], time, value)
                    current_values[var_name] = value

    print(f"Merged VCD file written to {merged_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge debug and interface CSV files into a VCD file."
    )
    parser.add_argument("debug_csv", help="Path to the debug CSV file.")
    parser.add_argument("interface_csv", help="Path to the interface CSV file.")
    parser.add_argument("merged_vcd", help="Path to the output merged VCD file.")

    args = parser.parse_args()

    main(args.debug_csv, args.interface_csv, args.merged_vcd)
