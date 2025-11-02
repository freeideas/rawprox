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
    'the-system/prompts/fix_req-contradictions.md',
    'the-system/prompts/fix_req-derivative.md',
    'the-system/prompts/fix_req-testability.md',
    'the-system/prompts/fix_req-coverage.md',
    'the-system/prompts/fix_req-overspec.md',
    'the-system/prompts/fix_req-sources.md',
    'the-system/prompts/fix_req-flow-structure.md'
]

def timestamp():
    """Get current timestamp string."""
    return datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

def write_report(report_type, content):
    """Write a markdown report file and return the path."""
    ts = timestamp()
    report_path = Path(f"./reports/{ts}_{report_type}.md")

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return report_path

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
        result = run_prompt(prompt)
        print(f"← Command finished successfully")
    except Exception as e:
        print(f"\nERROR: run_prompt failed: {e}")
        sys.exit(1)

    # Write report
    report_content = f"""# WRITE_REQS Report
**Timestamp:** {timestamp()}

---

## Output

{result}
"""

    report_path = write_report("write_reqs", report_content)
    print(f"✓ Report written: {report_path}\n")

    print("✓ Phase 1 complete\n")

def run_fix_prompt(prompt_path):
    """Run a fix prompt."""
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
        output_text = run_prompt(prompt)
        print(f"← Command finished successfully")
    except Exception as e:
        print(f"\nERROR: run_prompt failed: {e}")

        # Write error report
        report_content = f"""# {prompt_name.upper()} - ERROR
**Timestamp:** {timestamp()}
**Error:** {e}

---

## Error Details

{str(e)}
"""

        report_path = write_report(f"{prompt_name}_ERROR", report_content)
        print(f"✓ Error report written: {report_path}")
        sys.exit(1)

    # Extract status from last line
    lines = output_text.strip().split('\n')
    status = lines[-1].strip() if lines else 'UNKNOWN'

    # Validate status
    valid_statuses = ['GOODENUF', 'NEEDIMPROV', 'READMEBUG']
    if status not in valid_statuses:
        print(f"\nERROR: Invalid status '{status}' (expected one of: {', '.join(valid_statuses)})")

        # Write error report
        report_content = f"""# {prompt_name.upper()} - PARSE ERROR
**Timestamp:** {timestamp()}
**Error:** Failed to extract valid status from last line

**Last line:** {status}
**Expected:** One of {', '.join(valid_statuses)}

---

## Output

{output_text}
"""

        report_path = write_report(f"{prompt_name}_PARSE_ERROR", report_content)
        print(f"✓ Error report written: {report_path}")
        sys.exit(1)

    print(f"✓ Fix complete: {status}\n")

    # Write report (full output as markdown)
    report_content = f"""# {prompt_name.upper()}
**Timestamp:** {timestamp()}
**Status:** {status}

---

{output_text}
"""

    report_path = write_report(prompt_name, report_content)
    print(f"✓ Report written: {report_path}\n")

    # Check for READMEBUG status
    if status == 'READMEBUG':
        print("=" * 60)
        print("⚠ README DOCUMENTATION ISSUES DETECTED")
        print("=" * 60)
        print(f"\nThe {prompt_name} check found issues with README documentation.")
        print(f"Report: {report_path}\n")
        print("\nACTION REQUIRED:")
        print("1. Read the report to understand the README issues")
        print("2. Revise the README documentation to address the issues")
        print("3. Re-run this script\n")
        sys.exit(2)

    return status

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

    # If reqs exist (or were just created), run validation/fix loop
    iteration = 0
    max_iterations = 10  # Prevent infinite loops

    while iteration < max_iterations:
        iteration += 1

        print(f"\n{'=' * 60}")
        print(f"VALIDATION/FIX ITERATION {iteration}")
        print(f"{'=' * 60}\n")

        # Compute hash before fixes
        hash_before = compute_reqs_hash()
        print(f"→ Hash before: {hash_before}\n")

        # Phase 0: Fix duplicate IDs (always run)
        run_fix_unique_ids()

        # Phase 1: Run all fix prompts in order
        for prompt_path in FIX_PROMPTS:
            run_fix_prompt(prompt_path)
            # If READMEBUG detected, script exits above

        # Compute hash after fixes
        hash_after = compute_reqs_hash()
        print(f"→ Hash after: {hash_after}\n")

        # Check if anything changed
        if hash_before == hash_after:
            print("=" * 60)
            print("✓ REQUIREMENTS GENERATION COMPLETE")
            print("=" * 60)
            print(f"\nNo changes detected. All requirements are valid.")
            print(f"Total validation iterations: {iteration}\n")
            sys.exit(0)
        else:
            print(f"→ Requirements changed. Running another iteration...\n")

    # If we get here, we've exceeded max iterations
    print(f"\nERROR: Exceeded maximum iterations ({max_iterations})")
    print("Requirements still changing after all iterations.")
    sys.exit(1)

if __name__ == '__main__':
    main()
