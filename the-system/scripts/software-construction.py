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
import sqlite3
from datetime import datetime
from pathlib import Path

# Change to project root (two levels up from this script)
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
os.chdir(project_root)

# Import the agentic coder wrapper
sys.path.insert(0, str(script_dir))
from prompt_agentic_coder import run_prompt

def timestamp():
    """Get current timestamp string."""
    return datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

def write_report(report_type, content, extra_info=None):
    """Write a report file and return the path."""
    ts = timestamp()
    report_path = Path(f"./reports/{ts}_{report_type}.md")

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# {report_type.replace('_', ' ').title()} Report\n\n")
        f.write(f"**Timestamp:** {ts}\n\n")
        if extra_info:
            f.write(f"{extra_info}\n\n")
        f.write("---\n\n")
        f.write(content)

    return report_path

def run_build_req_index():
    """Run build-req-index.py to rebuild the requirements database."""
    print("\n" + "=" * 60)
    print("BUILDING REQUIREMENTS INDEX")
    print("=" * 60 + "\n")

    cmd = ['uv', 'run', '--script', './the-system/scripts/build-req-index.py']
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"\nERROR: build-req-index.py failed with exit code {result.returncode}")
        sys.exit(1)

def query_db(query):
    """Execute a query against the requirements database."""
    conn = sqlite3.connect('./tmp/reqs.sqlite')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

def handle_missing_build_script():
    """Create ./tests/build.py based on README.md."""
    print("\n" + "=" * 60)
    print("WORK ITEM: missing_build_script")
    print("=" * 60 + "\n")

    # Check if README.md exists
    if not os.path.exists('./README.md'):
        print("ERROR: ./README.md does not exist")
        print("Please create README.md with project and build information")
        sys.exit(1)

    # Build prompt
    prompt = "Please follow these instructions: @./the-system/prompts/BUILD_SCRIPT.md"

    print(f"→ Running: prompt_agentic_coder.run_prompt()")
    result = run_prompt(prompt)
    print(f"← Command finished")

    # Write report
    report_content = "## Prompt\n\n```\n" + prompt[:500] + ("..." if len(prompt) > 500 else "") + "\n```\n\n"
    report_content += "## Result\n\n```\n" + result + "\n```\n\n"

    report_path = write_report("missing_build_script", report_content)
    print(f"✓ Report written: {report_path}\n")

    # Check if AI indicated insufficient README info
    if "INSUFFICIENT_BUILD_INFO" in result:
        print("\n" + "=" * 60)
        print("⚠ README.md LACKS BUILD INFORMATION")
        print("=" * 60)
        print("\nThe README.md does not contain enough information to create build.py")
        print(f"Report: {report_path}\n")
        print("ACTION REQUIRED:")
        print("1. Read the report to see what information is missing")
        print("2. Update README.md with the required build details")
        print("3. Re-run this script\n")
        sys.exit(2)

    # Verify build.py was created
    if not os.path.exists('./tests/build.py'):
        print("\nERROR: ./tests/build.py was not created")
        print(f"See report: {report_path}")
        sys.exit(1)

    print("✓ Created ./tests/build.py\n")

    # Copy build artifacts validation test to failing tests
    artifacts_test_src = './the-system/scripts/_test_build_artifacts.py'
    artifacts_test_dst = './tests/failing/_test_build_artifacts.py'

    if os.path.exists(artifacts_test_src):
        import shutil
        shutil.copy2(artifacts_test_src, artifacts_test_dst)
        print("✓ Copied _test_build_artifacts.py to ./tests/failing/")
        print("  (This test validates that build.py produces the correct artifacts)\n")

    return True  # work was done

def handle_orphan_req_ids(orphans):
    """Remove orphan $REQ_ID tags from tests and code."""
    print("\n" + "=" * 60)
    print("WORK ITEM: orphan_req_id")
    print("=" * 60 + "\n")

    # Build list of orphans with locations
    orphan_info = []
    for req_id, in orphans:
        locations = query_db(f"SELECT filespec, line_num FROM req_locations WHERE req_id = '{req_id}' AND category IN ('tests', 'code')")
        orphan_info.append(f"  {req_id}:")
        for filespec, line_num in locations:
            orphan_info.append(f"    - {filespec}:{line_num}")

    orphan_text = "\n".join(orphan_info)
    print(f"Found {len(orphans)} orphan $REQ_IDs:\n{orphan_text}\n")

    # Build prompt
    prompt = f"Please follow these instructions: @./the-system/prompts/REMOVE_ORPHAN_REQS.md\n\nOrphan $REQ_IDs to remove:\n{orphan_text}"

    print(f"→ Running: prompt_agentic_coder.run_prompt()")
    result = run_prompt(prompt)
    print(f"← Command finished")

    # Write report
    report_content = f"**Orphans found:** {len(orphans)}\n\n"
    report_content += "## Orphan $REQ_IDs\n\n```\n" + orphan_text + "\n```\n\n"
    report_content += "## Result\n\n```\n" + result + "\n```\n\n"

    report_path = write_report("orphan_req_id", report_content)
    print(f"✓ Report written: {report_path}\n")

    print(f"✓ Removed {len(orphans)} orphan $REQ_IDs\n")
    return True  # work was done

