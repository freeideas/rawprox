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

def check_dotnet():
    """Check if dotnet SDK is available"""
    print("Checking for .NET SDK...")
    try:
        result = subprocess.run(
            ["dotnet", "--version"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"✓ .NET SDK found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    print("⚠ .NET SDK not found", file=sys.stderr)
    print("  Please install .NET 8 SDK or later", file=sys.stderr)
    return False

def main():
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    binary = "rawprox.exe"

    print("=" * 60)
    print("RawProx Build (C#/.NET Native AOT)")
    print("=" * 60)

    # Delete existing binary first (fail-fast: if build fails, no binary exists)
    dest_dir = project_root / "release"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / binary

    if dest.exists():
        print(f"\nDeleting existing {binary}...")
        dest.unlink()
        print(f"✓ Deleted ./release/{binary}")

    # Check for dotnet SDK
    has_dotnet = check_dotnet()
    if not has_dotnet:
        sys.exit(1)

    # Build with Native AOT
    print("\nBuilding native executable with .NET Native AOT...")

    # Add Visual Studio toolchain and installer to PATH
    vs_tools_path = r"C:\acex\mountz\vstools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64"
    vs_installer_path = r"C:\Program Files (x86)\Microsoft Visual Studio\Installer"
    env = os.environ.copy()
    env["PATH"] = vs_tools_path + os.pathsep + vs_installer_path + os.pathsep + env["PATH"]

    build_cmd = [
        "dotnet", "publish",
        "-c", "Release",
        "-r", "win-x64",
        "--self-contained",
        "-p:PublishAot=true",
        "-p:StripSymbols=true"
    ]

    result = subprocess.run(build_cmd, capture_output=True, text=True, env=env)

    if result.returncode != 0:
        print("❌ Native AOT build failed", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    print("✓ Native AOT build successful")

    # Find and move the native executable
    native_exe = project_root / "bin" / "Release" / "net8.0" / "win-x64" / "publish" / "rawprox.exe"

    if not native_exe.exists():
        # Try alternative paths
        alt_paths = list((project_root / "bin").rglob("rawprox.exe"))
        if alt_paths:
            native_exe = alt_paths[0]
        else:
            print(f"❌ Native executable not found", file=sys.stderr)
            sys.exit(1)

    print(f"\nMoving {native_exe.name} to ./release/{binary}...")
    shutil.copy2(str(native_exe), str(dest))
    print(f"✓ Binary copied to ./release/{binary}")

    # Clean up build directory
    print("\nCleaning up build directory...")
    bin_dir = project_root / "bin"
    obj_dir = project_root / "obj"
    if bin_dir.exists():
        shutil.rmtree(bin_dir, ignore_errors=True)
    if obj_dir.exists():
        shutil.rmtree(obj_dir, ignore_errors=True)
    print("✓ Build directories cleaned")

    # Summary
    print("\n" + "=" * 60)
    print("BUILD COMPLETE")
    print("=" * 60)
    print(f"  ✓ ./release/{binary}")

if __name__ == "__main__":
    main()
