#!/usr/bin/env uvrun
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import sys
import io

# Ensure UTF-8 encoding on all platforms
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("→ reqs-gen.py: Script starting...")

import os
import subprocess
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
import concurrent.futures

# Change to project root (two levels up from this script)
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
os.chdir(project_root)

# Import the agentic coder wrapper (already in same Python environment)
sys.path.insert(0, str(script_dir))
from prompt_agentic_coder import get_ai_response_text

def find_most_recent_report():
    """Find the most recent report file in ./reports/ directory."""
    reports_dir = Path('./reports')
    if not reports_dir.exists():
        return None

    report_files = list(reports_dir.glob('*.md'))
    if not report_files:
        return None

    # Sort by modification time, most recent first
    report_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return report_files[0]

def prompt_user_to_continue():
    """Prompt user to review report and decide whether to continue."""
    recent_report = find_most_recent_report()

    print("\n" + "=" * 60)
    print("README QUALITY ISSUES DETECTED")
    print("=" * 60)

    if recent_report:
        print(f"\nPlease review the report: {recent_report}")
    else:
        print("\nPlease review the most recent report in the ./reports/ directory.")

    print("\nAfter reviewing the report, you can decide whether to continue:")
    print("  - Press Ctrl-C to stop and fix the README documents")
    print("  - Press Enter to continue if you believe the README documents")
    print("    are good enough for generating or perfecting requirements")
    print()

    try:
        input("Your choice: ")
        print("\nContinuing with requirements generation...\n")
    except KeyboardInterrupt:
        print("\n\nStopped by user. Please fix README documents and re-run.\n")
        sys.exit(1)

def run_check_readmes():
    """Check README quality before generating requirements. Prompts user if problems found."""
    print("\n" + "=" * 60)
    print("PHASE 0: CHECKING README QUALITY")
    print("=" * 60 + "\n")

    prompt = "Please follow these instructions: @the-system/prompts/req-check_readmes.md"

    print(f"→ Running: prompt_agentic_coder.get_ai_response_text()")
    print(f"   (Prompt: @the-system/prompts/req-check_readmes.md)")

    try:
        response = get_ai_response_text(prompt, report_type="req-check_readmes")
        print(f"← Command finished successfully\n")

        # Check if README changes are required
        if "**README_CHANGES_REQUIRED: true**" in response:
            prompt_user_to_continue()

    except Exception as e:
        print(f"\nERROR: get_ai_response_text failed: {e}")
        sys.exit(1)

    print("✓ README quality check passed\n")

def find_fix_prompts():
    """Find all req-fix_*.md prompts in the-system/prompts/."""
    prompts_dir = Path('the-system/prompts')
    fix_prompts = sorted(prompts_dir.glob('req-fix_*.md'))
    return [str(p) for p in fix_prompts]

def run_single_fix_prompt(prompt_path):
    """Run a single fix prompt. Returns dict with results."""
    prompt_name = Path(prompt_path).stem

    print(f"  → Starting: {prompt_name}")

    try:
        prompt = f"Please follow these instructions: @{prompt_path}"
        response = get_ai_response_text(prompt, report_type=prompt_name)

        readme_changes_required = "**README_CHANGES_REQUIRED: true**" in response

        print(f"  ← Finished: {prompt_name}")

        return {
            'prompt_path': prompt_path,
            'prompt_name': prompt_name,
            'readme_changes_required': readme_changes_required,
            'success': True
        }
    except Exception as e:
        print(f"  ✗ Failed: {prompt_name} - {e}")
        return {
            'prompt_path': prompt_path,
            'prompt_name': prompt_name,
            'readme_changes_required': False,
            'success': False,
            'error': str(e)
        }

def run_all_fix_prompts_in_parallel():
    """Run all req-fix_*.md prompts in parallel. Returns True if any require README changes."""
    fix_prompts = find_fix_prompts()

    if not fix_prompts:
        print("WARNING: No req-fix_*.md prompts found\n")
        return False

    print("\n" + "=" * 60)
    print("RUNNING FIX PROMPTS IN PARALLEL")
    print("=" * 60 + "\n")
    print(f"Found {len(fix_prompts)} fix prompts:")
    for p in fix_prompts:
        print(f"  - {p}")
    print("\nLaunching parallel execution...\n")

    # Run all fix prompts in parallel using ThreadPoolExecutor
    readme_changes_required = False
    failed_prompts = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(fix_prompts)) as executor:
        # Submit all prompts
        future_to_prompt = {
            executor.submit(run_single_fix_prompt, prompt_path): prompt_path
            for prompt_path in fix_prompts
        }

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_prompt):
            result = future.result()

            if not result['success']:
                failed_prompts.append(result['prompt_name'])

            if result['readme_changes_required']:
                readme_changes_required = True

    print()

    # Check for failures
    if failed_prompts:
        print(f"ERROR: {len(failed_prompts)} fix prompt(s) failed:")
        for name in failed_prompts:
            print(f"  - {name}")
        print()
        sys.exit(1)

    if readme_changes_required:
        return True

    print("✓ All fix prompts complete\n")
    return False

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
    print(f"→ Running: prompt_agentic_coder.get_ai_response_text()")

    try:
        result = get_ai_response_text(prompt, report_type="write_reqs")
        print(f"← Command finished successfully\n")
    except Exception as e:
        print(f"\nERROR: get_ai_response_text failed: {e}")
        sys.exit(1)

    print("✓ Phase 1 complete\n")

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Generate requirements from README documentation')
    parser.add_argument('--skip-readme-check', action='store_true',
                       help='Skip the initial README quality check')
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("REQUIREMENTS GENERATION")
    print("=" * 60)

    # Create necessary directories
    os.makedirs('./reqs', exist_ok=True)
    os.makedirs('./reports', exist_ok=True)

    # Phase 0: Check README quality ONCE before proceeding
    # This validates source documentation before generating requirements
    if not args.skip_readme_check:
        run_check_readmes()
    else:
        print("\n⚠ Skipping README quality check (--skip-readme-check flag set)\n")

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
    max_iterations = 5  # Prevent infinite loops

    while iteration < max_iterations:
        iteration += 1

        print(f"\n{'=' * 60}")
        print(f"VALIDATION/FIX ITERATION {iteration}")
        print(f"{'=' * 60}\n")

        # Compute signature before fixes
        sig_before = compute_reqs_hash()
        print(f"→ Signature before: {sig_before}\n")

        # Phase 1: Fix duplicate IDs (must run serially since it edits files)
        run_fix_unique_ids()

        # Phase 2: Run all fix prompts IN PARALLEL
        readme_changes_required = run_all_fix_prompts_in_parallel()

        if readme_changes_required:
            prompt_user_to_continue()

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