def handle_untested_req(untested):
    """Write test for the first untested requirement."""
    print("\n" + "=" * 60)
    print("WORK ITEM: untested_req")
    print("=" * 60 + "\n")

    # Get first untested req
    req_id = untested[0][0]

    # Get flow file for this req
    flow_info = query_db(f"SELECT flow_file, req_text, source_attribution FROM req_definitions WHERE req_id = '{req_id}'")
    if not flow_info:
        print(f"ERROR: Could not find definition for {req_id}")
        sys.exit(1)

    flow_file, req_text, source_attribution = flow_info[0]

    print(f"Creating test for: {req_id}")
    print(f"  Flow file: {flow_file}")
    print(f"  Requirement: {req_text[:80]}...")
    print()

    # Build prompt with context
    prompt = f"Please follow these instructions: @./the-system/prompts/WRITE_TEST.md\n\n"
    prompt += f"Create test for requirement:\n"
    prompt += f"  $REQ_ID: {req_id}\n"
    prompt += f"  Flow file: {flow_file}\n"
    prompt += f"  Source: {source_attribution}\n"
    prompt += f"  Requirement text: {req_text}\n"

    print(f"→ Running: prompt_agentic_coder.run_prompt()")
    result = run_prompt(prompt)
    print(f"← Command finished")

    # Write report
    report_content = f"**$REQ_ID:** {req_id}\n"
    report_content += f"**Flow file:** {flow_file}\n\n"
    report_content += "## Result\n\n```\n" + result + "\n```\n\n"

    report_path = write_report("untested_req", report_content)
    print(f"✓ Report written: {report_path}\n")

    print(f"✓ Created test for {req_id}\n")
    return True  # work was done

def handle_failing_test(failing_tests):
    """Fix code to make the first failing test pass."""
    print("\n" + "=" * 60)
    print("WORK ITEM: failing_test")
    print("=" * 60 + "\n")

    # Get first failing test
    test_file = failing_tests[0]
    print(f"Fixing test: {test_file}\n")

    # Run the test to get failure output
    print("→ Running test to capture failure output...")
    # Use uv run --script to run test.py (same pattern that works in reqs-gen.py)
    test_cmd = ['uv', 'run', '--script', './the-system/scripts/test.py', test_file]
    # Write output to file instead of capturing in memory (avoid Windows subprocess issues)
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False, suffix='.txt') as f:
        temp_output_file = f.name
    try:
        with open(temp_output_file, 'w', encoding='utf-8') as f:
            test_result = subprocess.run(test_cmd, stdout=f, stderr=subprocess.STDOUT, text=True)
        with open(temp_output_file, 'r', encoding='utf-8') as f:
            test_output = f.read()
    finally:
        if os.path.exists(temp_output_file):
            os.unlink(temp_output_file)
    print(f"← Test completed with exit code: {test_result.returncode}\n")

    # Build prompt with test failure context
    prompt = f"Please follow these instructions: @./the-system/prompts/FIX_FAILING_TEST.md\n\n"
    prompt += f"Failing test: {test_file}\n\n"
    prompt += f"Test output:\n```\n{test_output}\n```\n"

    print(f"→ Running: prompt_agentic_coder.run_prompt()")
    result = run_prompt(prompt)
    print(f"← Command finished")

    # Write report
    report_content = f"**Test file:** {test_file}\n\n"
    report_content += "## Test Output (before fix)\n\n```\n" + test_output + "\n```\n\n"
    report_content += "## Result\n\n```\n" + result + "\n```\n\n"

    report_path = write_report("failing_test", report_content)
    print(f"✓ Report written: {report_path}\n")

    # Run test again to verify it passes
    print("→ Running test again to verify fix...")
    test_result = subprocess.run(test_cmd, capture_output=True, text=True, encoding='utf-8')
    print(f"← Test completed with exit code: {test_result.returncode}\n")

    if test_result.returncode == 0:
        # Move test to passing
        test_filename = Path(test_file).name
        dest = f"./tests/passing/{test_filename}"
        os.makedirs('./tests/passing', exist_ok=True)
        os.rename(test_file, dest)
        print(f"✓ Test passes! Moved to {dest}\n")
    else:
        print(f"⚠ Test still failing after fix attempt\n")
        print("Test output:\n" + test_result.stdout + "\n" + test_result.stderr)

    return True  # work was done

