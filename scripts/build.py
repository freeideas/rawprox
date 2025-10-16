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
import glob

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def check_native_image():
    """Check if native-image is available"""
    print("Checking for GraalVM native-image...")
    try:
        result = subprocess.run(
            ["native-image", "--version"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"✓ GraalVM native-image found")
            print(result.stdout.strip())
            return True
    except FileNotFoundError:
        pass

    print("⚠ GraalVM native-image not found", file=sys.stderr)
    print("  Please install GraalVM and native-image", file=sys.stderr)
    return False

def find_java_files(src_dir):
    """Find all .java files recursively"""
    return list(Path(src_dir).rglob("*.java"))

def main():
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    binary = "rawprox.exe"

    print("=" * 60)
    print("RawProx Build (Java/GraalVM Native)")
    print("=" * 60)

    # Delete existing binary first (fail-fast: if build fails, no binary exists)
    dest_dir = project_root / "release"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / binary

    if dest.exists():
        print(f"\nDeleting existing {binary}...")
        dest.unlink()
        print(f"✓ Deleted ./release/{binary}")

    # Check for native-image
    has_native_image = check_native_image()
    if not has_native_image:
        sys.exit(1)

    # Create build directory
    build_dir = project_root / "build"
    build_dir.mkdir(exist_ok=True)

    # Find all Java source files
    src_dir = project_root / "src" / "main" / "java"
    java_files = find_java_files(src_dir)

    if not java_files:
        print("❌ No Java source files found", file=sys.stderr)
        sys.exit(1)

    print(f"\nFound {len(java_files)} Java source files")

    # Compile Java files
    print("\nCompiling Java sources...")
    java_file_paths = [str(f) for f in java_files]

    compile_cmd = [
        "javac",
        "-d", str(build_dir),
        "--release", "21"
    ] + java_file_paths

    result = subprocess.run(compile_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Compilation failed", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    print("✓ Compilation successful")

    # Build native image
    print("\nBuilding native executable with GraalVM...")
    native_image_cmd = [
        "native-image",
        "-cp", str(build_dir),
        "com.rawprox.Main",
        "rawprox",
        "--no-fallback",
        "-H:+ReportExceptionStackTraces"
    ]

    result = subprocess.run(native_image_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Native image build failed", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    print("✓ Native image built successfully")

    # Find and move the native executable
    native_exe = project_root / "rawprox.exe"
    if not native_exe.exists():
        native_exe = project_root / "rawprox"

    if not native_exe.exists():
        print(f"❌ Native executable not found", file=sys.stderr)
        sys.exit(1)

    print(f"\nMoving {native_exe.name} to ./release/{binary}...")
    shutil.move(str(native_exe), str(dest))
    print(f"✓ Binary moved to ./release/{binary}")

    # Clean up build directory
    print("\nCleaning up build directory...")
    shutil.rmtree(build_dir, ignore_errors=True)
    print("✓ Build directory cleaned")

    # Summary
    print("\n" + "=" * 60)
    print("BUILD COMPLETE")
    print("=" * 60)
    print(f"  ✓ ./release/{binary}")

if __name__ == "__main__":
    main()
