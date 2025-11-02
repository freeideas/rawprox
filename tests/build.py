#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import sys
import os
import subprocess
import shutil
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def main():
    """Build rawprox.exe using .NET Native AOT and place in ./release/"""

    # Get paths
    root_dir = Path(__file__).parent.parent.resolve()
    code_dir = root_dir / "code"
    release_dir = root_dir / "release"

    print(f"Building rawprox from {code_dir}")

    # Ensure release directory exists and is clean
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True)

    # Determine runtime identifier for Windows
    rid = "win-x64"

    # Build command for .NET single-file self-contained executable
    cmd = [
        "dotnet", "publish",
        "-c", "Release",
        "-r", rid,
        "--self-contained", "true",
        "-o", str(release_dir)
    ]

    print(f"Running: {' '.join(cmd)}")

    # Set up environment for Native AOT compilation
    env = os.environ.copy()

    # MSVC and Windows SDK paths
    msvc_base = r"C:\acex\mountz\vstools"
    msvc_bin = rf"{msvc_base}\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64"
    msvc_lib = rf"{msvc_base}\VC\Tools\MSVC\14.44.35207\lib\x64"
    sdk_lib_um = rf"{msvc_base}\WindowsSDK\Lib\um\x64"
    sdk_lib_ucrt = rf"{msvc_base}\WindowsSDK\Lib\ucrt\x64"
    sdk_include_um = rf"{msvc_base}\WindowsSDK\Include\um"
    sdk_include_ucrt = rf"{msvc_base}\WindowsSDK\Include\ucrt"
    sdk_include_shared = rf"{msvc_base}\WindowsSDK\Include\shared"
    msvc_include = rf"{msvc_base}\VC\Tools\MSVC\14.44.35207\include"
    vswhere_dir = r"C:\Program Files (x86)\Microsoft Visual Studio\Installer"

    # Prepend MSVC tools to PATH to override Git's link.exe
    paths_to_add = []
    if os.path.exists(msvc_bin):
        paths_to_add.append(msvc_bin)
    if os.path.exists(vswhere_dir):
        paths_to_add.append(vswhere_dir)
    if paths_to_add:
        env['PATH'] = os.pathsep.join(paths_to_add) + os.pathsep + env.get('PATH', '')

    # Set LIB and INCLUDE for linker
    libs = []
    if os.path.exists(msvc_lib):
        libs.append(msvc_lib)
    if os.path.exists(sdk_lib_um):
        libs.append(sdk_lib_um)
    if os.path.exists(sdk_lib_ucrt):
        libs.append(sdk_lib_ucrt)
    if libs:
        env['LIB'] = os.pathsep.join(libs) + (os.pathsep + env['LIB'] if 'LIB' in env else '')

    includes = []
    if os.path.exists(msvc_include):
        includes.append(msvc_include)
    if os.path.exists(sdk_include_um):
        includes.append(sdk_include_um)
    if os.path.exists(sdk_include_ucrt):
        includes.append(sdk_include_ucrt)
    if os.path.exists(sdk_include_shared):
        includes.append(sdk_include_shared)
    if includes:
        env['INCLUDE'] = os.pathsep.join(includes) + (os.pathsep + env['INCLUDE'] if 'INCLUDE' in env else '')

    # Run build
    result = subprocess.run(
        cmd,
        cwd=code_dir,
        capture_output=False,
        text=True,
        env=env
    )

    if result.returncode != 0:
        print(f"Build failed with exit code {result.returncode}", file=sys.stderr)
        return 1

    # Verify rawprox.exe exists
    exe_path = release_dir / "rawprox.exe"
    if not exe_path.exists():
        print(f"Error: Expected executable not found at {exe_path}", file=sys.stderr)
        return 1

    # Clean up unwanted files (keep only rawprox.exe)
    for item in release_dir.iterdir():
        if item.name != "rawprox.exe":
            print(f"Removing unwanted artifact: {item.name}")
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    # Report success
    exe_size = exe_path.stat().st_size / (1024 * 1024)  # Size in MB
    print(f"\nBuild successful!")
    print(f"Artifact: {exe_path}")
    print(f"Size: {exe_size:.2f} MB")

    return 0

if __name__ == "__main__":
    sys.exit(main())
