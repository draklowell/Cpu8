#!/usr/bin/env python3
"""
Test runner for the Dragonfly 8b9m GDB CLI debugger.
Run this script to execute all tests.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py -v           # Verbose output
    python run_tests.py -k "break"   # Run only tests matching "break"
    python run_tests.py --cov        # Run with coverage
"""

import os
import subprocess
import sys


def main():
    # Change to the simulator directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]

    # Add any additional arguments passed to this script
    cmd.extend(sys.argv[1:])

    # Default options if no args provided
    if len(sys.argv) == 1:
        cmd.extend(["-v", "--tb=short"])

    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)

    # Run pytest
    result = subprocess.run(cmd)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
