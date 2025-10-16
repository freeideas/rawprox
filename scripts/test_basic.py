#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Basic smoke test for RawProx binaries
Tests that the binaries exist and show usage when run incorrectly
"""

import sys
import subprocess
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def test_binary(binary_path, name):
    """Test a single binary"""
    print(f"\n{'=' * 60}")
    print(f"Testing {name}")
    print('=' * 60)

    # Test 1: Binary exists
    print(f"Test 1: Checking if {binary_path.name} exists...")
    if not binary_path.exists():
        print(f"❌ Binary not found at {binary_path}", file=sys.stderr)
        return False
    print(f"✓ Binary exists at {binary_path}")

    # Test 2: Binary is executable
    print(f"\nTest 2: Checking if binary is a valid file...")
    if not binary_path.is_file():
        print(f"❌ Path exists but is not a file", file=sys.stderr)
        return False
    print(f"✓ Binary is a file")

    # Test 3: Check file size
    size = binary_path.stat().st_size
    print(f"\nTest 3: Checking binary size...")
    if size < 1000:  # Less than 1KB seems wrong
        print(f"❌ Binary is suspiciously small: {size} bytes", file=sys.stderr)
        return False
    print(f"✓ Binary size looks reasonable: {size:,} bytes")

    # Test 4: Running with no args should fail and show usage
    # Skip execution test on Windows when testing Linux binary and vice versa
    is_windows = sys.platform == "win32"
    is_exe = binary_path.suffix == ".exe"

    if is_windows != is_exe:
        print(f"\nTest 4: Skipping execution test (cross-platform binary)")
    else:
        print(f"\nTest 4: Running with no arguments (should show usage)...")
        try:
            result = subprocess.run(
                [str(binary_path)],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                print(f"❌ Expected non-zero exit code, got 0", file=sys.stderr)
                return False

            # Should output usage information
            output = result.stdout + result.stderr
            if "rawprox" not in output.lower():
                print(f"❌ Expected usage/error message containing 'rawprox', got:", file=sys.stderr)
                print(output[:200], file=sys.stderr)
                return False

            print(f"✓ Binary shows usage/error correctly")

        except subprocess.TimeoutExpired:
            print(f"❌ Binary timed out (may be hanging)", file=sys.stderr)
            return False
        except Exception as e:
            print(f"❌ Error running binary: {e}", file=sys.stderr)
            return False

    return True

def main():
    # Get project root
    project_root = Path(__file__).parent.parent
    release_dir = project_root / "release"

    # Define binaries to test
    binaries = [
        (release_dir / "x86win64" / "rawprox.exe", "Windows x86_64"),
        (release_dir / "x86linux64" / "rawprox", "Linux x86_64")
    ]

    print("=" * 60)
    print("RawProx Basic Tests")
    print("=" * 60)

    results = []
    tested_count = 0
    for binary_path, name in binaries:
        # Skip binaries that don't exist
        if not binary_path.exists():
            print(f"\n⚠ Skipping {name} - binary not found at {binary_path}")
            continue

        tested_count += 1
        passed = test_binary(binary_path, name)
        results.append((name, passed))

    # Require at least one binary to be tested
    if tested_count == 0:
        print("\n❌ No binaries found to test", file=sys.stderr)
        sys.exit(1)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ PASSED" if passed else "❌ FAILED"
        print(f"{name:20} {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✓ All basic tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
