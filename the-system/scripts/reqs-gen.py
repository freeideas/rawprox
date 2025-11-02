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
import hashlib
from datetime import datetime
from pathlib import Path

# Change to project root (two levels up from this script)
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
os.chdir(project_root)

# Import the agentic coder wrapper (already in same Python environment)
sys.path.insert(0, str(script_dir))
from prompt_agentic_coder import run_prompt

# Fix prompts run in order
FIX_PROMPTS = [
    'the-system/prompts/req-fix_contradictions.md',
    'the-system/prompts/req-fix_derivative.md',
    'the-system/prompts/req-fix_testability.md',
    'the-system/prompts/req-fix_coverage.md',
    'the-system/prompts/req-fix_overspec.md',
    'the-system/prompts/req-fix_sources.md',
    'the-system/prompts/req-fix_flow-structure.md'
]

def compute_reqs_hash():
    """Compute hash of all .md files in ./reqs/ directory."""
    reqs_dir = Path('./reqs')
    if not reqs_dir.exists():
        return None

    md_files = sorted(reqs_dir.glob('*.md'))
    if not md_files:
        return None

    hasher = hashlib.sha256()
    for md_file in md_files:
        with open(md_file, 'rb') as f:
            hasher.update(f.read())

    return hasher.hexdigest()

def run_fix_unique_ids():
    """Run fix-unique-req-ids.py to auto-fix duplicate IDs."""
    print("\n" + "=" * 60)
    print("PRE-CHECK: FIXING DUPLICATE REQ IDs")
    print("=" * 60 + "\n")

    cmd = ['uv', 'run', '--script', './the-system/scripts/fix-unique-req-ids.py']
    print(f"→ Running command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

    print(f"← Command finished with exit code: {result.returncode}")

    # Show output directly (no report needed since this doesn't use AI)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if result.returncode != 0:
        print(f"\nERROR: fix-unique-req-ids.py failed with exit code {result.returncode}")
        sys.exit(1)

    print()

def run_write_reqs():
    """Run the WRITE_REQS prompt to generate initial requirements."""
    print("\n" + "=" * 60)
    print("PHASE 1: WRITING INITIAL REQUIREMENTS")
    print("=" * 60 + "\n")

    # Build the prompt
    prompt = "Please follow these instructions: @the-system/prompts/WRITE_REQS.md"

    # Run agentic-coder via imported wrapper (no subprocess overhead)
    print(f"→ Running: prompt_agentic_coder.run_prompt()")

    try:
        result = run_prompt(prompt, report_type="write_reqs")
        print(f"← Command finished successfully\n")
    except Exception as e:
        print(f"\nERROR: run_prompt failed: {e}")
        sys.exit(1)

    print("✓ Phase 1 complete\n")

def run_fix_prompt(prompt_path):
    """Run a fix prompt. Returns True if README changes are required."""
    prompt_name = Path(prompt_path).stem

    print("\n" + "=" * 60)
    print(f"FIX: {prompt_name.upper()}")
    print("=" * 60 + "\n")

    # Build the prompt
    prompt = f"Please follow these instructions: @{prompt_path}"

    # Run agentic-coder via imported wrapper
    print(f"→ Running: prompt_agentic_coder.run_prompt()")
    print(f"   (Prompt: @{prompt_path})")

    try:
        response = run_prompt(prompt, report_type=prompt_name)
        print(f"← Command finished successfully")

        # Check if README changes are required
        if "**README_CHANGES_REQUIRED: true**" in response:
            return True

    except Exception as e:
        print(f"\nERROR: run_prompt failed: {e}")
        sys.exit(1)

    print(f"✓ Fix complete\n")
    return False

def main():
    print("\n" + "=" * 60)
    print("REQUIREMENTS GENERATION")
    print("=" * 60)

    # Create necessary directories
    os.makedirs('./reqs', exist_ok=True)
    os.makedirs('./reports', exist_ok=True)

    # Check if requirements already exist
    existing_reqs = list(Path('./reqs').glob('*.md'))
    reqs_exist = len(existing_reqs) > 0

    if not reqs_exist:
        # No reqs exist -- run WRITE_REQS once to create them
        print("\nNo requirements found in ./reqs/")
        print("Running WRITE_REQS to create initial requirements...\n")
        run_write_reqs()
        # After creating, fall through to validation

    # Run validation/fix loop until requirements stabilize
    iteration = 0
    max_iterations = 10  # Prevent infinite loops

    while iteration < max_iterations:
        iteration += 1

        print(f"\n{'=' * 60}")
        print(f"VALIDATION/FIX ITERATION {iteration}")
        print(f"{'=' * 60}\n")

        # Compute signature before fixes
        sig_before = compute_reqs_hash()
        print(f"→ Signature before: {sig_before}\n")

        # Phase 0: Fix duplicate IDs (always run)
        run_fix_unique_ids()

        # Phase 1: Run all fix prompts in order
        for prompt_path in FIX_PROMPTS:
            readme_changes_required = run_fix_prompt(prompt_path)

            if readme_changes_required:
                print("=" * 60)
                print("⚠ README CHANGES REQUIRED")
                print("=" * 60)
                print("\nThe requirements validation identified issues that cannot be fixed")
                print("by editing the requirements files. The README documentation needs to")
                print("be updated to resolve these issues.")
                print(f"\nPlease review the report in ./reports/ for details on what needs")
                print("to be clarified or added to the README files.")
                print("\nAfter updating the README files, re-run this script to continue.\n")
                sys.exit(1)

        # Compute signature after fixes
        sig_after = compute_reqs_hash()
        print(f"→ Signature after: {sig_after}\n")

        # Check if anything changed
        if sig_before == sig_after:
            print("=" * 60)
            print("✓ REQUIREMENTS GENERATION COMPLETE")
            print("=" * 60)
            print(f"\nNo changes detected. All requirements are valid.")
            print(f"Total validation iterations: {iteration}\n")
            sys.exit(0)
        else:
            print(f"→ Requirements modified. Running another iteration...\n")

    # If we get here, we've exceeded max iterations
    print(f"\nERROR: Exceeded maximum iterations ({max_iterations})")
    print("Requirements still changing after all iterations.")
    sys.exit(1)

if __name__ == '__main__':
    main()
