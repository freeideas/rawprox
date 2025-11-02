#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import sys
# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import os
import subprocess
import argparse
from pathlib import Path

# Change to project root (two levels up from this script)
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
os.chdir(project_root)

def run_command(cmd, description):
    """Run a command and return exit code."""
    print(f"\n{'=' * 60}")
    print(f"{description}")
    print(f"{'=' * 60}\n")
    # Convert command string to list for shell=False (better Windows compatibility)
    import shlex
    if isinstance(cmd, str):
        cmd_list = shlex.split(cmd, posix=False)  # posix=False for Windows
    else:
        cmd_list = cmd
    result = subprocess.run(cmd_list, shell=False, timeout=300)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description='Run tests with build step')
    parser.add_argument('--passing', action='store_true', help='Run only passing tests')
    parser.add_argument('--failing', action='store_true', help='Run only failing tests')
    parser.add_argument('test_file', nargs='?', help='Specific test file to run')

    args = parser.parse_args()

    # Step 1: Run build script
    if not os.path.exists('./tests/build.py'):
        print("ERROR: ./tests/build.py does not exist")
        print("Run work-queue.py to see what needs to be done")
        sys.exit(1)

    exit_code = run_command('uv run --script ./tests/build.py', 'Building project')
    if exit_code != 0:
        print(f"\nBuild failed with exit code {exit_code}")
        sys.exit(exit_code)

    # Step 2: Determine which tests to run
    if args.test_file:
        # Run specific test file
        test_target = args.test_file
    elif args.passing:
        # Run all passing tests
        test_target = './tests/passing'
        if not os.path.exists(test_target) or not os.listdir(test_target):
            print("\nNo passing tests found")
            sys.exit(0)
    elif args.failing:
        # Run all failing tests
        test_target = './tests/failing'
        if not os.path.exists(test_target) or not os.listdir(test_target):
            print("\nNo failing tests found")
            sys.exit(0)
    else:
        # Default: run failing tests if they exist, otherwise passing tests
        if os.path.exists('./tests/failing') and os.listdir('./tests/failing'):
            test_target = './tests/failing'
        elif os.path.exists('./tests/passing') and os.listdir('./tests/passing'):
            test_target = './tests/passing'
        else:
            print("\nNo tests found")
            sys.exit(0)

    # Step 3: Run tests directly (no pytest)
    if args.test_file:
        # Run single test file
        exit_code = run_command(f'uv run --script {test_target}', f'Running test: {test_target}')
    else:
        # Run all tests in directory
        import glob
        test_files = glob.glob(f'{test_target}/test_*.py') + glob.glob(f'{test_target}/_test_*.py')
        if not test_files:
            print(f"\nNo test files found in {test_target}")
            return 0

        failed = []
        for test_file in test_files:
            exit_code = run_command(f'uv run --script {test_file}', f'Running test: {test_file}')
            if exit_code != 0:
                failed.append(test_file)

        if failed:
            print(f"\n✗ {len(failed)} test(s) failed:")
            for f in failed:
                print(f"  - {f}")
            exit_code = 1
        else:
            print(f"\n✓ All {len(test_files)} test(s) passed")
            exit_code = 0

    print(f"\n{'=' * 60}")
    if exit_code == 0:
        print("✓ All tests passed")
    else:
        print(f"✗ Tests failed with exit code {exit_code}")
    print(f"{'=' * 60}\n")

    sys.exit(exit_code)

if __name__ == '__main__':
    main()
