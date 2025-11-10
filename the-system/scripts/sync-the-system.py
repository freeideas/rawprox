#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Sync all the-system directories across ~/prjx to match the source the-system.

Usage:
    Run from anywhere under ~/prjx:
    ./sync-the-system.py

This script:
1. Finds the current directory's ./the-system (the source/model)
2. Walks up the directory tree until it finds a directory named 'prjx' (the root)
3. Syncs every instance of the-system directories found under prjx to match the source
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def find_prjx_root(start_path: Path) -> Path:
    """
    Walk up the directory tree from start_path until finding 'prjx' directory.

    Args:
        start_path: Starting directory (usually cwd)

    Returns:
        Path to prjx directory

    Raises:
        RuntimeError: If prjx directory is not found
    """
    current = start_path.resolve()

    while current != current.parent:  # Stop at root
        if current.name == "prjx":
            return current
        current = current.parent

    raise RuntimeError(f"Could not find 'prjx' directory walking up from {start_path}")


def find_source_the_system() -> Path:
    """
    Find the ./the-system directory relative to current working directory.

    Returns:
        Path to ./the-system

    Raises:
        RuntimeError: If ./the-system does not exist
    """
    source = Path.cwd() / "the-system"

    if not source.is_dir():
        raise RuntimeError(f"./the-system directory not found at {source}")

    return source


def find_all_the_system_dirs(prjx_root: Path) -> list[Path]:
    """
    Find all directories named 'the-system' under prjx_root.

    Args:
        prjx_root: Root prjx directory to search from

    Returns:
        List of paths to the-system directories
    """
    result = []
    for dirpath, dirnames, _ in os.walk(prjx_root):
        if "the-system" in dirnames:
            result.append(Path(dirpath) / "the-system")
    return sorted(result)


def sync_directory(source: Path, target: Path) -> bool:
    """
    Sync source directory to target with --delete behavior (cross-platform).

    Args:
        source: Source directory
        target: Target directory

    Returns:
        True if successful, False otherwise
    """
    try:
        # First, copy/update all files from source to target
        shutil.copytree(source, target, dirs_exist_ok=True)

        # Then, remove files/dirs in target that don't exist in source (--delete behavior)
        for root, dirs, files in os.walk(target, topdown=False):
            root_path = Path(root)
            rel_path = root_path.relative_to(target)
            source_root = source / rel_path

            # Remove files that don't exist in source
            for file in files:
                target_file = root_path / file
                source_file = source_root / file
                if not source_file.exists():
                    target_file.unlink()

            # Remove directories that don't exist in source
            for dir_name in dirs:
                target_dir = root_path / dir_name
                source_dir = source_root / dir_name
                if not source_dir.exists():
                    shutil.rmtree(target_dir)

        return True

    except Exception as e:
        print(f"ERROR syncing {target}: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    try:
        # Find source the-system
        source_the_system = find_source_the_system()
        print(f"Source the-system: {source_the_system}")

        # Find prjx root
        prjx_root = find_prjx_root(Path.cwd())
        print(f"Found prjx root: {prjx_root}")

        # Find all the-system directories
        all_the_system_dirs = find_all_the_system_dirs(prjx_root)
        print(f"Found {len(all_the_system_dirs)} the-system directories")

        if not all_the_system_dirs:
            print("No the-system directories found!", file=sys.stderr)
            sys.exit(1)

        # Sync each one (except the source itself)
        failed = []
        synced = []

        for target in all_the_system_dirs:
            # Skip the source itself
            if target == source_the_system:
                print(f"Skipping source: {target}")
                continue

            print(f"Syncing {target}...", end=" ")
            if sync_directory(source_the_system, target):
                print("✓")
                synced.append(target)
            else:
                print("✗")
                failed.append(target)

        # Print summary
        print(f"\nSummary: {len(synced)} synced", end="")
        if failed:
            print(f", {len(failed)} failed")
            print("Failed:", file=sys.stderr)
            for path in failed:
                print(f"  {path}", file=sys.stderr)
            sys.exit(1)
        else:
            print(" (all successful)")
            sys.exit(0)

    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
