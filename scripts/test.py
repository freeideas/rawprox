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
    # Get scripts directory
    scripts_dir = Path(__file__).parent
    project_root = scripts_dir.parent

    # Check for --no-build flag
    skip_build = "--no-build" in sys.argv

    # Build unless --no-build specified
    if not skip_build:
        print("=" * 60)
        print("Running build.py...")
        print("=" * 60)
        build_script = scripts_dir / "build.py"
        result = subprocess.run(
            ["uv", "run", "--script", str(build_script)],
            cwd=project_root
        )

        if result.returncode != 0:
            print("\n❌ Build failed, aborting tests", file=sys.stderr)
            sys.exit(1)
    else:
        print("=" * 60)
        print("Skipping build (--no-build specified)")
        print("=" * 60)

    # Verify ./release/rawprox.exe exists
    binary_path = project_root / "release" / "rawprox.exe"
    if not binary_path.exists():
        print(f"\n❌ Binary not found: {binary_path}", file=sys.stderr)
        print("Run without --no-build to build first", file=sys.stderr)
        sys.exit(1)

    print(f"\n✓ Testing against: ./release/rawprox.exe")
    sys.stdout.flush()

    # Find all test_*.py files in scripts directory
    test_files = sorted(scripts_dir.glob("test_*.py"))

    if not test_files:
        print("\n⚠ No test files found (test_*.py)")
        return

    print("\n" + "=" * 60)
    print(f"Found {len(test_files)} test file(s)")
    for test_file in test_files:
        print(f"  - {test_file.name}")
    print("=" * 60)
    sys.stdout.flush()

    failed_tests = []

    # Run each test file
    for test_file in test_files:
        print(f"\n{'='*60}")
        print(f"STARTING: {test_file.name}")
        print(f"{'='*60}")
        sys.stdout.flush()

        result = subprocess.run(
            ["uv", "run", "--script", str(test_file)],
            cwd=project_root
        )

        sys.stdout.flush()

        if result.returncode != 0:
            failed_tests.append(test_file.name)
            print(f"❌ {test_file.name} FAILED")
        else:
            print(f"✓ {test_file.name} PASSED")
        sys.stdout.flush()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total: {len(test_files)}")
    print(f"Passed: {len(test_files) - len(failed_tests)}")
    print(f"Failed: {len(failed_tests)}")

    if failed_tests:
        print("\nFailed tests:")
        for test in failed_tests:
            print(f"  - {test}")
        sys.exit(1)
    else:
        print("\n✓ All tests passed!")

if __name__ == "__main__":
    main()
