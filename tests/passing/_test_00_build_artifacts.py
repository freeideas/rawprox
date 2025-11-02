#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Meta-test: Verify ./release/ contains exactly what documentation specifies.

This test validates that ./tests/build.py produces the correct artifacts.
If this test fails, fix ./tests/build.py to match the documentation.
"""

import sys
# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import os
from pathlib import Path

# Change to project root
script_dir = Path(__file__).parent
# Handle being in either ./the-system/scripts/ or ./tests/failing/
if script_dir.name == 'scripts':
    project_root = script_dir.parent.parent
elif script_dir.name == 'failing':
    project_root = script_dir.parent.parent
else:
    project_root = script_dir.parent

os.chdir(project_root)

# Import the agentic coder wrapper
sys.path.insert(0, str(project_root / 'the-system' / 'scripts'))
from prompt_agentic_coder import run_prompt

def main():
    print("=" * 60)
    print("BUILD ARTIFACTS VALIDATION")
    print("=" * 60)
    print()
    print("Verifying ./release/ matches documentation...")
    print()

    # Run the validation prompt
    prompt = "Please follow these instructions: @./the-system/prompts/CHECK_BUILD_ARTIFACTS.md"
    result = run_prompt(prompt, report_type="build_artifacts")

    # Extract status from last line
    output_text = result.strip()
    lines = output_text.split('\n')
    status = lines[-1].strip() if lines else 'UNKNOWN'

    # Print the AI's analysis
    if len(lines) > 1:
        print('\n'.join(lines[:-1]))  # Print everything except last line
        print()

    # Check status
    print("=" * 60)
    if status == 'PASS':
        print("✓ BUILD ARTIFACTS MATCH DOCUMENTATION")
        print("=" * 60)
        print()
        return 0
    elif status == 'FAIL':
        print("✗ BUILD ARTIFACTS DO NOT MATCH DOCUMENTATION")
        print("=" * 60)
        print()
        print("ACTION REQUIRED:")
        print("  Fix ./tests/build.py to produce the artifacts specified")
        print("  in README.md and ./readme/ documentation.")
        print()
        print("  The documentation is the source of truth.")
        print("  The build script must be changed to match it.")
        print()
        return 1
    else:
        print(f"⚠ UNEXPECTED STATUS: {status}")
        print("=" * 60)
        print()
        print("Expected status 'PASS' or 'FAIL' on last line")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())