def run_final_test_verification():
    """Run final test verification (test.py will run passing tests if no failing tests exist)."""
    print("\n" + "=" * 60)
    print("FINAL VERIFICATION: Running all tests")
    print("=" * 60 + "\n")

    print("→ Running test.py (will run passing tests since no failing tests exist)...")
    cmd = ['uv', 'run', '--script', './the-system/scripts/test.py']
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    # Write report
    report_content = f"**Exit code:** {result.returncode}\n\n"
    report_content += "## Test Output\n\n```\n" + result.stdout + "\n```\n\n"
    if result.stderr:
        report_content += "## STDERR\n\n```\n" + result.stderr + "\n```\n"

    report_path = write_report("final_verification", report_content)
    print(f"\n✓ Report written: {report_path}\n")

    if result.returncode != 0:
        print("=" * 60)
        print("⚠ FINAL VERIFICATION FAILED")
        print("=" * 60)
        print("\nSome tests failed during final verification.")
        print(f"Report: {report_path}\n")
        print("This may indicate a regression or flaky test.")
        print("Please investigate and manually move failed tests to ./tests/failing/ if needed.\n")
        sys.exit(1)

    return True  # verification passed

def main():
    print("\n" + "=" * 60)
    print("SOFTWARE CONSTRUCTION")
    print("=" * 60)

    # Create necessary directories
    os.makedirs('./tests/failing', exist_ok=True)
    os.makedirs('./tests/passing', exist_ok=True)
    os.makedirs('./reports', exist_ok=True)
    os.makedirs('./code', exist_ok=True)
    os.makedirs('./release', exist_ok=True)

    iteration = 0
    max_iterations = 100

    while iteration < max_iterations:
        iteration += 1

        print(f"\n{'=' * 60}")
        print(f"ITERATION {iteration}")
        print(f"{'=' * 60}\n")

        # Step 1: Check if build.py exists
        if not os.path.exists('./tests/build.py'):
            work_done = handle_missing_build_script()
            if work_done:
                continue  # restart from top

        # Step 2: Build requirements index
        run_build_req_index()

        # Step 3: Check for orphan req_ids
        orphans = query_db("""
            SELECT DISTINCT req_id FROM req_locations
            WHERE category IN ('tests', 'code')
              AND req_id NOT IN (SELECT req_id FROM req_definitions)
        """)
        if orphans:
            work_done = handle_orphan_req_ids(orphans)
            if work_done:
                continue  # restart from top

        # Step 4: Check for untested requirements
        untested = query_db("""
            SELECT DISTINCT req_id FROM req_definitions
            WHERE req_id NOT IN (SELECT req_id FROM req_locations WHERE category = 'tests')
        """)
        if untested:
            work_done = handle_untested_req(untested)
            if work_done:
                continue  # restart from top

        # Step 5: Check for failing tests
        failing_tests = []
        if os.path.exists('./tests/failing'):
            for filename in os.listdir('./tests/failing'):
                if (filename.startswith('test_') or filename.startswith('_test_')) and filename.endswith('.py'):
                    failing_tests.append(os.path.join('./tests/failing', filename))

        # Sort so infrastructure tests (_test_*.py) come before requirement tests (test_*.py)
        # Infrastructure tests like _test_build_artifacts.py must pass first because
        # they validate the build output that other tests depend on
        failing_tests.sort(key=lambda x: (not os.path.basename(x).startswith('_test_'), x))

        if failing_tests:
            work_done = handle_failing_test(failing_tests)
            if work_done:
                continue  # restart from top

        # If we get here, no work items remain -- run final verification
        # test.py will automatically run passing tests since no failing tests exist
        run_final_test_verification()

        # All work is done!
        print("=" * 60)
        print("✓ SOFTWARE CONSTRUCTION COMPLETE")
        print("=" * 60)
        print(f"\nAll requirements have been implemented and tested!")
        print(f"Total iterations: {iteration}")

        # Print summary
        conn = sqlite3.connect('./tmp/reqs.sqlite')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(DISTINCT req_id) FROM req_definitions')
        total_reqs = cursor.fetchone()[0]
        conn.close()

        passing_tests = len([f for f in os.listdir('./tests/passing') if f.startswith('test_')])

        print(f"\nSummary:")
        print(f"  Requirements implemented: {total_reqs}")
        print(f"  Tests passing: {passing_tests}")
        print(f"  Build artifacts: ./release/\n")

        sys.exit(0)

    # If we get here, we've exceeded max iterations
    print(f"\nERROR: Exceeded maximum iterations ({max_iterations})")
    print("Software construction is incomplete.")
    sys.exit(1)

if __name__ == '__main__':
    main()
