#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import sys
import subprocess
import shutil
import os
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def ensure_target_installed(target):
    """Ensure a Rust target is installed"""
    print(f"Checking if {target} is installed...")
    result = subprocess.run(
        ["rustup", "target", "list", "--installed"],
        capture_output=True,
        text=True
    )

    if target not in result.stdout:
        print(f"Installing {target}...")
        result = subprocess.run(["rustup", "target", "add", target])
        if result.returncode != 0:
            print(f"❌ Failed to install {target}", file=sys.stderr)
            sys.exit(1)
        print(f"✓ {target} installed")
    else:
        print(f"✓ {target} already installed")

def main():
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    target = "x86_64-pc-windows-msvc"
    binary = "rawprox.exe"

    print("=" * 60)
    print("RawProx Build (Windows x64)")
    print("=" * 60)

    # Delete existing binary first (fail-fast: if build fails, no binary exists)
    dest_dir = project_root / "release"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / binary

    if dest.exists():
        print(f"\nDeleting existing {binary}...")
        dest.unlink()
        print(f"✓ Deleted ./release/{binary}")

    # Ensure target is installed
    ensure_target_installed(target)

    # Build
    print(f"\nBuilding for {target}...")
    result = subprocess.run(
        ["cargo", "build", "--release", "--target", target],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ Build failed for {target}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    print(f"✓ Build successful")

    # Move binary to ./release/
    source = project_root / "target" / target / "release" / binary

    print(f"\nMoving {binary} to ./release/{binary}...")
    shutil.move(str(source), str(dest))
    print(f"✓ Binary moved to ./release/{binary}")

    # Summary
    print("\n" + "=" * 60)
    print("BUILD COMPLETE")
    print("=" * 60)
    print(f"  ✓ ./release/{binary}")

if __name__ == "__main__":
    main()
