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
        print("EXIT: README.md LACKS BUILD INFORMATION")
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
        print("\n" + "=" * 60)
        print("EXIT: build.py NOT CREATED")
        print("=" * 60)
        print("\nERROR: ./tests/build.py was not created")
        print(f"See report: {report_path}\n")
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

def handle_test_ordering():
    """Ensure tests are ordered from general/foundational to specific/advanced."""
    print("\n" + "=" * 60)
    print("WORK ITEM: order_tests")
    print("=" * 60 + "\n")

    # Build prompt
    prompt = "Please follow these instructions: @./the-system/prompts/ORDER_TESTS.md"

    print(f"→ Running: prompt_agentic_coder.run_prompt()")
    result = run_prompt(prompt)
    print(f"← Command finished")

    # Write report
    report_content = "## Prompt\n\n```\n" + prompt + "\n```\n\n"
    report_content += "## Result\n\n```\n" + result + "\n```\n\n"

    report_path = write_report("order_tests", report_content)
    print(f"✓ Report written: {report_path}\n")

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
        # Write output to file instead of capturing in memory (avoid Windows subprocess issues)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False, suffix='.txt') as f:
            temp_output_file = f.name

        test_output = ""
        test_result = None
        try:
            # Run test and capture output to file
            try:
                with open(temp_output_file, 'w', encoding='utf-8') as f:
                    test_result = subprocess.run(test_cmd, stdout=f, stderr=subprocess.STDOUT, text=True, timeout=300)
            except subprocess.TimeoutExpired:
                # Test timed out -- create a result object indicating timeout
                test_result = type('obj', (object,), {'returncode': -1})()
                # Append timeout message to output file
                with open(temp_output_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n[ERROR] Test execution timed out after 300 seconds\n")

            # Read the output (file is now closed)
            with open(temp_output_file, 'r', encoding='utf-8') as f:
                test_output = f.read()
        finally:
            # Clean up temp file (now it's definitely closed)
            if os.path.exists(temp_output_file):
                try:
                    os.unlink(temp_output_file)
                except PermissionError:
                    # File still in use on Windows, skip deletion (it's in temp dir anyway)
                    pass
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
        prompt += f"Failing test: {test_file}\n\n"
        prompt += f"Test output:\n```\n{test_output}\n```\n"

        print(f"→ Running: prompt_agentic_coder.run_prompt()")
        result = run_prompt(prompt)
        print(f"← Command finished")

        # Write report
        report_content = f"**Test file:** {test_file}\n"
        report_content += f"**Attempt:** {attempt}/{max_attempts}\n\n"
        report_content += "## Test Output (before fix)\n\n```\n" + test_output + "\n```\n\n"
        report_content += "## Result\n\n```\n" + result + "\n```\n\n"

        report_path = write_report("failing_test", report_content)
        print(f"✓ Report written: {report_path}\n")

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

    # Step 2: Build requirements index
    run_build_req_index()

    # Step 3: Remove orphan req_ids
    orphans = query_db("""
        SELECT DISTINCT req_id FROM req_locations
        WHERE category IN ('tests', 'code')
          AND req_id NOT IN (SELECT req_id FROM req_definitions)
    """)
    if orphans:
        handle_orphan_req_ids(orphans)
        run_build_req_index()  # Rebuild after cleanup

    # Step 4: Write tests for all untested requirements
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

    # Step 5: Order tests by dependency (only if new tests were written)
    if tests_were_written:
        handle_test_ordering()

    print("\n" + "=" * 60)
    print("✓ SETUP COMPLETE")
    print("=" * 60)
    print("\nAll tests written and ordered. Beginning test iteration...\n")

    # ========================================================================
    # ITERATION PHASE (max 5 full passes)
    # ========================================================================

    max_iterations = 5

    for iteration in range(1, max_iterations + 1):
        print("\n" + "=" * 60)
        print(f"ITERATION {iteration}/{max_iterations}")
        print("=" * 60 + "\n")

        # Get all tests from failing directory (sorted by dependency order)
        failing_tests = []
        if os.path.exists('./tests/failing'):
            for filename in os.listdir('./tests/failing'):
                if (filename.startswith('test_') or filename.startswith('_test_')) and filename.endswith('.py'):
                    failing_tests.append(os.path.join('./tests/failing', filename))

        # Sort alphabetically - numeric prefixes ensure proper order
        failing_tests.sort()

        if not failing_tests:
            print("All tests already in passing directory.\n")
            print("=" * 60)
            print("✓ SOFTWARE CONSTRUCTION COMPLETE")
            print("=" * 60)
            print(f"\nAll requirements have been implemented and tested!")
            print(f"Total iterations: {iteration}\n")

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

        print(f"Processing {len(failing_tests)} test(s) in this iteration\n")

        # Track whether any failures occurred in this iteration
        any_failures = False

        # Process each test until it passes
        for test_file in failing_tests:
            # Skip if file no longer exists (AI may have moved it despite instructions)
            if not os.path.exists(test_file):
                print(f"⚠ Skipping {os.path.basename(test_file)} - file not found (may have been moved)\n")
                continue

            test_had_failure = handle_single_test_until_passes(test_file)
            if test_had_failure:
                any_failures = True

        # After all tests processed, check if any had failures
        if any_failures:
            print("\n" + "=" * 60)
            print("ITERATION COMPLETE - FAILURES OCCURRED")
            print("=" * 60)
            print("\nSome tests required fixes. Moving all tests back to failing/")
            print("for next iteration to verify no regressions...\n")

            # Move all passing tests back to failing
            if os.path.exists('./tests/passing'):
                for filename in os.listdir('./tests/passing'):
                    if (filename.startswith('test_') or filename.startswith('_test_')) and filename.endswith('.py'):
                        src = os.path.join('./tests/passing', filename)
                        dst = os.path.join('./tests/failing', filename)
                        os.rename(src, dst)
                        print(f"  Moved: {filename}")

            print(f"\nContinuing to iteration {iteration + 1}...\n")
        else:
            # No failures - all tests passed on first try!
            print("\n" + "=" * 60)
            print("✓ ITERATION COMPLETE - NO FAILURES")
            print("=" * 60)
            print("\nAll tests passed on first try! Software construction complete.\n")

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

    # If we get here, we've exceeded max iterations
    print("\n" + "=" * 60)
    print(f"EXIT: EXCEEDED MAXIMUM ITERATIONS ({max_iterations})")
    print("=" * 60)
    print(f"\nERROR: Exceeded {max_iterations} full iterations")
    print("Tests pass individually but not all together (interdependency issue).")
    print("\nThis indicates:")
    print("  - Tests modify shared state that affects other tests")
    print("  - Code has hidden dependencies between features")
    print("  - Tests are not properly isolated")
    print("\nPlease review the most recent reports in ./reports/\n")
    sys.exit(1)

if __name__ == '__main__':
    main()
