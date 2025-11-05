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

def run_fix_unique_ids():
    """Run fix-unique-req-ids.py to auto-fix duplicate IDs."""
    print("\n" + "=" * 60)
    print("PRE-CHECK: FIXING DUPLICATE REQ IDs")
    print("=" * 60 + "\n")

    cmd = ['uv', 'run', '--script', './the-system/scripts/fix-unique-req-ids.py']
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=60)

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print("\n" + "=" * 60)
        print("EXIT: fix-unique-req-ids.py FAILED")
        print("=" * 60)
        print(f"\nERROR: fix-unique-req-ids.py failed with exit code {result.returncode}\n")
        sys.exit(1)

def run_build_req_index():
    """Run build-req-index.py to rebuild the requirements database."""
    print("\n" + "=" * 60)
    print("BUILDING REQUIREMENTS INDEX")
    print("=" * 60 + "\n")

    cmd = ['uv', 'run', '--script', './the-system/scripts/build-req-index.py']
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=60)

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print("\n" + "=" * 60)
        print("EXIT: build-req-index.py FAILED")
        print("=" * 60)
        print(f"\nERROR: build-req-index.py failed with exit code {result.returncode}\n")
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
        print("\n" + "=" * 60)
        print("EXIT: README.md MISSING")
        print("=" * 60)
        print("\nERROR: ./README.md does not exist")
        print("Please create README.md with project and build information\n")
        sys.exit(1)

    # Build prompt
    prompt = "Please follow these instructions: @./the-system/prompts/BUILD_SCRIPT.md"

    print(f"→ Running: prompt_agentic_coder.run_prompt()")
    result = run_prompt(prompt, report_type="missing_build_script")
    print(f"← Command finished\n")

    # Check if AI indicated insufficient README info
    if "INSUFFICIENT_BUILD_INFO" in result:
        print("\n" + "=" * 60)
        print("EXIT: README.md LACKS BUILD INFORMATION")
        print("=" * 60)
        print("\nThe README.md does not contain enough information to create build.py\n")
        print("ACTION REQUIRED:")
        print("1. Read the latest report in ./reports/ to see what information is missing")
        print("2. Update README.md with the required build details")
        print("3. Re-run this script\n")
        sys.exit(2)

    # Verify build.py was created
    if not os.path.exists('./tests/build.py'):
        print("\n" + "=" * 60)
        print("EXIT: build.py NOT CREATED")
        print("=" * 60)
        print("\nERROR: ./tests/build.py was not created")
        print("See latest report in ./reports/\n")
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
    result = run_prompt(prompt, report_type="orphan_req_id")
    print(f"← Command finished\n")

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
        print("\n" + "=" * 60)
        print("EXIT: REQUIREMENT NOT FOUND IN DATABASE")
        print("=" * 60)
        print(f"\nERROR: Could not find definition for {req_id}")
        print("This may indicate a database inconsistency.\n")
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
    result = run_prompt(prompt, report_type="untested_req")
    print(f"← Command finished\n")

    print(f"✓ Created test for {req_id}\n")
    return True  # work was done

def handle_test_ordering():
    """Ensure tests are ordered from general/foundational to specific/advanced."""
    print("\n" + "=" * 60)
    print("WORK ITEM: order_tests")
    print("=" * 60 + "\n")

    # Build prompt
    prompt = "Please follow these instructions: @./the-system/prompts/ORDER_TESTS.md"

    print(f"→ Running: prompt_agentic_coder.run_prompt()")
    result = run_prompt(prompt, report_type="order_tests")
    print(f"← Command finished\n")

    print("✓ Tests analyzed and ordered\n")

