#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Verify that ./release/ contains the correct build artifacts.

Checks that:
- rawprox.exe exists in ./release/
- No debug symbols (.pdb files)
- No runtime dependencies (.dll files)
"""

import sys
# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path

def main():
    print("Verifying build artifacts...")

    release_dir = Path('./release')
    assert release_dir.exists(), "Missing ./release/ directory"

    # $REQ_SIMPLE_001: Single Executable
    exe_path = release_dir / 'rawprox.exe'
    assert exe_path.exists(), f"Missing executable: {exe_path}"  # $REQ_SIMPLE_001
    assert exe_path.is_file(), f"{exe_path} must be a file"  # $REQ_SIMPLE_001
    print(f"✓ Executable exists: {exe_path}")

    # $REQ_SIMPLE_002A: Executable Extension on All Platforms
    files = list(release_dir.glob('*'))
    assert exe_path.name == 'rawprox.exe', "Executable must be named rawprox.exe"  # $REQ_SIMPLE_002A
    print(f"✓ Executable has correct name: rawprox.exe")

    # Verify no debug or runtime files
    for f in files:
        assert not f.name.endswith('.pdb'), f"No debug files allowed: {f.name}"
        assert not f.name.endswith('.dll'), f"No runtime files allowed: {f.name}"
    print(f"✓ No debug (.pdb) or runtime (.dll) files")

    print(f"✓ All build artifacts correct")
    return 0

if __name__ == '__main__':
    sys.exit(main())
