#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import sys
import subprocess
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def main():
    print("=" * 60)
    print("UNIT TESTS (_TEST_ methods)")
    print("=" * 60)
    print()

    project_root = Path(__file__).parent.parent

    # Run the program with --run-tests flag
    result = subprocess.run(
        ["dotnet", "run", "--", "--run-tests"],
        cwd=project_root,
        timeout=30
    )

    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