def handle_single_test_until_passes(test_file):
    """Fix code to make a single test pass, retrying until it succeeds."""
    test_name = os.path.basename(test_file)

    print("\n" + "=" * 60)
    print(f"PROCESSING TEST: {test_name}")
    print(f"Path: {test_file}")
    print("=" * 60 + "\n")

    # Check if test file exists
    if not os.path.exists(test_file):
        print(f"⚠ Test file does not exist: {test_file}")
        print(f"  (May have been moved to ./tests/passing/)\n")
        return False  # No failure occurred

    # Build requirements index before running test
    run_build_req_index()

    attempt = 0
    max_attempts = 10  # If test can't be fixed after 10 attempts, there's a systemic problem

    while attempt < max_attempts:
        attempt += 1
        print(f"\n{'─' * 60}")
        print(f"TEST: {test_name} | Attempt {attempt}/{max_attempts}")
        print(f"{'─' * 60}\n")

        # Check if test file still exists (may have been moved by AI)
        if not os.path.exists(test_file):
            print(f"⚠ Test file no longer exists: {test_file}")
            print(f"  (May have been moved to ./tests/passing/)\n")
            return False  # No failure occurred

        # Run the test to check if it passes
        print(f"→ Running {test_name}...")
        # Use uv run --script to run test.py (same pattern that works in reqs-gen.py)
        test_cmd = ['uv', 'run', '--script', './the-system/scripts/test.py', test_file]
        # Capture output to find the report file path
        test_result = None
        test_output = ""
        report_file_path = None

        try:
            # Run test and capture output to find report file
            try:
                result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=3600)
                test_result = result
                captured_output = result.stdout + result.stderr
            except subprocess.TimeoutExpired:
                # Test timed out -- create a result object indicating timeout
                test_result = type('obj', (object,), {'returncode': -1})()
                captured_output = "[ERROR] Test execution timed out after 3600 seconds\n"

            # Look for "report file: " line in captured output
            for line in captured_output.splitlines():
                if line.startswith("report file: "):
                    report_file_path = line[len("report file: "):].strip()
                    break

            # Read the actual test report (clean, without build output)
            if report_file_path and os.path.exists(report_file_path):
                with open(report_file_path, 'r', encoding='utf-8') as f:
                    test_output = f.read()
            else:
                # Fallback to captured output if report file not found
                test_output = captured_output

        except Exception as e:
            test_result = type('obj', (object,), {'returncode': -1})()
            test_output = f"Error running test: {e}\n"

        print(f"← Test completed with exit code: {test_result.returncode}\n")

        # If test passes, move it to passing and return
        if test_result.returncode == 0:
            test_filename = Path(test_file).name
            dest = f"./tests/passing/{test_filename}"
            os.makedirs('./tests/passing', exist_ok=True)
            os.rename(test_file, dest)

            if attempt == 1:
                print(f"✓ Test passed on first try! Moved to {dest}\n")
                return False  # No failure occurred
            else:
                print(f"✓ Test passes after {attempt-1} fix(es)! Moved to {dest}\n")
                return True  # Failure occurred but was fixed

        # Test failed - ask AI to fix it
        print(f"✗ Test failed, asking AI to fix...\n")

        # Build prompt with test failure context
        prompt = f"Please follow these instructions: @./the-system/prompts/FIX_FAILING_TEST.md\n\n"
        prompt += f"Failing test: {test_file}\n"
        prompt += f"Attempt: {attempt}/{max_attempts}\n\n"
        prompt += f"Test output:\n```\n{test_output}\n```\n"

        print(f"→ Running: prompt_agentic_coder.run_prompt()")
        result = run_prompt(prompt, report_type="failing_test")
        print(f"← Command finished\n")

        # Rebuild requirements index after AI made changes
        run_build_req_index()

        # Loop continues to re-test

    # If we get here, we exceeded max attempts
    print("\n" + "=" * 60)
    print(f"ERROR: Could not fix test after {max_attempts} attempts")
    print("=" * 60)
    print(f"\nTest: {test_file}")
    print(f"This test could not be fixed after {max_attempts} attempts.")
    print("Please review the most recent reports in ./reports/\n")
    sys.exit(1)

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

    # ========================================================================
    # SETUP PHASE (runs once)
    # ========================================================================

    print("\n" + "=" * 60)
    print("SETUP PHASE")
    print("=" * 60 + "\n")

    # Step 1: Check if build.py exists
    if not os.path.exists('./tests/build.py'):
        handle_missing_build_script()

    # Step 2: Fix any duplicate req_ids before building index
    run_fix_unique_ids()

    # Step 3: Build requirements index
    run_build_req_index()

    # Step 4: Remove orphan req_ids
    orphans = query_db("""
        SELECT DISTINCT req_id FROM req_locations
        WHERE category IN ('tests', 'code')
          AND req_id NOT IN (SELECT req_id FROM req_definitions)
    """)
    if orphans:
        handle_orphan_req_ids(orphans)
        run_build_req_index()  # Rebuild after cleanup

    # Step 5: Write tests for all untested requirements
    tests_were_written = False
    while True:
        untested = query_db("""
            SELECT DISTINCT req_id FROM req_definitions
            WHERE req_id NOT IN (SELECT req_id FROM req_locations WHERE category = 'tests')
        """)
        if not untested:
            break
        handle_untested_req(untested)
        run_build_req_index()  # Rebuild after writing tests
        tests_were_written = True

    # Step 6: Order tests by dependency (only if new tests were written)
    if tests_were_written:
        handle_test_ordering()

    print("\n" + "=" * 60)
    print("✓ SETUP COMPLETE")
    print("=" * 60)
    print("\nAll tests written and ordered. Beginning test processing...\n")

    # ========================================================================
    # MAIN TEST LOOP - Process tests until failing directory is empty
    # ========================================================================

    while True:
        # Get alphabetically first test from failing directory
        failing_tests = []
        if os.path.exists('./tests/failing'):
            for filename in os.listdir('./tests/failing'):
                if (filename.startswith('test_') or filename.startswith('_test_')) and filename.endswith('.py'):
                    failing_tests.append(os.path.join('./tests/failing', filename))

        # Sort alphabetically - numeric prefixes ensure proper order
        failing_tests.sort()

        if not failing_tests:
            # No tests in failing directory - we're done!
            print("\n" + "=" * 60)
            print("✓ ALL TESTS PASSING")
            print("=" * 60)
            print(f"\nAll requirements have been implemented and tested!\n")

            # Print summary
            conn = sqlite3.connect('./tmp/reqs.sqlite')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(DISTINCT req_id) FROM req_definitions')
            total_reqs = cursor.fetchone()[0]
            conn.close()

            passing_tests = len([f for f in os.listdir('./tests/passing') if f.startswith('test_') or f.startswith('_test_')])

            print(f"Summary:")
            print(f"  Requirements implemented: {total_reqs}")
            print(f"  Tests passing: {passing_tests}")
            print(f"  Build artifacts: ./release/\n")

            print("=" * 60)
            print("EXIT: SUCCESS")
            print("=" * 60)
            print("\nAll requirements implemented and all tests passing.\n")
            sys.exit(0)

        # Process the first failing test
        test_file = failing_tests[0]
        handle_single_test_until_passes(test_file)

if __name__ == '__main__':
    main()
