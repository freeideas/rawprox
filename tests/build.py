#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    """Build RawProx and package artifacts in ./release/"""

    # Determine project paths
    project_root = Path(__file__).parent.parent.absolute()
    code_dir = project_root / "code"
    release_dir = project_root / "release"

    print(f"Building RawProx...")
    print(f"Project root: {project_root}")
    print(f"Code directory: {code_dir}")
    print(f"Release directory: {release_dir}")

    # Clean release directory
    if release_dir.exists():
        print(f"Cleaning {release_dir}...")
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)

    # Determine runtime identifier
    if sys.platform == "win32":
        rid = "win-x64"
    elif sys.platform == "darwin":
        rid = "osx-x64"
    else:
        rid = "linux-x64"

    print(f"Building for runtime: {rid}")

    # Build command
    build_cmd = [
        "dotnet", "publish",
        str(code_dir / "RawProx.csproj"),
        "-c", "Release",
        "-r", rid,
        "--self-contained",
        "-p:PublishAot=true",
        "-p:StripSymbols=true",
        "-p:DebugType=none",
        "-o", str(release_dir)
    ]

    print(f"Running: {' '.join(build_cmd)}")
    result = subprocess.run(build_cmd, cwd=code_dir)

    if result.returncode != 0:
        print("Build failed!", file=sys.stderr)
        return 1

    # Verify only rawprox.exe exists
    files = list(release_dir.glob("*"))

    # Remove any non-executable files
    for file in files:
        if file.name not in ["rawprox.exe", "rawprox"]:
            print(f"Removing extra file: {file.name}")
            file.unlink()

    # Rename executable to rawprox.exe if needed
    exe_path = release_dir / "rawprox.exe"
    if not exe_path.exists():
        rawprox_path = release_dir / "rawprox"
        if rawprox_path.exists():
            print("Renaming rawprox to rawprox.exe")
            rawprox_path.rename(exe_path)

    # Verify final artifact
    if not exe_path.exists():
        print("Error: rawprox.exe not found in release directory!", file=sys.stderr)
        return 1

    # Make executable on Unix
    if sys.platform != "win32":
        os.chmod(exe_path, 0o755)

    final_files = list(release_dir.glob("*"))
    print(f"\nBuild complete!")
    print(f"Artifacts in {release_dir}:")
    for file in final_files:
        size = file.stat().st_size / (1024 * 1024)
        print(f"  {file.name} ({size:.2f} MB)")

    return 0

if __name__ == "__main__":
    sys.exit(main())
